# combat_env_min.py
from __future__ import annotations
from typing import Dict, Any, Tuple, List, Optional, Set
import copy, math, os, json, random
import torch
from ai.io.state_encoder import state_encoder as SE  # uses your path-based encoder

# ---- Constants (match your rules) -------------------------------------------
MAX_ACTIONS_PER_TURN = 3
ROUND_CAP = 30
SKIP_CODE = 10
BUFF_CODES = {4, 5, 6}
DEBUFF_CODES = {7, 8, 9}

class CombatEnv:
    """
    Minimal combat env:
      - 3 actions/turn; any effect code in 4..9 ends the turn immediately
      - Skip (code 10) costs 0; always allowed at decode time
      - End of round after both acted: +1 AP (capped), poison DoT, tick durations
      - One buff slot and one debuff slot per entity (replacement rule)
      - Terminal when any HP <= 0, or round cap (draw)

    Public API:
      env = CombatEnv(encoder_json_path="ai/data/data.json", device="cuda")
      obs = env.reset(f_ai, f_enemy, seed=123)
      obs, reward, done, info = env.step(action_idx)  # idx: 0..4 (P1..P4,P5)
    """

    def __init__(self, encoder_json_path: str = "ai/data/data.json", device: Optional[str] = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.encoder = SE()
        self.path = encoder_json_path
        self.rng = random.Random()

        # Core state
        self.state: Dict[str, Any] = {}
        self.actor: str = "ai"              # who acts now: "ai" or "enemy"
        self.actions_left: int = MAX_ACTIONS_PER_TURN
        self.round_count: int = 0
        self.acted_this_round: Set[str] = set()  # tracks who acted this round
        self.first_actor: str = "ai"
        self.second_actor: str = "enemy"

        # Histories for encoder input
        self.enemy_recent_actions: List[Dict[str, Any]] = []  # last 3 enemy actions
        self.ai_actions_history: List[Dict[str, Any]] = []    # last 2 ai actions

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------
    def reset(self, fighter_ai: dict, fighter_enemy: dict, seed: Optional[int] = None):
        """Initialize a fresh fight and return the first observation."""
        if seed is not None:
            self.rng.seed(seed)

        self.state = {
            "ai": self._init_entity(copy.deepcopy(fighter_ai)),
            "enemy": self._init_entity(copy.deepcopy(fighter_enemy)),
        }

        # Initiative: higher speed starts
        if self.state["enemy"]["speed"] > self.state["ai"]["speed"]:
            self.first_actor, self.second_actor = "enemy", "ai"
        else:
            self.first_actor, self.second_actor = "ai", "enemy"

        self.actor = self.first_actor
        self.actions_left = MAX_ACTIONS_PER_TURN
        self.round_count = 0
        self.acted_this_round.clear()
        self.enemy_recent_actions.clear()
        self.ai_actions_history.clear()

        return self._obs()

    def step(self, action_idx: int) -> Tuple[Dict[str, Any], float, bool, Dict[str, Any]]:
        """
        Apply chosen action for current actor:
          - 0..3 -> P1..P4 slots (if unavailable -> treated as Skip)
          - 4    -> Skip
        Returns next observation for whoever acts next.
        """
        info = {"actor": self.actor, "action_idx": int(action_idx)}
        me, opp = self.actor, self._other(self.actor)

        # 1) Stun → lose entire turn immediately
        if self._is_stunned(me):
            info["forced_stun_skip"] = True
            self._end_turn_and_maybe_round()
            done, reward = self._terminal_and_reward()
            return self._obs(), reward, done, info

        # 2) Map index to slot or Skip, validate with mask
        slots = self._slots(me)                        # up to 4 non-skip actions
        mask = self._mask(slots, self.state[me]["ap"]) # [P1..P4, P5=0]
        is_skip = (action_idx == 4) or (action_idx not in (0,1,2,3)) or (mask[action_idx] == 0)

        ends_turn = False
        total_damage = 0

        # 3) Apply chosen
        if is_skip:
            info["used_skip"] = True
            self._log_action(me, self._skip_action())
            # Skip ends the entire turn immediately (no AP change, no partial action consumption)
            ends_turn = True
        else:
            chosen = slots[action_idx]
            cost = int(chosen.get("cost", 0))
            if cost > self.state[me]["ap"]:
                # Safety fallback; should not happen with mask
                info["fallback_skip_insufficient_ap"] = True
                self._log_action(me, self._skip_action())
                # Treat insufficient AP fallback as a Skip that ends the turn
                ends_turn = True
            else:
                self.state[me]["ap"] -= cost
                # Resolve effects in order
                for eff in chosen.get("effects", []):
                    code = int(eff.get("code", 0))
                    mult = int(eff.get("multiplier", 0))
                    dur  = int(eff.get("duration", 0))

                    if code in (1, 2, 3):
                        total_damage += self._attack(code, mult, me, opp)
                    elif code in BUFF_CODES:
                        self._buff(code, mult, dur, me)
                        ends_turn = True
                    elif code in DEBUFF_CODES:
                        self._debuff(code, mult, dur, opp)
                        ends_turn = True
                    elif code == SKIP_CODE:
                        pass  # ignore; skip already handled

                info["damage_dealt"] = total_damage
                self._log_action(me, chosen)
                if not ends_turn:
                    self.actions_left -= 1

        # 4) Terminal check
        done, reward = self._terminal_and_reward()
        if done:
            return self._obs(), reward, True, info

        # 5) Turn/round progression
        if ends_turn or self.actions_left <= 0:
            self._end_turn_and_maybe_round()

        # 6) Next obs
        done, reward = self._terminal_and_reward()
        return self._obs(), reward, done, info

    # -------------------------------------------------------------------------
    # Internal helpers (kept minimal)
    # -------------------------------------------------------------------------
    def _init_entity(self, f: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "level": int(f.get("level", 1)),
            "hpMax": int(f.get("hpMax", 100)),
            "hp": int(f.get("hp", f.get("hpMax", 100))),
            "speed": int(f.get("speed", 5)),
            "apMax": int(f.get("apMax", 4)),
            "ap": int(f.get("ap", 2)),
            "stats": copy.deepcopy(f.get("stats", {
                "phy_atk": 0, "phy_def": 0,
                "spi_atk": 0, "spi_def": 0,
                "ele_atk": 0, "ele_def": 0
            })),
            "actions": copy.deepcopy(f.get("actions", [])),
            "buff": {"code": 0, "multiplier": 0, "duration": 0},    # 4..6
            "debuff": {"code": 0, "multiplier": 0, "duration": 0},  # 7..9
        }

    def _is_stunned(self, who: str) -> bool:
        d = self.state[who]["debuff"]
        return d["code"] == 7 and d["duration"] > 0

    def _end_turn_and_maybe_round(self) -> None:
        """Finish current actor turn; if both acted, process end-of-round updates."""
        self.acted_this_round.add(self.actor)
        if len(self.acted_this_round) == 2:
            # End of round: +1 AP, poison DoT, tick durations, round++
            for side in ("ai", "enemy"):
                self.state[side]["ap"] = min(self.state[side]["apMax"], self.state[side]["ap"] + 1)
            for side in ("ai", "enemy"):
                deb = self.state[side]["debuff"]
                if deb["code"] == 8 and deb["duration"] > 0:
                    dot = math.floor(self.state[side]["hpMax"] * (deb["multiplier"] / 100.0))
                    self.state[side]["hp"] = max(0, self.state[side]["hp"] - dot)
            for side in ("ai", "enemy"):
                for slot in ("buff", "debuff"):
                    if self.state[side][slot]["duration"] > 0:
                        self.state[side][slot]["duration"] -= 1
                    if self.state[side][slot]["duration"] <= 0:
                        self.state[side][slot] = {"code": 0, "multiplier": 0, "duration": 0}
            self.round_count += 1
            self.acted_this_round.clear()
            # Next round starts with first_actor again
            self.actor = self.first_actor
        else:
            # Switch to the other actor within the same round
            self.actor = self._other(self.actor)
        self.actions_left = MAX_ACTIONS_PER_TURN

    def _attack(self, code: int, mult: int, atk_side: str, def_side: str) -> int:
        # Code mapping per spec:
        # 1 -> physical, 2 -> elemental, 3 -> spiritual
        key_atk, key_def = {
            1: ("phy_atk", "phy_def"),
            2: ("ele_atk", "ele_def"),
            3: ("spi_atk", "spi_def"),
        }[code]

        atk = max(0, int(self.state[atk_side]["stats"].get(key_atk, 0)))
        df  = max(0, int(self.state[def_side]["stats"].get(key_def, 0)))

        # Buffs (4: atk up on attacker, 5: def up on defender)
        atk_up = (self.state[atk_side]["buff"]["code"] == 4) * (self.state[atk_side]["buff"]["multiplier"] / 100.0)
        def_up = (self.state[def_side]["buff"]["code"] == 5) * (self.state[def_side]["buff"]["multiplier"] / 100.0)
        # Debuff 9 reduces holder's atk/def
        atk_down = (self.state[atk_side]["debuff"]["code"] == 9) * (self.state[atk_side]["debuff"]["multiplier"] / 100.0)
        def_down = (self.state[def_side]["debuff"]["code"] == 9) * (self.state[def_side]["debuff"]["multiplier"] / 100.0)

        atk_eff = atk * (1 + atk_up) * (1 - atk_down)
        def_eff = df  * (1 + def_up) * (1 - def_down)
        base = max(0.0, atk_eff - 0.5 * def_eff)
        dmg = max(1, math.floor(base * (mult / 100.0)))

        self.state[def_side]["hp"] = max(0, self.state[def_side]["hp"] - dmg)
        return dmg

    def _buff(self, code: int, mult: int, dur: int, target: str) -> None:
        if code == 6:  # heal now
            heal = math.floor(self.state[target]["hpMax"] * (mult / 100.0))
            self.state[target]["hp"] = min(self.state[target]["hpMax"], self.state[target]["hp"] + heal)
        self.state[target]["buff"] = {"code": code, "multiplier": mult, "duration": max(1, dur)}

    def _debuff(self, code: int, mult: int, dur: int, target: str) -> None:
        self.state[target]["debuff"] = {"code": code, "multiplier": mult, "duration": max(1, dur)}

    # -------------------------------------------------------------------------
    # Observation (bridge to your state_encoder)
    # -------------------------------------------------------------------------
    def _obs(self) -> Dict[str, Any]:
        me, opp = self.actor, self._other(self.actor)

        # 4 candidate actions (exclude Skip), padded to 4 entries
        slots = self._slots(me)
        mask = torch.tensor(self._mask(slots, self.state[me]["ap"]), dtype=torch.int32, device=self.device)

        # Build raw dict in the exact structure your normalizer/state_encoder expect
        recents = self._pad_actions(self.enemy_recent_actions, 3)
        ai_hist = self._pad_actions(self.ai_actions_history, 2)

        def actifs_of(who: str):
            buff, deb = self.state[who]["buff"], self.state[who]["debuff"]
            return [
                {"code": buff["code"], "multiplier": buff["multiplier"], "duration": buff["duration"]},
                {"code": deb["code"],  "multiplier": deb["multiplier"],  "duration": deb["duration"]},
            ]

        raw = {
            "enemy_recent_actions": recents,   # 3 actions
            "actifs": {
                "ai_actifs": actifs_of("ai"),
                "enemy_actifs": actifs_of("enemy"),
            },
            "combat_stats": {
                "ai_stats": {
                    "level": self.state["ai"]["level"], "hpMax": self.state["ai"]["hpMax"], "hp": self.state["ai"]["hp"],
                    "speed": self.state["ai"]["speed"], "apMax": self.state["ai"]["apMax"], "ap": self.state["ai"]["ap"],
                    "stats": {
                        "phy_atk": self.state["ai"]["stats"].get("phy_atk", 0),
                        "phy_def": self.state["ai"]["stats"].get("phy_def", 0),
                        "spi_atk":     self.state["ai"]["stats"].get("spi_atk", 0),
                        "spi_def":     self.state["ai"]["stats"].get("spi_def", 0),
                        "ele_atk":     self.state["ai"]["stats"].get("ele_atk", 0),
                        "ele_def":     self.state["ai"]["stats"].get("ele_def", 0),
                    }
                },
                "enemy_stats": {
                    "level": self.state["enemy"]["level"],
                    "hpMax": self.state["enemy"]["hpMax"],
                    "hp":    self.state["enemy"]["hp"],
                }
            },
            "combat_states": {"round_count": self.round_count, "action_left": self.actions_left},
            # IMPORTANT: keep this exact key for compatibility with your files (typo intentional)
            "ai_available_actions": self._pad_actions(slots, 4),
            "ai_actions_history": ai_hist,
        }

        # Build features without disk I/O
        data_list = self.encoder.dict_to_list(raw)
        assert len(data_list) == 92, f"Expected 92 features, got {len(data_list)}"
        features = torch.tensor(data_list, dtype=torch.float32, device=self.device)

        return {"who": me, "features": features, "mask": mask,
            "round_count": self.round_count, "actions_left": self.actions_left}

    # -------------------------------------------------------------------------
    # Small utilities (compact & focused)   
    # -------------------------------------------------------------------------
    def _slots(self, who: str) -> List[Dict[str, Any]]:
        """Return up to 4 actions excluding Skip; pad with empty actions."""
        acts = [a for a in self.state[who]["actions"] if self._first_code(a) != SKIP_CODE][:4]
        while len(acts) < 4:
            acts.append(self._empty_action())
        return acts

    def _mask(self, slots: List[Dict[str, Any]], ap: int) -> List[int]:
        """P1..P4 = 1 if slot non-empty & cost <= ap; P5 = 0 (decoder will force Skip)."""
        def non_empty(a):
            if a.get("cost", 0) > 0: return True
            for e in a.get("effects", []):
                if any(int(e.get(k, 0)) > 0 for k in ("code", "multiplier", "duration")):
                    return True
            return False
        m = [(1 if non_empty(s) and int(s.get("cost", 0)) <= ap else 0) for s in slots]
        m.append(0)  # Skip flag left 0 here
        return m

    def _pad_actions(self, arr: List[Dict[str, Any]], n: int) -> List[Dict[str, Any]]:
        """Keep last n; pad to n with empties; ensure exactly 2 effects."""
        out = list(arr)[-n:]
        while len(out) < n:
            out.insert(0, self._empty_action())
        fixed = []
        for a in out:
            effs = a.get("effects", [])
            if len(effs) < 2:
                effs = effs + [{"code": 0, "multiplier": 0, "duration": 0}] * (2 - len(effs))
            fixed.append({"cost": int(a.get("cost", 0)), "effects": effs[:2]})
        return fixed

    def _empty_action(self) -> Dict[str, Any]:
        return {"cost": 0, "effects": [
            {"code": 0, "multiplier": 0, "duration": 0},
            {"code": 0, "multiplier": 0, "duration": 0}
        ]}

    def _skip_action(self) -> Dict[str, Any]:
        return {"cost": 0, "effects": [
            {"code": SKIP_CODE, "multiplier": 0, "duration": 1},
            {"code": 0, "multiplier": 0, "duration": 0}
        ]}

    def _first_code(self, action: Dict[str, Any]) -> int:
        effs = action.get("effects", [])
        return int(effs[0].get("code", 0)) if effs else 0

    def _log_action(self, who: str, action: Dict[str, Any]) -> None:
        """Keep last 3 enemy actions, last 2 AI actions (for encoder)."""
        if who == "enemy":
            self.enemy_recent_actions.append(self._shrink_action(action))
            if len(self.enemy_recent_actions) > 3:
                self.enemy_recent_actions.pop(0)
        else:
            self.ai_actions_history.append(self._shrink_action(action))
            if len(self.ai_actions_history) > 2:
                self.ai_actions_history.pop(0)

    def _shrink_action(self, a: Dict[str, Any]) -> Dict[str, Any]:
        effs = a.get("effects", [])
        e1 = effs[0] if len(effs) > 0 else {"code": 0, "multiplier": 0, "duration": 0}
        e2 = effs[1] if len(effs) > 1 else {"code": 0, "multiplier": 0, "duration": 0}
        return {"cost": int(a.get("cost", 0)), "effects": [
            {"code": int(e1.get("code", 0)), "multiplier": int(e1.get("multiplier", 0)), "duration": int(e1.get("duration", 0))},
            {"code": int(e2.get("code", 0)), "multiplier": int(e2.get("multiplier", 0)), "duration": int(e2.get("duration", 0))}
        ]}

    def _other(self, who: str) -> str:
        return "enemy" if who == "ai" else "ai"

    def _terminal_and_reward(self) -> Tuple[bool, float]:
        ai_hp, en_hp = self.state["ai"]["hp"], self.state["enemy"]["hp"]
        if ai_hp <= 0 and en_hp <= 0: return True, 0.5
        if ai_hp <= 0: return True, 0.0
        if en_hp <= 0: return True, 1.0
        if self.round_count >= ROUND_CAP: return True, 0.25
        

        return False, 0.0
