from __future__ import annotations
import os
import sys
import shutil
from typing import Any, Dict, List, Tuple

import torch

from ai.env.combat_env import CombatEnv
from ai.io.action_decoder import decode_action
from fighter_generator.fighter_gen import fighter_gen

# -------- Your trained model shape (must match training) --------
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


def gen_fighter(level: int) -> Dict[str, Any]:
    generator = fighter_gen()
    return generator._build_random_fighter(custom_level=level)


# Perspective mapping (CombatEnv uses 'ai' and 'enemy')
HUMAN = "enemy"  # you
BOT = "ai"       # the model


# =========================
# Terminal/format settings
# =========================
USE_ANSI = sys.stdout.isatty() and os.environ.get("NO_ANSI", "0") != "1"
USE_UNICODE = os.environ.get("ASCII", "0") != "1"

try:
    if os.name == "nt":
        import colorama  # type: ignore
        colorama.just_fix_windows_console()
except Exception:
    pass

USE_ANSI = sys.stdout.isatty() and os.environ.get("NO_ANSI", "0") != "1"


class Ansi:
    RESET = "\x1b[0m" if USE_ANSI else ""
    BOLD = "\x1b[1m" if USE_ANSI else ""
    DIM = "\x1b[2m" if USE_ANSI else ""
    ITAL = "\x1b[3m" if USE_ANSI else ""
    UNDER = "\x1b[4m" if USE_ANSI else ""

    RED = "\x1b[31m" if USE_ANSI else ""
    GREEN = "\x1b[32m" if USE_ANSI else ""
    YELLOW = "\x1b[33m" if USE_ANSI else ""
    BLUE = "\x1b[34m" if USE_ANSI else ""
    MAGENTA = "\x1b[35m" if USE_ANSI else ""
    CYAN = "\x1b[36m" if USE_ANSI else ""
    GRAY = "\x1b[90m" if USE_ANSI else ""

    @staticmethod
    def c(text: str, *styles: str) -> str:
        if not styles or not USE_ANSI:
            return str(text)
        return "".join(styles) + str(text) + Ansi.RESET


EDGE_H = "─" if USE_UNICODE else "-"
EDGE_V = "│" if USE_UNICODE else "|"
EDGE_TL = "┌" if USE_UNICODE else "+"
EDGE_TR = "┐" if USE_UNICODE else "+"
EDGE_BL = "└" if USE_UNICODE else "+"
EDGE_BR = "┘" if USE_UNICODE else "+"
HP_FILL = "█" if USE_UNICODE else "#"
AP_FILL = "■" if USE_UNICODE else "="
EMPTY = "·" if USE_UNICODE else "."
CROSS = "×" if USE_UNICODE else "x"
ARROW = "→" if USE_UNICODE else "->"
PLUSMINUS = "±" if USE_UNICODE else "+/-"


# =========================
# Effect dictionary & helpers
# =========================
# From your table (code numeric ↔ code string ↔ signification)
#   1 phy physical | 2 elm elemental | 3 spr spiritual
#   4 atk attack   | 5 def defense   | 6 med medical
#   7 stn stun     | 8 psn poison    | 9 imd intimidate
#  10 skp skip
EFFECTS_NUM: Dict[int, Tuple[str, str, str]] = {
    1: ("phy", "physical",  "Attaque basée sur la stat physique"),
    2: ("elm", "elemental",  "Attaque basée sur la stat élémentaire"),
    3: ("spr", "spiritual",  "Attaque basée sur la stat spirituelle"),
    4: ("atk", "attack",    "Augmentation des dégâts infligés"),
    5: ("def", "defense",   "Réduction des dégâts subis"),
    6: ("med", "medical",   "Régénération des PV"),
    7: ("stn", "stun",      "Le personnage saute son tour"),
    8: ("psn", "poison",    "Subit des dégâts passifs chaque tour"),
    9: ("imd", "intimidate","Réduction temporaire de l'atk et def"),
    10:("skp", "skip",      "Passer son tour"),
}
EFFECTS_CODE: Dict[str, Tuple[int, str, str]] = { v[0]: (k, v[1], v[2]) for k, v in EFFECTS_NUM.items() }

# Color per effect family
FAMILY_COLOR: Dict[str, str] = {
    "phy": Ansi.RED,
    "elm": Ansi.CYAN,
    "spr": Ansi.MAGENTA,
    "atk": Ansi.YELLOW,
    "def": Ansi.BLUE,
    "med": Ansi.GREEN,
    "stn": Ansi.RED,
    "psn": Ansi.GREEN,
    "imd": Ansi.GRAY,
    "skp": Ansi.DIM,
}


def _meta_from_code(code_val: Any) -> Tuple[str, int, str, str]:
    """Return (short_code, numeric_code, signification_en, fr_desc, color)."""
    if isinstance(code_val, int):
        short, sign, fr = EFFECTS_NUM.get(code_val, (str(code_val), "?", "?"))
        return short, code_val, sign, fr, FAMILY_COLOR.get(short, Ansi.GRAY)
    # strings like "phy"
    s = str(code_val)
    if s in EFFECTS_CODE:
        num, sign, fr = EFFECTS_CODE[s]
        return s, num, sign, fr, FAMILY_COLOR.get(s, Ansi.GRAY)
    return str(code_val), -1, "?", "?", Ansi.GRAY


# =========================
# Formatting helpers
# =========================

def _term_width(default: int = 100) -> int:
    try:
        return max(60, shutil.get_terminal_size().columns)
    except Exception:
        return default


def _cut(s: str, width: int) -> str:
    return s if len(s) <= width else s[: max(0, width - 1)] + "…"


def _bar(current: int, maximum: int, width: int = 18, fill_char: str = HP_FILL) -> str:
    maximum = max(1, maximum)
    current = max(0, min(current, maximum))
    filled = int(round(current / maximum * width))
    return fill_char * filled + EMPTY * (width - filled)


def _fmt_pct(current: int, maximum: int) -> str:
    maximum = max(1, maximum)
    pct = (current / maximum) * 100
    return f"{pct:5.1f}%"


# unified print for long blocks — always appends an extra newline
from sys import stdout

def pblock(text: str, pad: int = 1) -> None:
    stdout.write(text)
    stdout.write("\n" * max(1, pad))
    stdout.flush()


def fmt_effect_short(e: Dict[str, Any]) -> str:
    if not e:
        return "-"
    short, num, sign, fr, color = _meta_from_code(e.get("code", 0))
    mult = int(e.get("multiplier", e.get("mult", 0)))
    dur = int(e.get("duration", e.get("dur", 0)))
    parts = [Ansi.c(short.upper(), color, Ansi.BOLD)]
    if mult:
        parts.append(f"{mult}%")
    if dur:
        parts.append(f"{dur}t")
    return " ".join(parts)


def fmt_effect_verbose(e: Dict[str, Any]) -> str:
    if not e or e.get("code", 0) == 0:
        return "-"
    short, num, sign, fr, color = _meta_from_code(e.get("code", 0))
    mult = int(e.get("multiplier", e.get("mult", 0)))
    dur = int(e.get("duration", e.get("dur", 0)))
    head = f"[{Ansi.c(short.upper(), color, Ansi.BOLD)}|{num}] {sign}"
    extra = []
    if mult:
        extra.append(f"{mult}%")
    if dur:
        extra.append(f"{dur}t")
    if extra:
        head += " (" + ", ".join(extra) + ")"
    return head + f" — {fr}"



def legend_panel() -> str:
    rows = ["Code | Num | Signification — Effet"]
    for num in range(1, 11):
        short, sign, fr = EFFECTS_NUM[num]
        color = FAMILY_COLOR.get(short, Ansi.GRAY)
        rows.append(f"{Ansi.c(short.upper(), color, Ansi.BOLD):<4} | {num:<3} | {sign} — {fr}")
    return _panel("Legend: effects", rows, Ansi.GRAY)


def _panel(title: str, lines: List[str], color: str = Ansi.BOLD) -> str:
    term_w = _term_width()
    inner_w = min(max(36, max(len(title) + 6, *(len(l) for l in lines))), term_w - 4)
    top = f"{EDGE_TL}{EDGE_H*2} {title} " + EDGE_H * (inner_w - len(title) - 3) + EDGE_TR
    body = [f"{EDGE_V} " + _cut(line, inner_w) + " " * (inner_w - len(_cut(line, inner_w))) + EDGE_V for line in lines]
    bot = EDGE_BL + EDGE_H * (inner_w + 3) + EDGE_BR
    return Ansi.c(top, color) + "\n" + "\n".join(body) + "\n" + Ansi.c(bot, color)


def _effect_line(label: str, e: Dict[str, Any]) -> str:
    if not e or not e.get("code", 0):
        return f"{label}: -"
    return f"{label}: {fmt_effect_verbose(e)}"


def _entity_block(label: str, ent: Dict[str, Any], accent: str) -> str:
    hp = ent.get("hp", 0); hpM = ent.get("hpMax", 1)
    ap = ent.get("ap", 0); apM = ent.get("apMax", 1)
    hp_bar = _bar(hp, hpM)
    ap_bar = _bar(ap, apM, width=14, fill_char=AP_FILL)
    lines = [
        f"{Ansi.c(label, accent, Ansi.BOLD)}",
        f"HP [{Ansi.c(hp_bar, Ansi.GREEN)}] {hp}/{hpM} {_fmt_pct(hp, hpM)}",
        f"AP [{Ansi.c(ap_bar, Ansi.CYAN)}] {ap}/{apM}",
        _effect_line("Buff", ent.get("buff", {})),
        _effect_line("Debuff", ent.get("debuff", {})),
    ]
    return "\n".join(lines)


def print_header(env: CombatEnv) -> None:
    you = env.state[HUMAN]; ai = env.state[BOT]
    title = "FIGHT START"
    me_block = _entity_block("YOU", you, Ansi.BLUE)
    ai_block = _entity_block("AI", ai, Ansi.RED)
    header_lines = [
        f"Round: {env.round_count}   Actor: {Ansi.c(env.actor.upper(), Ansi.BOLD)}",
        "",
        me_block,
        "",
        ai_block,
    ]
    pblock(_panel(title, header_lines, color=Ansi.GRAY), pad=2)
    # Show a one-time legend so the meanings are clear
    pblock(legend_panel(), pad=2)


def print_turn(env: CombatEnv) -> None:
    who = env.actor
    actor_lbl = "YOU" if who == HUMAN else "AI"
    me = env.state[who]
    opp = env.state[env._other(who)]
    title = f"{actor_lbl} TURN  |  Round {env.round_count}  |  Actions left: {env.actions_left}"
    me_line = f"{actor_lbl:<4} HP {me['hp']}/{me['hpMax']}  AP {me['ap']}/{me['apMax']}"
    opp_lbl = "AI" if actor_lbl == "YOU" else "YOU"
    opp_line = f"{opp_lbl:<4} HP {opp['hp']}/{opp['hpMax']}  AP {opp['ap']}/{opp['apMax']}"
    pblock(_panel(title, [me_line, opp_line], color=Ansi.BOLD), pad=1)


def list_actions(env: CombatEnv, obs: Dict[str, Any]) -> None:
    slots = env._slots(env.actor)  # up to 4 actions (Skip is implicit)
    mask = obs["mask"].tolist()
    # generous columns for meanings
    col_w = max(36, (_term_width() - 26) // 2)
    rows = ["#  COST  EFFECT-1".ljust(col_w + 10) + "EFFECT-2".ljust(col_w) + "READY"]
    for i, a in enumerate(slots, start=1):
        e1 = _cut(fmt_effect_verbose(a["effects"][0]), col_w)
        e2 = _cut(fmt_effect_verbose(a["effects"][1]), col_w)
        ready = Ansi.c("YES", Ansi.GREEN) if mask[i - 1] == 1 else Ansi.c("NO", Ansi.RED)
        rows.append(f"{i:<2}  {a['cost']:^4}  {e1:<{col_w}}  {e2:<{col_w}}  {ready}")
    rows.append("5   -     SKIP (always allowed)")
    pblock(_panel("Choose your action (1-5)", rows, color=Ansi.CYAN), pad=1)


class Snapshot:
    def __init__(self, state: Dict[str, Dict[str, Any]]):
        self.human = dict(state[HUMAN])
        self.ai = dict(state[BOT])


def _delta(a: int, b: int) -> Tuple[str, int]:
    d = b - a
    if d == 0:
        return Ansi.c(f"{PLUSMINUS}0", Ansi.GRAY), d
    col = Ansi.GREEN if d > 0 else Ansi.RED
    sign = "+" if d > 0 else ""
    return Ansi.c(f"{sign}{d}", col), d


def print_deltas(before: Snapshot, after: Snapshot) -> None:
    rows = ["STAT     YOU        AI"]
    for key, label in (("hp", "HP"), ("ap", "AP")):
        y_before, y_after = before.human.get(key, 0), after.human.get(key, 0)
        a_before, a_after = before.ai.get(key, 0), after.ai.get(key, 0)
        y_delta, _ = _delta(y_before, y_after)
        a_delta, _ = _delta(a_before, a_after)
        rows.append(f"{label:<7}  {y_before:>3}{ARROW}{y_after:<3} {y_delta:<5}   {a_before:>3}{ARROW}{a_after:<3} {a_delta:<5}")
    pblock(_panel("State changes", rows, color=Ansi.YELLOW), pad=1)


def print_action_result(info: Dict[str, Any]) -> None:
    actor = info.get("actor", "?")
    actor_lbl = "YOU" if actor == HUMAN else "AI"
    lines: List[str] = []
    if info.get("forced_stun_skip"):
        lines.append(Ansi.c(f"{actor_lbl} was stunned and lost the turn!", Ansi.RED))
    elif info.get("used_skip"):
        lines.append(Ansi.c(f"{actor_lbl} chose SKIP.", Ansi.GRAY))
    dmg = info.get("damage_dealt")
    if dmg is not None:
        lines.append(f"Damage dealt: {Ansi.c(str(dmg), Ansi.RED)}")
    applied = info.get("applied_effects")
    if applied:
        lines.append("Applied: " + ", ".join(fmt_effect_short(e) for e in applied))
    expired = info.get("expired_effects")
    if expired:
        lines.append("Expired: " + ", ".join(fmt_effect_short(e) for e in expired))
    if not lines:
        lines.append(Ansi.c("(no special events)", Ansi.GRAY))
    pblock(_panel("Action result", lines, color=Ansi.MAGENTA), pad=1)


# -------- Game loop: You (enemy) vs Model (ai) --------
@torch.no_grad()
def play(model_path: str, my_level: int, ai_level: int, use_gpu: bool = True) -> None:
    device = "cuda" if (use_gpu and torch.cuda.is_available()) else "cpu"

    # Load model
    policy = PolicyMLP().to(device).eval()
    ckpt = torch.load(model_path, map_location=device)
    if isinstance(ckpt, dict):
        if "state_dict" in ckpt and isinstance(ckpt["state_dict"], dict):
            state_dict = ckpt["state_dict"]
        elif "best_state_dict" in ckpt and isinstance(ckpt["best_state_dict"], dict):
            state_dict = ckpt["best_state_dict"]
        elif all(isinstance(v, torch.Tensor) for v in ckpt.values()):
            state_dict = ckpt
        else:
            raise ValueError("Unsupported checkpoint format.")
    else:
        state_dict = ckpt
    policy.load_state_dict(state_dict, strict=True)

    # Make fighters
    f_you = gen_fighter(level=my_level)
    f_ai = gen_fighter(level=ai_level)

    # Start env
    env = CombatEnv(encoder_json_path="ai/data/data.json", device=device)
    obs = env.reset(f_ai, f_you)
    print_header(env)

    done = False
    prev = Snapshot(env.state)

    while not done:
        print_turn(env)

        if obs["who"] == HUMAN:
            list_actions(env, obs)
            while True:
                try:
                    choice_str = input("Enter 1-5 (q to quit): ").strip()
                    if choice_str.lower() in ("q", "quit", "exit"):
                        pblock(Ansi.c("Exiting game.", Ansi.DIM), pad=2); return
                    choice = int(choice_str)
                    if not (1 <= choice <= 5):
                        raise ValueError
                    break
                except Exception:
                    pblock(Ansi.c("Invalid input. Please enter a number 1-5 (or 'q' to quit).", Ansi.RED), pad=1)
            action_idx = choice - 1
        else:
            feats = obs["features"].to(device)
            logits = policy(feats.unsqueeze(0)).squeeze(0)
            probs_tensor, action_idx, _ = decode_action(logits, obs["mask"].to(device))
            action_idx = int(action_idx)
            p = ", ".join(f"{x:.3f}" for x in probs_tensor.detach().cpu().numpy())
            pblock(_panel("Model decision", [f"Picked: {action_idx+1}", f"Probs: [{p}]"], color=Ansi.GRAY), pad=1)

        obs, reward, done, info = env.step(action_idx)

        # Feedback and state changes
        print_action_result(info or {})
        now = Snapshot(env.state)
        print_deltas(prev, now)
        # Reprint both entities with active effects highlighted
        pblock(_panel("Status", [ _entity_block("YOU", env.state[HUMAN], Ansi.BLUE), "", _entity_block("AI", env.state[BOT], Ansi.RED) ], color=Ansi.YELLOW), pad=1)
        prev = now

    # Result
    title = "RESULT"
    if reward >= 0.999:
        lines = [Ansi.c("You WIN! 🎉", Ansi.GREEN, Ansi.BOLD)]
    elif 0.249 <= reward < 0.751:
        lines = [Ansi.c("Draw. 🤝", Ansi.YELLOW, Ansi.BOLD)]
    else:
        lines = [Ansi.c("You lose. 💀", Ansi.RED, Ansi.BOLD)]
    lines.append(f"Rounds played: {env.round_count}")
    pblock(_panel(title, lines, color=Ansi.BLUE), pad=2)

""" if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Play against the AI with clean terminal output")
    parser.add_argument("--model", dest="model_path", default="ai/checkpoints/best_final.pt")
    parser.add_argument("--my-level", dest="my_level", type=int, default=4)
    parser.add_argument("--ai-level", dest="ai_level", type=int, default=4)
    parser.add_argument("--cpu", action="store_true", help="Force CPU even if CUDA is available")
    parser.add_argument("--ascii", action="store_true", help="Force ASCII borders (no box-drawing chars)")
    parser.add_argument("--no-ansi", action="store_true", help="Disable ANSI colors")
    args = parser.parse_args()

    if args.ascii:
        os.environ["ASCII"] = "1"
    if args.no_ansi:
        os.environ["NO_ANSI"] = "1"

    play(model_path=args.model_path, my_level=args.my_level, ai_level=args.ai_level, use_gpu=not args.cpu) """


if __name__ == "__main__":
    # model_path = "checkpoints/best_final.pt"
    model_path = "checkpoints/best_so_far.pt"
    my_level = 5
    ai_level = 5
    play(model_path=model_path, my_level=my_level, ai_level=ai_level)
