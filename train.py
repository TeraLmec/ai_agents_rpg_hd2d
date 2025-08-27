# ea_train.py
from __future__ import annotations
from dataclasses import dataclass
import time
from typing import Callable, Dict, Any, List, Tuple, Optional
import os, random, math
import torch

from ai.eval.evaluator import Evaluator
from ai.env.combat_env import CombatEnv
from fighter_generator.fighter_gen import fighter_gen


# ------------------------------
# Minimal policy (92 -> 128 -> 128 -> 5)
# ------------------------------
class PolicyMLP(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.net = torch.nn.Sequential(
            torch.nn.Linear(92, 128), torch.nn.ReLU(),
            torch.nn.Linear(128, 64), torch.nn.ReLU(),
            torch.nn.Linear(64, 5),
        )
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


# ------------------------------
# EA config
# ------------------------------
@dataclass
class EAConfig:
    pop_size: int = 256
    generation: int = 256
    elites: int = 8
    tournament_k: int = 3
    crossover_rate: float = 0.65
    mut_prob: float = 0.12             # per-parameter probability 0.08
    mut_sigma_scale: float = 0.08      # sigma = scale * tensor.std() 0.05
    mut_sigma_floor: float = 0.02      # minimum sigma if std is tiny 0.02
    eval_K: int = 64                    # episodes per individual
    device: str = "cuda"
    seed: int = 1234
    save_dir: str = "checkpoints"
    batch_eval: bool = True             # use batched evaluator
    batch_size: int = 2048                 # concurrent envs per evaluation

    w_hp_margin: float = 0.2           # scale for HP margin term
    w_brevity: float = 0.15             # scale favoring shorter fights
    w_skip_pen: float = 0.05            # penalty per voluntary skip by AI
    w_stun_pen: float = 0.02            # penalty per AI turn lost to stun
    w_no_damage_pen: float = 0.05       # penalty if AI deals zero total damage in an episode


# ------------------------------
# EA utils (operate on state_dicts)
# ------------------------------
def clone_state_dict(sd: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
    return {k: v.clone().detach().cpu() for k, v in sd.items()}

def blend_state_dicts(a: Dict[str, torch.Tensor], b: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
    """Layer-wise convex blend with alpha ~ U[0,1] per tensor."""
    child = {}
    for k in a.keys():
        W_a = a[k].float()
        W_b = b[k].float()
        alpha = torch.rand(1).item()  # scalar per tensor (simple & effective)
        child[k] = (alpha * W_a + (1.0 - alpha) * W_b).to(torch.float32)
    return child

def mutate_state_dict(sd: Dict[str, torch.Tensor], p: float, scale: float, sigma_floor: float) -> Dict[str, torch.Tensor]:
    """Add Gaussian noise to a random subset of parameters."""
    out = {}
    for k, w in sd.items():
        w = w.clone().detach().float()
        if w.numel() == 0:
            out[k] = w
            continue
        std = float(w.std().item())
        sigma = max(sigma_floor, scale * (std if std > 0 else 1.0))
        if p <= 0.0 or sigma <= 0.0:
            out[k] = w
            continue
        # mask ~ Bernoulli(p)
        mask = (torch.rand_like(w) < p).float()
        noise = torch.randn_like(w) * sigma
        out[k] = (w + mask * noise).to(torch.float32)
    return out


# ------------------------------
# EA Engine
# ------------------------------
class EAEngine:
    def __init__(
        self,
        make_model: Callable[[], torch.nn.Module],
        make_env: Callable[[], CombatEnv],
        make_fighter_pairs: Callable[[int], List[Tuple[Dict[str, Any], Dict[str, Any]]]],
        cfg: EAConfig,
    ):
        self.make_model = make_model
        self.make_env = make_env
        self.make_fighter_pairs = make_fighter_pairs
        self.cfg = cfg
        self.rng = random.Random(cfg.seed)

        # Evaluator (uses your action decoder internally) with configurable shaping
        self.evaluator = Evaluator(
            make_env=self.make_env,
            K=cfg.eval_K,
            device=cfg.device,
            weights={
                "w_hp_margin": cfg.w_hp_margin,
                "w_brevity": cfg.w_brevity,
                "w_skip_pen": cfg.w_skip_pen,
                "w_stun_pen": cfg.w_stun_pen,
                "w_no_damage_pen": cfg.w_no_damage_pen,
            },
        )

        os.makedirs(cfg.save_dir, exist_ok=True)

    def init_population(self) -> List[Dict[str, torch.Tensor]]:
        pop = []
        for _ in range(self.cfg.pop_size):
            model = self.make_model()
            # Different seeds via PyTorch default init randomness
            pop.append(clone_state_dict(model.state_dict()))
        return pop

    @torch.no_grad()
    def evaluate(self, sd: Dict[str, torch.Tensor]) -> Tuple[float, float]:
        """Load weights into a single model and evaluate -> (mean_fitness, mean_outcome)."""
        model = self.make_model().to(self.cfg.device).eval()
        model.load_state_dict({k: v.to(self.cfg.device) for k, v in sd.items()}, strict=True)
        pairs = self.make_fighter_pairs(self.cfg.eval_K)
        if self.cfg.batch_eval:
            report = self.evaluator.evaluate_batched(
                model, pairs, seed_base=self.cfg.seed, K=self.cfg.eval_K, batch_size=self.cfg.batch_size
            )
        else:
            report = self.evaluator.evaluate(model, pairs, seed_base=self.cfg.seed, K=self.cfg.eval_K)
        return float(report["mean_fitness"]), float(report["mean_outcome"])

    def tournament_select(self, fits: List[float], k: int) -> int:
        idxs = [self.rng.randrange(0, len(fits)) for _ in range(k)]
        best = max(idxs, key=lambda i: fits[i])
        return best

    def run(self, generations: int = 100) -> Dict[str, Any]:
        pop = self.init_population()

        # Evaluate initial population
        t0 = time.perf_counter()
        fits, outs = self._eval_population(pop, tag="gen0")

        best_idx = int(max(range(len(pop)), key=lambda i: fits[i]))
        best_sd = clone_state_dict(pop[best_idx])
        best_fit = fits[best_idx]
        best_out = outs[best_idx]
        gen_time = time.perf_counter() - t0
        if torch.cuda.is_available() and self.cfg.device.startswith("cuda"):
            try:
                mem_mb = torch.cuda.memory_allocated() / (1024**2)
            except Exception:
                mem_mb = 0.0
            print(f"[gen 0] best_fit={best_fit:.4f} best_out={best_out:.3f} mean_fit={sum(fits)/len(fits):.4f} time={gen_time:.2f}s cuda_mem={mem_mb:.1f}MB", flush=True)
        else:
            print(f"[gen 0] best_fit={best_fit:.4f} best_out={best_out:.3f} mean_fit={sum(fits)/len(fits):.4f} time={gen_time:.2f}s", flush=True)

        for gen in range(1, generations + 1):
            t_gen = time.perf_counter()
            # Sort by fitness
            order = sorted(range(len(pop)), key=lambda i: fits[i], reverse=True)
            elites = [clone_state_dict(pop[i]) for i in order[: self.cfg.elites]]

            # Reproduce to fill new pop
            new_pop: List[Dict[str, torch.Tensor]] = []
            new_pop.extend(elites)

            while len(new_pop) < self.cfg.pop_size:
                # selection
                a = self.tournament_select(fits, self.cfg.tournament_k)
                b = self.tournament_select(fits, self.cfg.tournament_k)

                parentA = pop[a]
                parentB = pop[b]

                # crossover or clone
                if self.rng.random() < self.cfg.crossover_rate:
                    child = blend_state_dicts(parentA, parentB)
                else:
                    child = clone_state_dict(parentA)

                # mutation
                child = mutate_state_dict(child, self.cfg.mut_prob, self.cfg.mut_sigma_scale, self.cfg.mut_sigma_floor)

                new_pop.append(child)

            pop = new_pop

            # Evaluate new population
            fits, outs = self._eval_population(pop, tag=f"gen{gen}")

            # Track best-so-far
            gen_best_idx = int(max(range(len(pop)), key=lambda i: fits[i]))
            gen_best_fit = fits[gen_best_idx]
            gen_best_out = outs[gen_best_idx]
            if gen_best_fit > best_fit:
                best_fit = gen_best_fit
                best_out = gen_best_out
                best_sd = clone_state_dict(pop[gen_best_idx])
                self._save_best(best_sd, gen, best_fit, best_out)
                print(f"[gen {gen}] NEW_BEST fit={best_fit:.4f} out={best_out:.3f} (idx={gen_best_idx})", flush=True)

            gen_time = time.perf_counter() - t_gen
            if torch.cuda.is_available() and self.cfg.device.startswith("cuda"):
                try:
                    mem_mb = torch.cuda.memory_allocated() / (1024**2)
                except Exception:
                    mem_mb = 0.0
                print(f"[gen {gen}] best_fit={gen_best_fit:.4f} best_out={gen_best_out:.3f} mean_fit={sum(fits)/len(fits):.4f} time={gen_time:.2f}s cuda_mem={mem_mb:.1f}MB", flush=True)
            else:
                print(f"[gen {gen}] best_fit={gen_best_fit:.4f} best_out={gen_best_out:.3f} mean_fit={sum(fits)/len(fits):.4f} time={gen_time:.2f}s", flush=True)

        # Return best
        return {"best_state_dict": best_sd, "best_fit": best_fit, "best_outcome": best_out}

    def _eval_population(self, pop: List[Dict[str, torch.Tensor]], tag: str) -> Tuple[List[float], List[float]]:
        fits, outs = [], []
        for i, sd in enumerate(pop):
            fit, out = self.evaluate(sd)
            fits.append(fit)
            outs.append(out)
            # Compact per-individual summary; prints every 8 to limit spam
            if (i % 8) == 0 or i == len(pop) - 1:
                print(f"[eval {tag}] indiv={i}/{len(pop)-1} fit={fit:.4f} out={out:.3f}", flush=True)
        # (Optional) save a quick CSV log
        try:
            with open(os.path.join(self.cfg.save_dir, "ea_log.csv"), "a", encoding="utf-8") as f:
                mean_fit = sum(fits) / max(1, len(fits))
                f.write(f"{tag},{mean_fit:.6f}\n")
        except Exception:
            pass
        return fits, outs

    def _save_best(self, sd: Dict[str, torch.Tensor], gen: int, fit: float, out: float) -> None:
        path = os.path.join(self.cfg.save_dir, "best_so_far.pt")
        torch.save({"gen": gen, "fitness": fit, "outcome": out, "state_dict": sd}, path)


# ------------------------------
# Minimal wiring to run training
# ------------------------------
def make_env() -> CombatEnv:
    # Use the same JSON path your encoder expects; adjust if needed
    return CombatEnv(encoder_json_path="ai/data/data.json")

def make_fighter_pairs_fn(K: int) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
    fighter_generator = fighter_gen()
    pairs = []
    for _ in range(K):
        ai = fighter_generator.generate_dict()
        en = fighter_generator.generate_dict()
        pairs.append((ai, en))
    return pairs


def main():
    torch.manual_seed(1234)
    cfg = EAConfig()
    engine = EAEngine(
        make_model=PolicyMLP,
        make_env=make_env,
        make_fighter_pairs=make_fighter_pairs_fn,
        cfg=cfg,
    )
    result = engine.run(generations=cfg.generation)   # adjust as you like
    print("\n=== BEST ===")
    print(f"fitness={result['best_fit']:.4f} outcome={result['best_outcome']:.3f}")
    # Save final best (already saved as best_so_far.pt during training)
    final_path = os.path.join(cfg.save_dir, "best_final.pt")
    torch.save(result, final_path)
    print(f"Saved final best to: {final_path}")


if __name__ == "__main__":
    main()
