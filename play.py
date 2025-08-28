# play.py — Web gameplay UI + NN Live Visualization pushes
from __future__ import annotations
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any, Dict, List, Tuple
import os
import urllib.request

import torch
from ai.env.combat_env import CombatEnv
from ai.io.action_decoder import decode_action
from fighter_generator.fighter_gen import fighter_gen


# ===== Model =====
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


FEATURE_NAMES = [
    # Enemy recent actions (3x7 = 21)
    *[f"enemy_recent_action{i}_{fld}"
      for i in range(1,4)
      for fld in ["cost","eff1_code","eff1_mult","eff1_dur","eff2_code","eff2_mult","eff2_dur"]],
    
    # AI actifs (buff, debuff)
    "ai_buff_code","ai_buff_mult","ai_buff_dur",
    "ai_debuff_code","ai_debuff_mult","ai_debuff_dur",

    # Enemy actifs
    "enemy_buff_code","enemy_buff_mult","enemy_buff_dur",
    "enemy_debuff_code","enemy_debuff_mult","enemy_debuff_dur",

    # AI stats
    "ai_level","ai_hpMax","ai_hp","ai_speed","ai_apMax","ai_ap",

    # AI detailed stats
    "ai_phy_atk","ai_phy_def","ai_spi_atk","ai_spi_def","ai_ele_atk","ai_ele_def",

    # Enemy stats
    "enemy_level","enemy_hpMax","enemy_hp",

    # Combat states
    "round_count","actions_left",

    # AI available actions (4x7 = 28)
    *[f"ai_avail_action{i}_{fld}"
      for i in range(1,5)
      for fld in ["cost","eff1_code","eff1_mult","eff1_dur","eff2_code","eff2_mult","eff2_dur"]],

    # AI history (2x7 = 14)
    *[f"ai_hist_action{i}_{fld}"
      for i in range(1,3)
      for fld in ["cost","eff1_code","eff1_mult","eff1_dur","eff2_code","eff2_mult","eff2_dur"]],
]
assert len(FEATURE_NAMES) == 92


# ===== Effect labels =====
EFFECTS_NUM: Dict[int, Tuple[str, str, str]] = {
    1: ("phy", "physical",  "Attaque basée sur la stat physique"),
    2: ("elm", "elemental", "Attaque basée sur la stat élémentaire"),
    3: ("spr", "spiritual", "Attaque basée sur la stat spirituelle"),
    4: ("atk", "attack",    "Augmentation des dégâts infligés"),
    5: ("def", "defense",   "Réduction des dégâts subis"),
    6: ("med", "medical",   "Régénération des PV"),
    7: ("stn", "stun",      "Le personnage saute son tour"),
    8: ("psn", "poison",    "Subit des dégâts passifs chaque tour"),
    9: ("imd", "intimidate","Réduction temporaire de l'atk et def"),
    10:("skp", "skip",      "Passer son tour"),
}

def fmt_effect(e: Dict[str, Any]) -> str:
    if not e or int(e.get("code", 0)) == 0:
        return "-"
    code = int(e.get("code", 0))
    mult = int(e.get("multiplier", e.get("mult", 0)))
    dur  = int(e.get("duration", e.get("dur", 0)))
    short, sign, _ = EFFECTS_NUM.get(code, (str(code), "?", "?"))
    parts = []
    if mult: parts.append(f"{mult}%")
    if dur:  parts.append(f"{dur}t")
    tail = f" ({', '.join(parts)})" if parts else ""
    return f"[{short.upper()}|{code}] {sign}{tail}"


# ===== NN Live Viz client =====
VIZ_ENABLED = True
VIZ_URL = os.environ.get("VIZ_PUSH_URL", "http://127.0.0.1:8765/push")
_VIZ_WARNED = False

def push_viz(frame: dict):
    """POST a frame to nn_viz_server; warn once if it fails."""
    global _VIZ_WARNED
    if not VIZ_ENABLED:
        return
    try:
        req = urllib.request.Request(
            VIZ_URL,
            data=json.dumps(frame).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=1.2).read()
    except Exception as e:
        if not _VIZ_WARNED:
            _VIZ_WARNED = True
            print(f"[viz] push failed: {e}  (tip: run nn_viz_server.py or set VIZ_PUSH_URL)")

# draw ALL edges; nn_viz_server will render weak ones as thin & faint
VIZ_EDGE_EPS = 1e-8

def _minmax01(t: torch.Tensor) -> torch.Tensor:
    # maps to [0,1], safe for constants
    mn = t.min()
    mx = t.max()
    if float(mx - mn) < 1e-12:
        return torch.zeros_like(t)
    return (t - mn) / (mx - mn)

def collect_frame(policy, feats, picked, probs, mask=None):
    with torch.no_grad():
        x = feats.detach().flatten()                  # (92,)
        l0 = policy.net[0]; l1 = policy.net[2]; l2 = policy.net[4]
        h1_pre = l0(x);  h1 = torch.relu(h1_pre)      # (128,)
        h2_pre = l1(h1); h2 = torch.relu(h2_pre)      # (64,)
        out_pre = l2(h2)                              # (5,)
        out_prob = probs

        # normalize activations for node sizes (0..1)
        x_n  = _minmax01(x)
        h1_n = _minmax01(h1)
        h2_n = _minmax01(h2)
        o_n  = _minmax01(out_prob)

        layers = [
            {"name": f"input({x.numel()})",
             "a": x_n.cpu().tolist(),
             "a_raw": x.cpu().tolist(),
             "labels": FEATURE_NAMES},
            {"name": f"h1({h1.numel()})",
             "a": h1_n.cpu().tolist(),
             "a_raw": None,
             "labels": None},
            {"name": f"h2({h2.numel()})",
             "a": h2_n.cpu().tolist(),
             "a_raw": None,
             "labels": None},
            {"name": f"output({out_prob.numel()})",
             "a": o_n.cpu().tolist(),
             "a_raw": out_prob.detach().cpu().tolist(),
             "labels": [str(i+1) for i in range(out_prob.numel())]},
        ]

        edges = []

        def dense_edges(src_act: torch.Tensor, W: torch.Tensor, dst_act: torch.Tensor, srcL: int, dstL: int):
            # strength = |w| * src_activation   (per-connection saliency for THIS input)
            w = W.weight.detach()               # (dst, src)
            s = torch.abs(w) * src_act.unsqueeze(0)  # (dst, src)
            s = s.t()                           # (src, dst)
            # normalize to [0,1] for visual width/opacity
            m = float(s.max())
            if m < VIZ_EDGE_EPS:
                s01 = torch.zeros_like(s)
            else:
                s01 = (s / m).clamp_min(0.0)

            conns = []
            S, D = s01.shape
            for i in range(S):
                row = s01[i]
                for j in range(D):
                    v = float(row[j])
                    if v > 0.0:                 # keep even tiny contributions
                        conns.append([i, j, v])
            edges.append({"srcLayer": srcL, "dstLayer": dstL, "conns": conns})

        dense_edges(x_n,  l0, h1_n, 0, 1)
        dense_edges(h1_n, l1, h2_n, 1, 2)
        dense_edges(h2_n, l2, o_n,  2, 3)

        return {
            "layers": layers,
            "edges": edges,
            "meta": {"picked": int(picked)},
        }


# ===== Game wrapper (unchanged) =====
class Game:
    def __init__(self, model_path: str, my_level: int = 5, ai_level: int = 5, device: str | None = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        # Model
        self.policy = PolicyMLP().to(self.device).eval()
        ckpt = torch.load(model_path, map_location=self.device)
        if isinstance(ckpt, dict):
            if "state_dict" in ckpt: state = ckpt["state_dict"]
            elif "best_state_dict" in ckpt: state = ckpt["best_state_dict"]
            elif all(isinstance(v, torch.Tensor) for v in ckpt.values()): state = ckpt
            else: raise ValueError("Unsupported checkpoint format.")
        else:
            state = ckpt
        self.policy.load_state_dict(state, strict=True)

        # Env + fighters
        f_you = fighter_gen()._build_random_fighter(custom_level=my_level)
        f_ai  = fighter_gen()._build_random_fighter(custom_level=ai_level)
        self.env = CombatEnv(device=self.device)
        self.env.reset(f_ai, f_you)

        self.logs: List[str] = []
        self.done = False
        self.last_reward = 0.0

        # Push an initial frame so the viz isn't blank
        try:
            obs = self.env._make_obs()
            feats = obs["features"].to(self.device)
            logits = self.policy(feats.unsqueeze(0)).squeeze(0)
            probs = torch.softmax(logits, -1)
            frame = collect_frame(self.policy, feats, picked=int(torch.argmax(probs)), probs=probs)
            push_viz(frame)
        except Exception as e:
            print("[viz] initial frame failed:", e)

    # ---- helpers for UI payloads ----
    def _side_payload(self, who: str) -> Dict[str, Any]:
        s = self.env.state[who]
        return {
            "label": ("YOU" if who == "enemy" else "AI"),
            "hp": s["hp"], "hpMax": s["hpMax"],
            "ap": s["ap"], "apMax": s["apMax"],
            "speed": s["speed"], "level": s["level"],
            "stats": s["stats"],
            "buff": fmt_effect(s.get("buff", {})),
            "debuff": fmt_effect(s.get("debuff", {})),
        }

    def _actions_for(self, who: str) -> List[Dict[str, Any]]:
        slots = self.env._slots(who)[:4]
        ap = self.env.state[who]["ap"]
        mask = [(1 if int(a.get("cost", 0)) <= ap else 0) for a in slots]
        rows = []
        for i, a in enumerate(slots, start=1):
            e1 = fmt_effect(a["effects"][0])
            e2 = fmt_effect(a["effects"][1])
            rows.append({
                "idx": i,
                "cost": int(a.get("cost", 0)),
                "e1": e1, "e2": e2,
                "ready": bool(mask[i-1] == 1),
            })
        rows.append({"idx": 5, "cost": "-", "e1": "[SKP|10] skip", "e2": "-", "ready": True})
        return rows

    def _obs_meta(self) -> Dict[str, Any]:
        return {
            "round": self.env.round_count,
            "actor": self.env.actor,
            "actorLabel": ("YOU" if self.env.actor == "enemy" else "AI"),
            "actionsLeft": self.env.actions_left,
            "done": self.done,
            "reward": self.last_reward,
        }

    def state_json(self) -> Dict[str, Any]:
        return {
            "meta": self._obs_meta(),
            "you": self._side_payload("enemy"),
            "ai": self._side_payload("ai"),
            "you_actions": self._actions_for("enemy"),
            "ai_actions": self._actions_for("ai"),
            "log": self.logs[-400:],
        }

    def log(self, text: str):
        self.logs.append(text)
        if len(self.logs) > 2000:
            self.logs = self.logs[-2000:]

    def step_human(self, idx_0_to_4: int):
        if self.done: return
        if self.env.actor != "enemy":
            self.log("⚠️ It's not your turn.")
            return

        slots = self.env._slots("enemy")[:4]
        ap = self.env.state["enemy"]["ap"]
        legal = (idx_0_to_4 == 4) or (0 <= idx_0_to_4 <= 3 and int(slots[idx_0_to_4].get("cost", 0)) <= ap)
        if not legal:
            self.log("❌ Invalid/Not ready action. Using SKIP.")
            idx_0_to_4 = 4

        # Push a frame for YOUR forward pass too (uses current actor's obs)
        try:
            obs = self.env._make_obs()
            feats = obs["features"].to(self.device)
            logits = self.policy(feats.unsqueeze(0)).squeeze(0)
            probs = torch.softmax(logits, -1)
            frame = collect_frame(self.policy, feats, picked=idx_0_to_4, probs=probs)
            push_viz(frame)
        except Exception:
            pass

        _, reward, done, info = self.env.step(idx_0_to_4)

        if info.get("damage_dealt") is not None:
            self.log(f"🗡️ YOU dealt {int(info['damage_dealt'])} dmg.")
        if info.get("used_skip"): self.log("⏭️ YOU chose Skip.")
        if info.get("forced_stun_skip"): self.log("💫 YOU was stunned and lost the turn.")
        if info.get("applied_effects"):
            self.log("✨ Applied: " + ", ".join(fmt_effect(e) for e in info["applied_effects"]))
        if info.get("expired_effects"):
            self.log("⌛ Expired: " + ", ".join(fmt_effect(e) for e in info["expired_effects"]))

        self.last_reward, self.done = reward, done
        if not self.done and self.env.actor == "ai":
            self.ai_move()

    def ai_move(self):
        if self.done: return
        for _ in range(12):
            if self.env.actor != "ai":
                break
            obs = self.env._make_obs()
            feats = obs["features"].to(self.device)
            mask  = obs["mask"].to(self.device)  # [5]
            logits = self.policy(feats.unsqueeze(0)).squeeze(0)
            probs_tensor = torch.softmax(logits, dim=-1)

            # Decode action with correct 5-long mask
            probs_tensor, action_idx, _ = decode_action(logits, mask)
            action_idx = int(action_idx)

            # Push viz frame BEFORE stepping (this is the actual decision pass)
            try:
                frame = collect_frame(self.policy, feats, picked=action_idx, probs=probs_tensor)
                push_viz(frame)
            except Exception:
                pass

            p_list = [float(x) for x in probs_tensor.detach().cpu().tolist()]
            self.log(f"🤖 AI picks {action_idx+1}  (probs={', '.join(f'{x:.2f}' for x in p_list)})")

            _, reward, done, info = self.env.step(action_idx)
            if info.get("damage_dealt") is not None:
                self.log(f"💥 AI dealt {int(info['damage_dealt'])} dmg.")
            if info.get("used_skip"): self.log("⏭️ AI chose Skip.")
            if info.get("forced_stun_skip"): self.log("💫 AI was stunned and lost the turn.")
            if info.get("applied_effects"):
                self.log("✨ Applied: " + ", ".join(fmt_effect(e) for e in info["applied_effects"]))
            if info.get("expired_effects"):
                self.log("⌛ Expired: " + ", ".join(fmt_effect(e) for e in info["expired_effects"]))

            self.last_reward, self.done = reward, done
            if done or self.env.actor != "ai":
                break


# ===== HTTP server =====
AUTOPLAY_AI = True

INDEX_HTML = r"""<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<title>RPG Duel — Web UI</title>
<style>
  :root {
    --bg: #F7FAFF; --bg2: #FFFFFF; --panel: #FFFFFF; --panel-bdr: #E3EAF4;
    --fg: #0B1220; --dim: #5A6B86; --rail: #E8EEF7;
    --you: #2563EB; --ai: #DC2626; --hp: #16A34A; --ap: #0891B2; --buff:#CA8A04; --debuff:#EA580C;
    --ready:#10B981; --notready:#EF4444;
  }
  html, body { height:100%; }
  body { margin:0; background:var(--bg); color:var(--fg); font:14px/1.5 system-ui,Segoe UI,Roboto,Arial,sans-serif; }
  header { display:flex; align-items:center; justify-content:space-between; gap:16px;
    padding:12px 16px; background:var(--bg2); border-bottom:1px solid var(--panel-bdr); position:sticky; top:0; z-index:2; }
  .title { font-weight:700; }
  .meta { color:var(--dim); font-size:12px; }
  .wrap { display:grid; grid-template-columns: 1fr 1fr 380px; gap:16px; padding:16px; }
  .card { background:var(--panel); border:1px solid var(--panel-bdr); border-radius:12px; padding:14px; box-shadow: 0 6px 14px rgba(0,0,0,.06); }
  h3 { margin:0 0 10px 0; font-size:16px; }
  table { width:100%; border-collapse: collapse; font-size:13px; }
  th, td { text-align:left; padding:6px 6px; border-bottom:1px dashed var(--panel-bdr); color:var(--fg); }
  th { color:var(--dim); font-weight:600; }
  .bar { height:14px; background:var(--rail); border:1px solid var(--panel-bdr); border-radius:8px; overflow:hidden; }
  .hp .fill { background: var(--hp); height:100%; }
  .ap .fill { background: var(--ap); height:100%; }
  .row { display:grid; grid-template-columns: 1fr 1fr; gap:10px; margin-bottom:8px; }
  .badge { display:inline-block; padding:2px 8px; border-radius:999px; font-size:12px; border:1px solid var(--panel-bdr); background:#F5F9FF; }
  .you { color:var(--you); } .ai { color:var(--ai); }
  .actions { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 12px; }
  .ready { color:var(--ready); font-weight:600; } .notready { color:var(--notready); }
  .log { height: 70vh; overflow:auto; white-space: pre-wrap; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size:12px; background:#FCFEFF; border-radius:10px; padding:10px; border:1px solid var(--panel-bdr); }
  .controls { display:flex; gap:8px; align-items:center; }
  input[type=text] { background:#FFFFFF; border:1px solid var(--panel-bdr); color:var(--fg); border-radius:8px; padding:8px 10px; width:140px; }
  input[disabled] { background:#F2F5FA; color:#9AA7BD; }
  button { background:#0F172A; color:#FFFFFF; border:1px solid #0F172A; border-radius:8px; padding:8px 12px; cursor:pointer; }
  button:disabled { background:#A8B2C2; border-color:#A8B2C2; cursor:not-allowed; }
  button:hover:not(:disabled) { filter: brightness(1.1); }
</style>
</head>
<body>
<header>
  <div class="title">RPG Duel — Web UI</div>
  <div class="meta">Type an action (1–5) and press Enter. <b>R</b> to refresh. Skip is 5.</div>
</header>

<div class="wrap">
  <div class="card" id="youCard">
    <h3>YOU <span class="badge you">enemy</span></h3>
    <div class="row">
      <div><div class="meta">HP</div><div class="bar hp"><div class="fill" id="youHP"></"></div></div></div>
      <div><div class="meta">AP</div><div class="bar ap"><div class="fill" id="youAP"></div></div></div>
    </div>
    <table>
      <tr><th>Level</th><td id="youLevel"></td><th>Speed</th><td id="youSpeed"></td></tr>
      <tr><th>Buff</th><td colspan="3" class="buff" id="youBuff">-</td></tr>
      <tr><th>Debuff</th><td colspan="3" class="debuff" id="youDebuff">-</td></tr>
    </table>
    <h3 style="margin-top:12px;">Stats</h3>
    <table id="youStats"></table>

    <h3 style="margin-top:12px;">Actions</h3>
    <div class="actions" id="youActions"></div>
  </div>

  <div class="card" id="aiCard">
    <h3>AI <span class="badge ai">ai</span></h3>
    <div class="row">
      <div><div class="meta">HP</div><div class="bar hp"><div class="fill" id="aiHP"></div></div></div>
      <div><div class="meta">AP</div><div class="bar ap"><div class="fill" id="aiAP"></div></div></div>
    </div>
    <table>
      <tr><th>Level</th><td id="aiLevel"></td><th>Speed</th><td id="aiSpeed"></td></tr>
      <tr><th>Buff</th><td colspan="3" class="buff" id="aiBuff">-</td></tr>
      <tr><th>Debuff</th><td colspan="3" class="debuff" id="aiDebuff">-</td></tr>
    </table>
    <h3 style="margin-top:12px;">Stats</h3>
    <table id="aiStats"></table>

    <h3 style="margin-top:12px;">Actions</h3>
    <div class="actions" id="aiActions"></div>
  </div>

  <div class="card">
    <h3>Control</h3>
    <div class="meta">Round <span id="round"></span> • Actor: <span id="actor"></span> • Actions left: <span id="actsLeft"></span></div>
    <div class="controls" style="margin:10px 0;">
      <input type="text" id="actionInput" placeholder="1..5"/>
      <button id="playBtn" onclick="play()">Play</button>
      <button onclick="refresh()">Refresh</button>
    </div>
    <h3>Log</h3>
    <div class="log" id="log"></div>
  </div>
</div>

<script>
async function api(path, opts){
  const res = await fetch(path, Object.assign({cache:'no-cache'}, opts||{}));
  if(!res.ok) throw new Error(res.statusText);
  return await res.json();
}
function pct(a,b){ b=Math.max(1,b); return Math.max(0, Math.min(100, (a/b)*100)); }
function fillBar(el, a, b){ el.style.width = pct(a,b) + '%'; }
function setStatsTable(tbl, stats){
  tbl.innerHTML = '';
  const rows = [['phy_atk','phy_def'],['ele_atk','ele_def'],['spi_atk','spi_def']];
  rows.forEach(pair=>{
    const tr = document.createElement('tr');
    pair.forEach(k=>{
      const th = document.createElement('th'); th.textContent = k; tr.appendChild(th);
      const td = document.createElement('td'); td.textContent = stats[k] ?? 0; tr.appendChild(td);
    });
    tbl.appendChild(tr);
  });
}
function setActions(el, actions){
  el.innerHTML = '';
  actions.forEach(r=>{
    const div = document.createElement('div');
    div.innerHTML = `<span class="${r.ready?'ready':'notready'}">[${r.idx}]</span>
      cost=${r.cost} • ${r.e1}  |  ${r.e2}`;
    el.appendChild(div);
  });
}
function render(state){
  document.getElementById('round').textContent = state.meta.round;
  document.getElementById('actor').textContent = state.meta.actorLabel;
  document.getElementById('actsLeft').textContent = state.meta.actionsLeft;

  const isYourTurn = (state.meta.actor === 'enemy');
  const inputEl = document.getElementById('actionInput');
  const playBtn = document.getElementById('playBtn');
  inputEl.disabled = !isYourTurn;
  playBtn.disabled = !isYourTurn;
  if (isYourTurn) { inputEl.focus(); }

  const you = state.you;
  fillBar(document.getElementById('youHP'), you.hp, you.hpMax);
  fillBar(document.getElementById('youAP'), you.ap, you.apMax);
  document.getElementById('youLevel').textContent = you.level;
  document.getElementById('youSpeed').textContent = you.speed;
  document.getElementById('youBuff').textContent = you.buff || '-';
  document.getElementById('youDebuff').textContent = you.debuff || '-';
  setStatsTable(document.getElementById('youStats'), you.stats);
  setActions(document.getElementById('youActions'), state.you_actions || []);

  const ai = state.ai;
  fillBar(document.getElementById('aiHP'), ai.hp, ai.hpMax);
  fillBar(document.getElementById('aiAP'), ai.ap, ai.apMax);
  document.getElementById('aiLevel').textContent = ai.level;
  document.getElementById('aiSpeed').textContent = ai.speed;
  document.getElementById('aiBuff').textContent = ai.buff || '-';
  document.getElementById('aiDebuff').textContent = ai.debuff || '-';
  setStatsTable(document.getElementById('aiStats'), ai.stats);
  setActions(document.getElementById('aiActions'), state.ai_actions || []);

  const logDiv = document.getElementById('log');
  logDiv.innerText = (state.log || []).join("\n");
  logDiv.scrollTop = logDiv.scrollHeight;
}
async function refresh(){
  const s = await api('/state');
  render(s);
}
async function play(){
  const inputEl = document.getElementById('actionInput');
  const v = inputEl.value.trim();
  const n = parseInt(v, 10);
  const body = JSON.stringify({ choice: (isFinite(n) ? n : 5) });
  await api('/act', { method:'POST', headers:{'Content-Type':'application/json'}, body });
  inputEl.value = '';
  await refresh();
}
document.addEventListener('keydown', (ev) => {
  if (ev.key === 'Enter') { ev.preventDefault(); if (!document.getElementById('playBtn').disabled) play(); }
  else if (ev.key.toLowerCase() === 'r') { ev.preventDefault(); refresh(); }
});
refresh();
setInterval(refresh, 1200);
</script>
</body>
</html>
"""

class Handler(BaseHTTPRequestHandler):
    def _ok(self, body: bytes, ctype="text/html; charset=utf-8"):
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/" or self.path.startswith("/index.html"):
            return self._ok(INDEX_HTML.encode("utf-8"))
        if self.path.startswith("/state"):
            if AUTOPLAY_AI and not GAME.done and GAME.env.actor == "ai":
                GAME.ai_move()
            return self._ok(json.dumps(GAME.state_json()).encode("utf-8"),
                            "application/json; charset=utf-8")
        self.send_error(404)

    def do_POST(self):
        if self.path.startswith("/act"):
            length = int(self.headers.get("Content-Length", "0"))
            data = self.rfile.read(length)
            try:
                payload = json.loads(data.decode("utf-8"))
            except Exception:
                payload = {}
            choice = int(payload.get("choice", 5))
            idx = max(1, min(5, choice)) - 1
            GAME.step_human(idx)
            return self._ok(json.dumps({"ok": True}).encode("utf-8"),
                            "application/json; charset=utf-8")
        self.send_error(404)


def run(host="127.0.0.1", port=8777):
    httpd = HTTPServer((host, port), Handler)
    print(f"Game web UI at http://{host}:{port}/")
    httpd.serve_forever()


if __name__ == "__main__":
    model_path = os.environ.get("MODEL_CKPT", "checkpoints/best_so_far.pt")
    GAME = Game(model_path=model_path, my_level=5, ai_level=5)
    run()
