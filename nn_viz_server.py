# nn_viz_server.py — NN viz with slider-controlled edge threshold + Apply button
from __future__ import annotations
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

LATEST = {"layers": [], "edges": [], "meta": {}}
LOCK = threading.Lock()

INDEX_HTML = r"""<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>NN Live Viz</title>
  <style>
    :root{
      --bg:#0b0f17; --panel:#0d1117; --bdr:#30363d; --ink:#e6edf3; --dim:#8b949e;
    }
    *{box-sizing:border-box}
    body { margin:0; font:14px/1.5 system-ui,Segoe UI,Roboto,Arial,sans-serif; background:var(--bg); color:var(--ink); }
    header { padding: 10px 14px; background: var(--panel); border-bottom: 1px solid var(--bdr);
             display:flex; gap:16px; align-items:center; justify-content:space-between; position:sticky; top:0; z-index:2; }
    .left { display:flex; gap:14px; align-items:center; }
    .title { font-weight:700; }
    .meta { color: var(--dim); font-size:12px; }
    .controls { display:flex; gap:10px; align-items:center; }
    .slider-wrap { display:flex; gap:10px; align-items:center; color:var(--ink); }
    input[type="range"]{ width:220px; }
    button { background:#1f6feb; color:white; border:1px solid #1f6feb; border-radius:8px; padding:6px 10px; cursor:pointer; }
    button:hover { filter:brightness(1.05); }
    #viz { width: 100vw; height: calc(100vh - 58px); display:block; }
    .node { stroke: #1f2328; stroke-width: 1px; }
    .layer-label { fill: var(--dim); font-size: 12px; text-anchor: middle; }
    .value-label { fill: #c9d1d9; font-size: 10px; text-anchor: start; }
    a { color: #58a6ff; text-decoration: none; }
  </style>
</head>
<body>
<header>
  <div class="left">
    <div class="title">NN Live Visualization</div>
    <div class="meta">Open while running <code>play.py</code></div>
  </div>
  <div class="controls">
    <div class="slider-wrap">
      <span class="meta">Edge threshold:</span>
      <input id="thSlider" type="range" min="0" max="100" step="1" value="5" />
      <span id="thLabel">5%</span>
      <button id="applyBtn">Apply</button>
    </div>
    <div class="meta" id="status">refresh ~2Hz</div>
  </div>
</header>
<svg id="viz"></svg>

<script>
const svg = document.getElementById('viz');
let W = svg.clientWidth, H = svg.clientHeight;

function resize(){ W = svg.clientWidth; H = svg.clientHeight; }
window.addEventListener('resize', resize);

// ---- UI state ----
const thSlider = document.getElementById('thSlider');
const thLabel  = document.getElementById('thLabel');
const applyBtn = document.getElementById('applyBtn');
let EDGE_THRESHOLD = Number(thSlider.value)/100;  // 0..1
let PENDING_APPLY = false;

thSlider.addEventListener('input', () => {
  thLabel.textContent = `${thSlider.value}%`;
});

applyBtn.addEventListener('click', () => {
  EDGE_THRESHOLD = Number(thSlider.value)/100;
  PENDING_APPLY = true;   // force re-render on next poll even if frame unchanged
  document.getElementById('status').textContent = `threshold set to ${thSlider.value}%`;
});

// ---- helpers ----
function lerp(a,b,t){return a+(b-a)*t;}
function clamp(x,a,b){return Math.max(a, Math.min(b, x));}

function nodeColor(v){
  // v in [0,1]: blue -> white -> orange
  const t = clamp(v,0,1);
  const r = Math.round(lerp( 30, 255, t));
  const g = Math.round(lerp(144, 200, t));
  const b = Math.round(lerp(255,  60, t));
  return `rgb(${r},${g},${b})`;
}
function edgeColor(w){
  // w in [0,1]: violet-ish intensity
  const t = clamp(w,0,1);
  const r = Math.round(lerp(120, 255, t));
  const g = Math.round(lerp(120, 160, t));
  const b = Math.round(lerp(180, 255, t));
  return `rgb(${r},${g},${b})`;
}

let LAST_JSON = null;

function renderFrame(frame){
  svg.innerHTML = '';
  resize();
  const layers = frame.layers || [];
  const edges  = frame.edges  || [];
  const L = layers.length;
  if(!L){ return; }

  const marginX = 90, marginY = 24;
  const colW = (W - 2*marginX) / Math.max(1, L-1);

  // centered vertical positions per layer
  const positions = [];
  for(let li=0; li<L; li++){
    const n = (layers[li].a || []).length;
    const innerH = H - 2*marginY;
    const step = innerH / (n + 1);
    const xs = marginX + colW * li;
    const ys = [];
    for(let i=0;i<n;i++) ys.push(marginY + step*(i+1));
    positions.push({x: xs, ys});
  }

  const NS = 'http://www.w3.org/2000/svg';

  // ---- Edges (respect slider threshold) ----
  const thr = EDGE_THRESHOLD;  // 0..1
  edges.forEach(edge=>{
    const sL = edge.srcLayer, dL = edge.dstLayer;
    const conns = edge.conns || [];
    for (let k=0; k<conns.length; k++){
      const [si, di, inf] = conns[k];   // influence in [0,1]
      if (inf < thr) continue;          // filter by UI threshold
      const x1 = positions[sL].x, y1 = positions[sL].ys[si];
      const x2 = positions[dL].x, y2 = positions[dL].ys[di];
      const line = document.createElementNS(NS, 'line');
      line.setAttribute('x1', x1); line.setAttribute('y1', y1);
      line.setAttribute('x2', x2); line.setAttribute('y2', y2);
      line.setAttribute('stroke', edgeColor(inf));
      // thin + faint for weak edges (still visible after threshold)
      const width = 0.15 + 3.0 * inf;          // 0.15px .. 3.15px
      const alpha = 0.20 + 0.75 * inf;         // 0.20 .. 0.95
      line.setAttribute('stroke-width', String(width));
      line.setAttribute('stroke-opacity', String(alpha));
      svg.appendChild(line);
    }
  });

  // ---- Nodes + labels ----
  layers.forEach((layer, li)=>{
    const {x, ys} = positions[li];
    const a = layer.a || [];
    const name = layer.name || `L${li}`;

    const label = document.createElementNS(NS, 'text');
    label.textContent = name;
    label.setAttribute('x', x);
    label.setAttribute('y', 16);
    label.setAttribute('class', 'layer-label');
    svg.appendChild(label);

    for(let i=0;i<a.length;i++){
      const v = a[i];
      const r = 4 + 9 * v;
      const c = nodeColor(v);
      const circ = document.createElementNS(NS, 'circle');
      circ.setAttribute('cx', x);
      circ.setAttribute('cy', ys[i]);
      circ.setAttribute('r', String(r));
      circ.setAttribute('fill', c);
      circ.setAttribute('class', 'node');
      svg.appendChild(circ);

      // output probs / input raw values
      if (li === L-1) {
        const t = document.createElementNS(NS, 'text');
        const raw = (layer.a_raw && layer.a_raw[i]!=null) ? layer.a_raw[i].toFixed(3) : '';
        const lab = (layer.labels && layer.labels[i]) ? layer.labels[i] : String(i+1);
        t.textContent = `${lab} ${raw}`;
        t.setAttribute('x', x + 24);
        t.setAttribute('y', ys[i] + 4);
        t.setAttribute('class', 'value-label');
        svg.appendChild(t);
      } else if (li === 0 && layer.a_raw){
        const t = document.createElementNS(NS, 'text');
        t.textContent = layer.a_raw[i].toFixed(2);
        t.setAttribute('x', x - 36);
        t.setAttribute('y', ys[i] + 4);
        t.setAttribute('class', 'value-label');
        svg.appendChild(t);
      }
    }
  });

  // picked output marker
  const picked = (frame.meta && frame.meta.picked !== undefined) ? frame.meta.picked : null;
  if (picked !== null && layers.length){
    const outPos = positions[layers.length-1];
    const px = outPos.x, py = outPos.ys[picked];
    if (py != null){
      const ring = document.createElementNS(NS, 'circle');
      ring.setAttribute('cx', px); ring.setAttribute('cy', py);
      ring.setAttribute('r', '14');
      ring.setAttribute('fill', 'none');
      ring.setAttribute('stroke', '#22c55e');
      ring.setAttribute('stroke-width', '2.5');
      svg.appendChild(ring);
    }
  }
}

async function poll(){
  try{
    const res = await fetch('/latest', {cache:'no-cache'});
    if(!res.ok) return;
    const data = await res.json();

    // Only re-render when:
    // 1) new frame content differs, or 2) user clicked "Apply"
    const sNew = JSON.stringify(data);
    if (PENDING_APPLY || sNew !== LAST_JSON){
      LAST_JSON = sNew;
      PENDING_APPLY = false;
      renderFrame(data);
    }
  }catch(e){}
}
setInterval(poll, 500); // ~2Hz
poll();
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
        if self.path.startswith("/latest"):
            with LOCK:
                data = json.dumps(LATEST).encode("utf-8")
            return self._ok(data, "application/json; charset=utf-8")
        self.send_error(404)

    def do_POST(self):
        if self.path.startswith("/push"):
            length = int(self.headers.get("Content-Length", "0"))
            payload = self.rfile.read(length)
            try:
                frame = json.loads(payload.decode("utf-8"))
                with LOCK:
                    global LATEST
                    LATEST = frame
                return self._ok(b"ok", "text/plain; charset=utf-8")
            except Exception as e:
                self.send_error(400, f"bad json: {e}")
                return
        self.send_error(404)

def run(host="127.0.0.1", port=8765):
    from http.server import HTTPServer
    httpd = HTTPServer((host, port), Handler)
    print(f"NN viz server running at http://{host}:{port}/  (POST frames to /push)")
    httpd.serve_forever()

if __name__ == "__main__":
    run()
