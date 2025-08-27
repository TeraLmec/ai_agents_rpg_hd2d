from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict


@dataclass
class RewardWeights:
    # Base terminal outcomes
    base_win: float = 1.0
    base_loss: float = 0.0
    base_double_ko: float = 0.5
    base_round_cap: float = 0.25

    # Shaping terms
    w_hp_margin: float = 0.25
    w_brevity: float = 0.10
    w_skip_pen: float = 0.01
    w_stun_pen: float = 0.0
    w_no_damage_pen: float = 0.0

    @staticmethod
    def from_dict(d: Optional[Dict[str, float]]) -> "RewardWeights":
        d = d or {}
        return RewardWeights(
            base_win=float(d.get("base_win", 1.0)),
            base_loss=float(d.get("base_loss", 0.0)),
            base_double_ko=float(d.get("base_double_ko", 0.5)),
            base_round_cap=float(d.get("base_round_cap", 0.25)),
            w_hp_margin=float(d.get("w_hp_margin", 0.25)),
            w_brevity=float(d.get("w_brevity", 0.10)),
            w_skip_pen=float(d.get("w_skip_pen", 0.01)),
            w_stun_pen=float(d.get("w_stun_pen", 0.0)),
            w_no_damage_pen=float(d.get("w_no_damage_pen", 0.0)),
        )


def compute_fitness(
    base_outcome: float,
    hp_ai: int,
    hp_enemy: int,
    avg_hpmax: int,
    rounds: int,
    voluntary_skips: int,
    ai_stun_turns: int,
    ai_total_damage: int,
    w: RewardWeights,
) -> float:
    # HP margin in [-1,+1]
    hp_term = w.w_hp_margin * ((hp_ai - hp_enemy) / max(1, int(avg_hpmax)))
    # Prefer shorter fights slightly
    brevity_term = w.w_brevity * (1.0 / max(1, int(rounds)))
    # Penalize stalling and negatives
    skip_penalty = w.w_skip_pen * max(0, int(voluntary_skips))
    stun_penalty = w.w_stun_pen * max(0, int(ai_stun_turns))
    no_dmg_penalty = w.w_no_damage_pen if int(ai_total_damage) <= 0 else 0.0
    return float(base_outcome + hp_term + brevity_term - skip_penalty - stun_penalty - no_dmg_penalty)


def remap_base_outcome(outcome: float, w: RewardWeights) -> float:
    """Map the environment's base terminal outcome (0.0, 0.25, 0.5, 1.0)
    to possibly customized base values from RewardWeights.
    """
    # Match with tolerance in case of float calc
    if abs(outcome - 1.0) < 1e-6:
        return w.base_win
    if abs(outcome - 0.5) < 1e-6:
        return w.base_double_ko
    if abs(outcome - 0.25) < 1e-6:
        return w.base_round_cap
    # treat anything else as loss
    return w.base_loss
