from __future__ import annotations
import argparse
import os
import sys
import shutil
from typing import Any, Dict, List, Optional, Tuple

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


def _safe_dict_str(d: Any) -> str:
    if d is None:
        return "-"
    if isinstance(d, (list, tuple)):
        if not d:
            return "-"
        return ", ".join(_safe_dict_str(x) for x in d)
    if isinstance(d, dict):
        code = d.get("code", 0); mult = d.get("multiplier", d.get("mult", 0)); dur = d.get("duration", d.get("dur", 0))
        if code == 0 and mult == 0 and dur == 0:
            return "-"
        return f"{code}@{mult} x{dur}t"
    return str(d)


def fmt_effect(e: Dict[str, Any]) -> str:
    if not e:
        return "-"
    code = e.get("code", 0); mult = e.get("multiplier", e.get("mult", 0)); dur = e.get("duration", e.get("dur", 0))
    if code == 0 and mult == 0 and dur == 0:
        return "-"
    return f"{code}{CROSS}{mult} ({dur}t)"


def _panel(title: str, lines: List[str], color: str = Ansi.BOLD) -> str:
    term_w = _term_width()
    inner_w = min(max(36, max(len(title) + 6, *(len(l) for l in lines))), term_w - 4)
    top = f"{EDGE_TL}{EDGE_H*2} {title} " + EDGE_H * (inner_w - len(title) - 3) + EDGE_TR
    body = [f"{EDGE_V} " + _cut(line, inner_w) + " " * (inner_w - len(_cut(line, inner_w))) + EDGE_V for line in lines]
    bot = EDGE_BL + EDGE_H * (inner_w + 3) + EDGE_BR
    return "\n" + Ansi.c(top, color) + "\n" + "\n".join(body) + "\n" + Ansi.c(bot, color) + "\n"


def _entity_block(label: str, ent: Dict[str, Any], accent: str) -> str:
    hp = ent.get("hp", 0); hpM = ent.get("hpMax", 1)
    ap = ent.get("ap", 0); apM = ent.get("apMax", 1)
    hp_bar = _bar(hp, hpM)
    ap_bar = _bar(ap, apM, width=14, fill_char=AP_FILL)
    lines = [
        f"{Ansi.c(label, accent, Ansi.BOLD)}",
        f"HP [{Ansi.c(hp_bar, Ansi.GREEN)}] {hp}/{hpM} {_fmt_pct(hp, hpM)}",
        f"AP [{Ansi.c(ap_bar, Ansi.CYAN)}] {ap}/{apM}",
        f"Buffs  : {Ansi.c(_safe_dict_str(ent.get('buff')), Ansi.YELLOW)}",
        f"Debuffs: {Ansi.c(_safe_dict_str(ent.get('debuff')), Ansi.MAGENTA)}",
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
    print(_panel(title, header_lines, color=Ansi.GRAY))


def print_turn(env: CombatEnv) -> None:
    who = env.actor
    actor_lbl = "YOU" if who == HUMAN else "AI"
    me = env.state[who]
    opp = env.state[env._other(who)]
    title = f"{actor_lbl} TURN  |  Round {env.round_count}  |  Actions left: {env.actions_left}"
    me_line = f"{actor_lbl:<4} HP {me['hp']}/{me['hpMax']}  AP {me['ap']}/{me['apMax']}"
    opp_lbl = "AI" if actor_lbl == "YOU" else "YOU"
    opp_line = f"{opp_lbl:<4} HP {opp['hp']}/{opp['hpMax']}  AP {opp['ap']}/{opp['apMax']}"
    print(_panel(title, [me_line, opp_line], color=Ansi.BOLD))


def list_actions(env: CombatEnv, obs: Dict[str, Any]) -> None:
    slots = env._slots(env.actor)
    mask = obs["mask"].tolist()
    rows = ["#  COST  EFFECT-1                 EFFECT-2                 READY"]
    for i, a in enumerate(slots, start=1):
        e1 = _cut(fmt_effect(a["effects"][0]), 22)
        e2 = _cut(fmt_effect(a["effects"][1]), 22)
        ready = Ansi.c("YES", Ansi.GREEN) if mask[i - 1] == 1 else Ansi.c("NO", Ansi.RED)
        rows.append(f"{i:<2}  {a['cost']:^4}  {e1:<22}  {e2:<22}  {ready}")
    rows.append("5   -     SKIP                      -                      ALWAYS")
    print(_panel("Choose your action (1-5)", rows, color=Ansi.CYAN))


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
    print(_panel("State changes", rows, color=Ansi.YELLOW))


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
        lines.append("Applied: " + ", ".join(fmt_effect(e) for e in applied))
    expired = info.get("expired_effects")
    if expired:
        lines.append("Expired: " + ", ".join(fmt_effect(e) for e in expired))
    if not lines:
        lines.append(Ansi.c("(no special events)", Ansi.GRAY))
    print(_panel("Action result", lines, color=Ansi.MAGENTA))


@torch.no_grad()
def play(model_path: str, my_level: int, ai_level: int, use_gpu: bool = True) -> None:
    device = "cuda" if (use_gpu and torch.cuda.is_available()) else "cpu"

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

    f_you = gen_fighter(level=my_level)
    f_ai = gen_fighter(level=ai_level)

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
                        print(Ansi.c("Exiting game.", Ansi.DIM) + "\n"); return
                    choice = int(choice_str)
                    if not (1 <= choice <= 5):
                        raise ValueError
                    break
                except Exception:
                    print(Ansi.c("Invalid input. Please enter a number 1-5 (or 'q' to quit).", Ansi.RED) + "\n")
            action_idx = choice - 1
        else:
            feats = obs["features"].to(device)
            logits = policy(feats.unsqueeze(0)).squeeze(0)
            probs_tensor, action_idx, out_json = decode_action(logits, obs["mask"].to(device))
            action_idx = int(action_idx)
            p = probs_tensor.detach().cpu().numpy()
            prob_str = ", ".join(f"{x:.3f}" for x in p)
            print(_panel("Model decision", [f"Picked: {action_idx+1}", f"Probs: [{prob_str}]"], color=Ansi.GRAY))

        obs, reward, done, info = env.step(action_idx)

        now = Snapshot(env.state)
        print_action_result(info or {})
        print_deltas(prev, now)
        prev = now

    title = "RESULT"
    if reward >= 0.999:
        lines = [Ansi.c("You WIN! 🎉", Ansi.GREEN, Ansi.BOLD)]
    elif 0.249 <= reward < 0.751:
        lines = [Ansi.c("Draw. 🤝", Ansi.YELLOW, Ansi.BOLD)]
    else:
        lines = [Ansi.c("You lose. 💀", Ansi.RED, Ansi.BOLD)]
    lines.append(f"Rounds played: {env.round_count}")
    print(_panel(title, lines, color=Ansi.BLUE))

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
    model_path = "checkpoints/best_final.pt"
    my_level = 4
    ai_level = 4
    play(model_path=model_path, my_level=my_level, ai_level=ai_level)
