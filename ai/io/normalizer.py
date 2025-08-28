# normalizer.py — normalization driven by fighter_gen's formulas
from __future__ import annotations

from fighter_generator.fighter_gen import FighterGenBounds

def normalizer(data: dict) -> dict:
    """
    Normalize the exact 92-feature structure your state_encoder expects,
    but derive min/max from fighter_gen's formulas at the CURRENT AI level.
    Output structure is unchanged.
    """
    def clamp01(x: float) -> float:
        return 0.0 if x <= 0.0 else (1.0 if x >= 1.0 else x)

    def norm_val(v, lo, hi) -> float:
        lo = float(lo); hi = float(hi)
        if hi <= lo:  # safety
            return 0.0
        return clamp01((float(v) - lo) / (hi - lo))

    # --- 1) determine the AI level and retrieve dynamic bounds --------------
    ai_src = data["combat_stats"]["ai_stats"]
    level = int(ai_src.get("level", 1))
    level = 1 if level < 1 else (5 if level > 5 else level)
    B = FighterGenBounds.at_level(level)

    # Small helpers for common fields
    def n_cost(x):  lo,hi = B["cost"];       return norm_val(x, lo, hi)
    def n_code(x):  lo,hi = B["code"];       return norm_val(x, lo, hi)
    def n_mult(x):  lo,hi = B["multiplier"]; return norm_val(x, lo, hi)
    def n_dur(x):   lo,hi = B["duration"];   return norm_val(x, lo, hi)

    def norm_effect(e: dict) -> dict:
        return {
            "code":       n_code(e["code"]),
            "multiplier": n_mult(e["multiplier"]),
            "duration":   n_dur(e["duration"]),
        }

    def norm_action(a: dict) -> dict:
        return {
            "cost":    n_cost(a["cost"]),
            "effects": [norm_effect(x) for x in a["effects"]],
        }

    out = {}

    # --- 2) enemy recent actions (3) ----------------------------------------
    out["enemy_recent_actions"] = [norm_action(a) for a in data["enemy_recent_actions"]]

    # --- 3) actifs (ai + enemy) ---------------------------------------------
    out["actifs"] = {
        "ai_actifs":    [norm_effect(x) for x in data["actifs"]["ai_actifs"]],
        "enemy_actifs": [norm_effect(x) for x in data["actifs"]["enemy_actifs"]],
    }

    # --- 4) combat stats (ai + enemy) ---------------------------------------
    # ai
    hpMax_lo, hpMax_hi = B["hpMax"]
    hp_lo, hp_hi       = B["hp"]
    spd_lo, spd_hi     = B["speed"]
    apM_lo, apM_hi     = B["apMax"]
    ap_lo, ap_hi       = B["ap"]
    stat_lo, stat_hi   = B["stat"]

    out["combat_stats"] = {
        "ai_stats": {
            "level": norm_val(ai_src["level"], *B["level"]),
            "hpMax": norm_val(ai_src["hpMax"], hpMax_lo, hpMax_hi),
            "hp":    norm_val(ai_src["hp"],    hp_lo,    hp_hi),
            "speed": norm_val(ai_src["speed"], spd_lo,   spd_hi),
            "apMax": norm_val(ai_src["apMax"], apM_lo,   apM_hi),
            "ap":    norm_val(ai_src["ap"],    ap_lo,    ap_hi),
            "stats": {
                "phy_atk": norm_val(ai_src["stats"]["phy_atk"], stat_lo, stat_hi),
                "phy_def": norm_val(ai_src["stats"]["phy_def"], stat_lo, stat_hi),
                "spi_atk": norm_val(ai_src["stats"]["spi_atk"], stat_lo, stat_hi),
                "spi_def": norm_val(ai_src["stats"]["spi_def"], stat_lo, stat_hi),
                "ele_atk": norm_val(ai_src["stats"]["ele_atk"], stat_lo, stat_hi),
                "ele_def": norm_val(ai_src["stats"]["ele_def"], stat_lo, stat_hi),
            },
        },
        # enemy (we don’t know enemy level’s role allocation → use same per-AI level ranges;
        # this matches how you trained/encode and keeps magnitudes consistent)
        "enemy_stats": {
            "level": norm_val(data["combat_stats"]["enemy_stats"]["level"], *B["level"]),
            "hpMax": norm_val(data["combat_stats"]["enemy_stats"]["hpMax"], hpMax_lo, hpMax_hi),
            "hp":    norm_val(data["combat_stats"]["enemy_stats"]["hp"],    hp_lo,    hp_hi),
        },
    }

    # --- 5) combat states ----------------------------------------------------
    out["combat_states"] = {
        "round_count": norm_val(data["combat_states"]["round_count"], *B["round_count"]),
        "action_left": norm_val(data["combat_states"]["action_left"], *B["action_left"]),
    }

    # --- 6) available actions (4) + history (2) ------------------------------
    out["ai_available_actions"] = [norm_action(a) for a in data["ai_available_actions"]]
    out["ai_actions_history"]   = [norm_action(a) for a in data["ai_actions_history"]]

    return out
