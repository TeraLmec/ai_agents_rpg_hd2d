# evaluator.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Dict, Any, List, Optional, Tuple
import torch
from ai.io.action_decoder import decode_action
from ai.env.combat_env import CombatEnv
from ai.eval.rewards import RewardWeights, compute_fitness, remap_base_outcome


@dataclass
class EpisodeResult:
    reward_outcome: float      # 1.0 win, 0.5 draw, 0.0 loss (from env)
    fitness: float
    rounds: int
    hp_ai: int
    hp_enemy: int
    voluntary_skips: int
    seed: int
    opponent_id: str


def default_enemy_policy(obs: Dict[str, Any]) -> int:
    """
    Very simple deterministic baseline for the enemy:
    - pick the first available non-skip action (P1..P4)
    - otherwise skip (P5)
    """
    mask = obs["mask"].tolist()
    # P1..P4 first available
    for i in range(4):
        if mask[i] == 1:
            return i
    return 4  # skip


class Evaluator:
    """
    Runs K battles for a policy (your MLP) and returns mean fitness.

    Parameters
    ----------
    make_env : Callable[[], CombatEnv]
        Factory to create a *fresh* environment instance per episode.
    enemy_policy : Callable[[obs_dict], int]
        Callable that returns an action index (0..4) for the enemy side.
        Defaults to a simple deterministic baseline.
    device : str
        'cuda' if available else 'cpu'.
    K : int
        Number of episodes per evaluation.
    """

    def __init__(
        self,
        make_env: Callable[[], CombatEnv],
        enemy_policy: Callable[[Dict[str, Any]], int] = default_enemy_policy,
        device: Optional[str] = None,
        K: int = 8,
        weights: Optional[Dict[str, float]] = None,
    ):
        self.make_env = make_env
        self.enemy_policy = enemy_policy
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.K = K
        # Centralized weights
        self.weights = RewardWeights.from_dict(weights)

    @torch.no_grad()
    def evaluate(
        self,
        model: torch.nn.Module,
        fighter_pairs: List[Tuple[Dict[str, Any], Dict[str, Any]]],
        seed_base: int = 12345,
        K: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate `model` over K episodes against a mix of opponents.

        fighter_pairs: list of (fighter_ai, fighter_enemy) dicts.
                       We'll cycle through this list if shorter than K.
        Returns:
            {
              "mean_fitness": float,
              "mean_outcome": float,
              "episodes": List[EpisodeResult],
            }
        """
        model = model.to(self.device).eval()
        K = K or self.K
        episodes: List[EpisodeResult] = []

        for epi in range(K):
            env = self.make_env()
            # Cycle opponents if needed
            f_ai, f_enemy = fighter_pairs[epi % len(fighter_pairs)]

            seed = seed_base + epi
            obs = env.reset(f_ai, f_enemy, seed=seed)

            voluntary_skips = 0
            ai_stun_turns = 0
            ai_total_damage = 0

            done = False
            while not done:
                if obs["who"] == "ai":
                    # Forward the model: features -> logits
                    feats = obs["features"].to(self.device)
                    logits = model(feats.unsqueeze(0)).squeeze(0)
                    # Masked decode to get chosen action index
                    _, choice, _ = decode_action(logits, obs["mask"].to(self.device))
                    action_idx = int(choice)
                else:
                    # Enemy baseline policy
                    action_idx = int(self.enemy_policy(obs))

                obs, reward, done, info = env.step(action_idx)

                # Count voluntary skips only when AI chose to skip (not stunned)
                if info.get("actor") == "ai" and info.get("used_skip") and not info.get("forced_stun_skip"):
                    voluntary_skips += 1
                # Count AI stun turns
                if info.get("actor") == "ai" and info.get("forced_stun_skip"):
                    ai_stun_turns += 1
                # Accumulate AI dealt damage
                if info.get("actor") == "ai":
                    ai_total_damage += int(info.get("damage_dealt", 0))

            # Episode ended: compute shaping
            outcome = float(reward)  # 1/0.5/0 from env
            hp_ai = int(env.state["ai"]["hp"])
            hp_enemy = int(env.state["enemy"]["hp"])
            avg_hpmax = max(1, (env.state["ai"]["hpMax"] + env.state["enemy"]["hpMax"]) // 2)
            rounds = int(env.round_count)

            # Remap base outcome via centralized weights (win/draw/loss/cap)
            base_outcome = remap_base_outcome(outcome, self.weights)
            fitness = compute_fitness(
                base_outcome,
                hp_ai,
                hp_enemy,
                avg_hpmax,
                rounds,
                voluntary_skips,
                ai_stun_turns,
                ai_total_damage,
                self.weights,
            )

            episodes.append(
                EpisodeResult(
                    reward_outcome=outcome,
                    fitness=fitness,
                    rounds=rounds,
                    hp_ai=hp_ai,
                    hp_enemy=hp_enemy,
                    voluntary_skips=voluntary_skips,
                    seed=seed,
                    opponent_id=f"pair_{epi % len(fighter_pairs)}",
                )
            )

        mean_fit = sum(e.fitness for e in episodes) / max(1, len(episodes))
        mean_out = sum(e.reward_outcome for e in episodes) / max(1, len(episodes))
        return {
            "mean_fitness": mean_fit,
            "mean_outcome": mean_out,
            "episodes": episodes,
        }

    @torch.no_grad()
    def evaluate_batched(
        self,
        model: torch.nn.Module,
        fighter_pairs: List[Tuple[Dict[str, Any], Dict[str, Any]]],
        seed_base: int = 12345,
        K: Optional[int] = None,
        batch_size: int = 8,
    ) -> Dict[str, Any]:
        """Evaluate model over K episodes using up to `batch_size` concurrent envs.
        Batching stacks features for all AI turns in the active envs into a single
        forward pass, reducing overhead and improving GPU utilization.
        """
        model = model.to(self.device).eval()
        K = K or self.K
        episodes: List[EpisodeResult] = []

        epi = 0
        while epi < K:
            # Build a mini-batch of envs
            B = min(batch_size, K - epi)
            envs = [self.make_env() for _ in range(B)]
            seeds = [seed_base + (epi + b) for b in range(B)]
            obs_list = []
            vskips = [0 for _ in range(B)]
            stun_turns = [0 for _ in range(B)]
            ai_dmg = [0 for _ in range(B)]
            ids = [f"pair_{(epi + b) % len(fighter_pairs)}" for b in range(B)]
            for b in range(B):
                f_ai, f_enemy = fighter_pairs[(epi + b) % len(fighter_pairs)]
                obs_list.append(envs[b].reset(f_ai, f_enemy, seed=seeds[b]))

            done_flags = [False for _ in range(B)]
            # Main loop until all in the batch are done
            while not all(done_flags):
                # Collect AI turns to batch
                ai_idxs = [i for i in range(B) if (not done_flags[i]) and obs_list[i]["who"] == "ai"]
                if ai_idxs:
                    feats = torch.stack([obs_list[i]["features"] for i in ai_idxs], dim=0).to(self.device)
                    logits = model(feats)  # shape (len(ai_idxs), 5)
                    # Decode each with its own mask
                    acts_ai = []
                    for j, i in enumerate(ai_idxs):
                        mask = obs_list[i]["mask"].to(self.device)
                        _, choice, _ = decode_action(logits[j], mask)
                        acts_ai.append(int(choice))
                else:
                    acts_ai = []

                # Step each env once
                ai_ptr = 0
                for i in range(B):
                    if done_flags[i]:
                        continue
                    if obs_list[i]["who"] == "ai":
                        action_idx = acts_ai[ai_ptr]
                        ai_ptr += 1
                    else:
                        action_idx = int(self.enemy_policy(obs_list[i]))
                    obs, reward, done, info = envs[i].step(int(action_idx))
                    # Count voluntary skips only when AI chose to skip (not stunned)
                    if info.get("actor") == "ai" and info.get("used_skip") and not info.get("forced_stun_skip"):
                        vskips[i] += 1
                    if info.get("actor") == "ai" and info.get("forced_stun_skip"):
                        stun_turns[i] += 1
                    if info.get("actor") == "ai":
                        ai_dmg[i] += int(info.get("damage_dealt", 0))
                    obs_list[i] = obs
                    done_flags[i] = bool(done)

            # Batch finished: collect results
            for b in range(B):
                outcome = float(envs[b]._terminal_and_reward()[1])  # env stores terminal reward
                hp_ai = int(envs[b].state["ai"]["hp"])
                hp_enemy = int(envs[b].state["enemy"]["hp"])
                avg_hpmax = max(1, (envs[b].state["ai"]["hpMax"] + envs[b].state["enemy"]["hpMax"]) // 2)
                rounds = int(envs[b].round_count)
                base_outcome = remap_base_outcome(outcome, self.weights)
                fitness = compute_fitness(
                    base_outcome,
                    hp_ai,
                    hp_enemy,
                    avg_hpmax,
                    rounds,
                    vskips[b],
                    stun_turns[b],
                    ai_dmg[b],
                    self.weights,
                )
                episodes.append(
                    EpisodeResult(
                        reward_outcome=outcome,
                        fitness=fitness,
                        rounds=rounds,
                        hp_ai=hp_ai,
                        hp_enemy=hp_enemy,
                        voluntary_skips=vskips[b],
                        seed=seeds[b],
                        opponent_id=ids[b],
                    )
                )

            epi += B

        mean_fit = sum(e.fitness for e in episodes) / max(1, len(episodes))
        mean_out = sum(e.reward_outcome for e in episodes) / max(1, len(episodes))
        return {"mean_fitness": mean_fit, "mean_outcome": mean_out, "episodes": episodes}

    # shaping moved to ai.eval.rewards
