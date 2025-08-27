import math
from typing import Dict, Any, List, Tuple, Optional
import torch

class CombatEnv:
    """
    Backward-compatible combat environment for training/eval,
    restored to your original turn-economy rules:
      - TURN_ACTION_CAP = 3 (max non-skip actions per turn)
      - Any BUFF/DEBUFF (codes 4..9) ends the turn immediately
      - Skip ends the turn immediately (no AP change)
      - End of round (after both acted): +1 AP capped, DoT/HoT ticks, durations decrement
      - One buff slot and one debuff slot per entity
      - Terminal on death or round cap

    Damage model:
        dmg = mult * (1 + (AtkType/100)) * ((100 - DefType)/100)
    with safe clamps to avoid negatives/overflows.
    """

    # ---- Tunables ---------------------------------------------------------
    DOT_PCT_BASE = 0.04   # 4% MaxHP per tick * intensity
    HOT_PCT_BASE = 0.03   # 3% MaxHP per tick * intensity
    INTENSITY_CAP = 1.5   # 150% cap for DoT/HoT intensity

    DEF_TERM_MIN = 0.05   # 5% minimum damage effectiveness
    DEF_TERM_MAX = 1.0    # 100% maximum

    ATK_DOWN_CAP = 0.90   # -90% max weaken
    DEF_DOWN_CAP = 0.90

    ATK_EFF_CAP = None    # Optional cap; set e.g. 300.0 if needed
    DEF_EFF_CAP = 95.0    # Avoid full immunity

    ROUND_CAP = 30        # restored to your old cap
    FEATURE_DIM = 92
    TURN_ACTION_CAP = 3   # max actions per turn (non-skip)

    def __init__(self, encoder_json_path: str = "", device: str = "cpu"):
        self.device = torch.device(device if device else "cpu")
        self.encoder_json_path = encoder_json_path

        # Runtime state
        self.state: Dict[str, Dict[str, Any]] = {}
        self.actor: str = "ai"
        self.round_count: int = 1
        self._round_starter: str = "ai"
        self.actions_left: int = 0
        self._terminal_reward: float = 0.0
        self._turn_actions_used: int = 0

    # ------------------------ Public API ----------------------------------
    def reset(self, ai_fighter: Dict[str, Any], enemy_fighter: Dict[str, Any], seed: Optional[int] = None):
        if seed is not None:
            try:
                import random
                random.seed(seed)
                torch.manual_seed(seed)
            except Exception:
                pass
        self.state = {
            "ai": self._init_side(ai_fighter),
            "enemy": self._init_side(enemy_fighter),
        }
        # Initiative: higher speed starts; tie -> ai
        self.actor = "ai" if self.state["ai"]["speed"] >= self.state["enemy"]["speed"] else "enemy"
        self._round_starter = self.actor
        self.round_count = 1
        self._terminal_reward = 0.0
        self._turn_actions_used = 0
        self.actions_left = min(self.state[self.actor]["ap"], self.TURN_ACTION_CAP)
        return self._make_obs()

    def step(self, action_idx: int):
        # Terminal guard
        if self.is_done():
            return self._make_obs(), self._terminal_reward, True, {}

        info: Dict[str, Any] = {"actor": self.actor}

        # 1) Stun check: lose whole turn
        if self.state[self.actor]["debuff"]["code"] == 7 and self.state[self.actor]["debuff"]["duration"] > 0:
            info["forced_stun_skip"] = True
            self.state[self.actor]["debuff"]["duration"] -= 1
            if self.state[self.actor]["debuff"]["duration"] <= 0:
                self.state[self.actor]["debuff"] = {"code": 0, "multiplier": 0, "duration": 0}
            self._end_turn_and_maybe_round()
            done, outc = self._terminal_and_reward()
            return self._make_obs(), outc if done else 0.5, done, info

        # 2) Action selection
        slots = self._slots(self.actor)
        mask = self._action_mask(slots)

        used_skip = False
        total_damage = 0
        applied_effects: List[Dict[str, Any]] = []
        ends_turn = False

        # If action cap reached, only SKIP is valid
        if self._turn_actions_used >= self.TURN_ACTION_CAP:
            action_idx = 4  # force SKIP

        if action_idx == 4 or mask[action_idx].item() == 0:
            used_skip = True
            ends_turn = True
        else:
            action = slots[action_idx]
            cost = int(action.get("cost", 0))
            if cost > self.state[self.actor]["ap"]:
                used_skip = True
                ends_turn = True
            else:
                self.state[self.actor]["ap"] -= cost
                for eff in action.get("effects", []):
                    code = int(eff.get("code", 0))
                    mult = int(eff.get("multiplier", eff.get("mult", 0)))
                    dur  = int(eff.get("duration",   eff.get("dur", 0)))
                    if code in (1, 2, 3):  # direct hit
                        total_damage += self._attack(code, mult, self.actor, self._other(self.actor))
                        applied_effects.append({"code": code, "multiplier": mult, "duration": dur})
                    elif code in (4, 5, 6):  # buff/regen on holder (4 atk,5 def,6 regen)
                        target = self.actor if code in (4, 6) else self._other(self.actor)
                        self._buff(code, mult, dur, target)
                        applied_effects.append({"code": code, "multiplier": mult, "duration": dur})
                        ends_turn = True
                    elif code in (7, 8, 9):  # debuffs on opponent
                        tgt = self._other(self.actor)
                        self._debuff(code, mult, dur, tgt)
                        applied_effects.append({"code": code, "multiplier": mult, "duration": dur})
                        ends_turn = True
                # Count this as one action performed
                self._turn_actions_used += 1

        info["used_skip"] = used_skip
        if total_damage:
            info["damage_dealt"] = int(total_damage)
        if applied_effects:
            info["applied_effects"] = applied_effects

        # 3) Turn/round flow
        turn_exhausted = (
            ends_turn or
            self._turn_actions_used >= self.TURN_ACTION_CAP or
            self.state[self.actor]["ap"] <= 0
        )
        if turn_exhausted:
            expired = self._end_turn_and_maybe_round()
            if expired:
                info["expired_effects"] = expired
        else:
            remaining_actions = self.TURN_ACTION_CAP - self._turn_actions_used
            self.actions_left = min(self.state[self.actor]["ap"], remaining_actions)

        # 4) Return new state
        done, outc = self._terminal_and_reward()
        return self._make_obs(), outc if done else 0.5, done, info

    # ------------------------ Introspection --------------------------------
    def is_done(self) -> bool:
        ai_dead = self.state.get("ai", {}).get("hp", 1) <= 0
        en_dead = self.state.get("enemy", {}).get("hp", 1) <= 0
        cap = self.round_count >= self.ROUND_CAP
        return bool(ai_dead or en_dead or cap)

    def _compute_outcome(self) -> float:
        ai_dead = self.state["ai"]["hp"] <= 0
        en_dead = self.state["enemy"]["hp"] <= 0
        if ai_dead and en_dead:
            return 0.5
        if en_dead:
            return 1.0
        if ai_dead:
            return 0.0
        if self.round_count >= self.ROUND_CAP:
            return 0.25
        return 0.5

    def _terminal_and_reward(self) -> Tuple[bool, float]:
        done = self.is_done()
        if done:
            self._terminal_reward = self._compute_outcome()
            return True, self._terminal_reward
        return False, 0.5

    def _other(self, side: str) -> str:
        return "enemy" if side == "ai" else "ai"

    # ------------------------ Helpers --------------------------------------
    def _init_side(self, fighter: Dict[str, Any]) -> Dict[str, Any]:
        st = {
            "level": int(fighter.get("level", 1)),
            "hpMax": int(fighter.get("hpMax", 100)),
            "hp": int(fighter.get("hp", fighter.get("hpMax", 100))),
            "speed": int(fighter.get("speed", 5)),
            "apMax": int(fighter.get("apMax", 4)),
            "ap": int(fighter.get("ap", 2)),
            "stats": dict(fighter.get("stats", {})),
            "actions": list(fighter.get("actions", [])),
            "buff": {"code": 0, "multiplier": 0, "duration": 0},
            "debuff": {"code": 0, "multiplier": 0, "duration": 0},
        }
        # Normalize each action to 2 effect slots (pad with no-ops)
        for a in st["actions"]:
            effs = list(a.get("effects", []))[:2]
            while len(effs) < 2:
                effs.append({"code": 0, "multiplier": 0, "duration": 0})
            a["effects"] = effs
        return st

    def _slots(self, side: str) -> List[Dict[str, Any]]:
        # Up to 4 actions from the fighter sheet (Skip is implicit at index 4)
        return list(self.state[side].get("actions", []))[:4]

    def _action_mask(self, slots: List[Dict[str, Any]]) -> torch.Tensor:
        # [P1..P4, SKIP]
        mask = [0, 0, 0, 0, 1]
        ap = self.state[self.actor]["ap"]
        if self._turn_actions_used >= self.TURN_ACTION_CAP:
            return torch.tensor(mask, dtype=torch.int64)
        remaining_actions = self.TURN_ACTION_CAP - self._turn_actions_used
        for i in range(min(4, len(slots))):
            mask[i] = 1 if (ap >= int(slots[i].get("cost", 0)) and remaining_actions > 0) else 0
        return torch.tensor(mask, dtype=torch.int64)

    # ------------------------ Combat math ----------------------------------
    def _effective_atk_def(self, code: int, atk_side: str, def_side: str) -> Tuple[float, float]:
        key_atk, key_def = {1: ("phy_atk", "phy_def"), 2: ("ele_atk", "ele_def"), 3: ("spi_atk", "spi_def")}[code]
        atk_raw = float(self.state[atk_side]["stats"].get(key_atk, 0))
        def_raw = float(self.state[def_side]["stats"].get(key_def, 0))
        buff_atk = self.state[atk_side]["buff"]
        buff_def = self.state[def_side]["buff"]
        deb_atk = self.state[atk_side]["debuff"]
        deb_def = self.state[def_side]["debuff"]
        atk_up = (buff_atk.get("code") == 4) * (buff_atk.get("multiplier", 0) / 100.0)
        def_up = (buff_def.get("code") == 5) * (buff_def.get("multiplier", 0) / 100.0)
        atk_dn = (deb_atk.get("code") == 9) * (deb_atk.get("multiplier", 0) / 100.0)
        def_dn = (deb_def.get("code") == 9) * (deb_def.get("multiplier", 0) / 100.0)
        atk_dn = min(atk_dn, self.ATK_DOWN_CAP)
        def_dn = min(def_dn, self.DEF_DOWN_CAP)
        atk_eff = max(0.0, atk_raw * (1 + atk_up) * (1 - atk_dn))
        def_eff = max(0.0, def_raw * (1 + def_up) * (1 - def_dn))
        if self.ATK_EFF_CAP is not None:
            atk_eff = min(atk_eff, float(self.ATK_EFF_CAP))
        if self.DEF_EFF_CAP is not None:
            def_eff = min(def_eff, float(self.DEF_EFF_CAP))
        return atk_eff, def_eff

    def _attack(self, code: int, mult: int, atk_side: str, def_side: str) -> int:
        atk_eff, def_eff = self._effective_atk_def(code, atk_side, def_side)
        term_atk = 1.0 + (atk_eff / 100.0)
        term_def = (100.0 - def_eff) / 100.0
        term_def = max(self.DEF_TERM_MIN, min(self.DEF_TERM_MAX, term_def))
        dmg = int(max(1.0, math.floor(float(mult) * term_atk * term_def)))
        self.state[def_side]["hp"] = max(0, self.state[def_side]["hp"] - dmg)
        return dmg

    def _buff(self, code: int, mult: int, dur: int, target: str) -> None:
        st = self.state[target]
        if code in (4, 5, 6):
            st["buff"] = {"code": code, "multiplier": mult, "duration": max(1, dur)}

    def _debuff(self, code: int, mult: int, dur: int, target: str) -> None:
        self.state[target]["debuff"] = {"code": code, "multiplier": mult, "duration": max(1, dur)}

    # ------------------------ Rounds & Ticks -------------------------------
    def _end_turn_and_maybe_round(self) -> List[Dict[str, Any]]:
        # Switch actor
        self.actor = self._other(self.actor)
        # Reset per-turn action counter for the new actor
        self._turn_actions_used = 0
        # actions_left: min(AP, action cap)
        self.actions_left = min(self.state[self.actor]["ap"], self.TURN_ACTION_CAP)

        expired: List[Dict[str, Any]] = []
        # If turn returns to round starter -> end of round
        if self.actor == self._round_starter:
            # Ticks: Poison/HoT
            for side in ("ai", "enemy"):
                st = self.state[side]
                if st["debuff"]["code"] == 8 and st["debuff"]["duration"] > 0:
                    intensity = min(st["debuff"]["multiplier"] / 100.0, self.INTENSITY_CAP)
                    dot = max(1, math.floor(st["hpMax"] * self.DOT_PCT_BASE * intensity))
                    st["hp"] = max(0, st["hp"] - dot)
                if st["buff"]["code"] == 6 and st["buff"]["duration"] > 0:
                    intensity = min(st["buff"]["multiplier"] / 100.0, self.INTENSITY_CAP)
                    hot = max(1, math.floor(st["hpMax"] * self.HOT_PCT_BASE * intensity))
                    st["hp"] = min(st["hpMax"], st["hp"] + hot)

            # Decrement durations & collect expirations
            for side in ("ai", "enemy"):
                for key in ("buff", "debuff"):
                    eff = self.state[side][key]
                    if eff["duration"] > 0:
                        if eff["code"] == 7:
                            continue
                        eff["duration"] -= 1
                        if eff["duration"] <= 0:
                            expired.append({"side": side, **eff})
                            self.state[side][key] = {"code": 0, "multiplier": 0, "duration": 0}

            # End of round AP drip: +1 capped (old rule)
            for side in ("ai", "enemy"):
                self.state[side]["ap"] = min(self.state[side]["apMax"], self.state[side]["ap"] + 1)

            # Next round bookkeeping
            self.actions_left = min(self.state[self.actor]["ap"], self.TURN_ACTION_CAP)
            self.round_count += 1
            self._round_starter = self.actor

        return expired

    # ------------------------ Observation ----------------------------------
    def _encode_features(self) -> torch.Tensor:
        def side_block(tag: str) -> List[float]:
            s = self.state[tag]
            b = s["buff"]; d = s["debuff"]
            return [
                float(s.get("hp", 0)), float(s.get("hpMax", 1)),
                float(s.get("ap", 0)), float(s.get("apMax", 1)),
                float(s.get("speed", 0)), float(s.get("level", 1)),
                float(b.get("code", 0)), float(b.get("multiplier", 0)), float(b.get("duration", 0)),
                float(d.get("code", 0)), float(d.get("multiplier", 0)), float(d.get("duration", 0)),
            ]
        def stat_block(tag: str) -> List[float]:
            stats = self.state[tag]["stats"]
            return [
                float(stats.get("phy_atk", 0)), float(stats.get("phy_def", 0)),
                float(stats.get("ele_atk", 0)), float(stats.get("ele_def", 0)),
                float(stats.get("spi_atk", 0)), float(stats.get("spi_def", 0)),
            ]
        vec: List[float] = []
        vec.append(1.0 if self.actor == "ai" else 0.0)
        vec.append(float(max(0, min(255, self.round_count))))
        vec.extend(side_block("ai"))
        vec.extend(side_block("enemy"))
        vec.extend(stat_block("ai"))
        vec.extend(stat_block("enemy"))
        if len(vec) < self.FEATURE_DIM:
            vec.extend([0.0] * (self.FEATURE_DIM - len(vec)))
        else:
            vec = vec[: self.FEATURE_DIM]
        return torch.tensor(vec, dtype=torch.float32)

    def _make_obs(self) -> Dict[str, Any]:
        feats = self._encode_features()
        slots = self._slots(self.actor)
        mask = self._action_mask(slots)
        return {"who": self.actor, "features": feats, "mask": mask}
