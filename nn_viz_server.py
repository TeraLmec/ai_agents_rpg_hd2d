# nn_viz_server.py — draw weak edges as thin/faint; show all edges sent
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
    body { font-family: system-ui, Segoe UI, Roboto, sans-serif; margin: 0; background: #0b0f17; color: #E6EDF3; }
    header { padding: 10px 14px; background: #0d1117; border-bottom: 1px solid #30363d; display:flex; justify-content:space-between; align-items:center;}
    .meta { font-size: 12px; color: #8b949e; }
    #viz { width: 100vw; height: calc(100vh - 56px); }
    .node { stroke: #1f2328; stroke-width: 1px; }
    .layer-label { fill: #8b949e; font-size: 12px; text-anchor: middle; }
    .value-label { fill: #c9d1d9; font-size: 10px; text-anchor: middle; }
    a { color: #58a6ff; text-decoration: none; }
  </style>
</head>
<body>
<header>
  <div><strong>NN Live Visualization</strong> — <span class="meta">open while running <code>play.py</code></span></div>
  <div class="meta">Refresh rate: ~2 Hz</div>
</header>
<svg id="viz"></svg>

<script>
const svg = document.getElementById('viz');
let W = svg.clientWidth, H = svg.clientHeight;

function resize() { W = svg.clientWidth; H = svg.clientHeight; }
window.addEventListener('resize', resize);

function lerp(a,b,t){return a+(b-a)*t;}
function clamp(x,a,b){return Math.max(a, Math.min(b, x));}

function colorFor(v){
  // v is 0..1 normalized activation; map to blue->white->orange
  const t = clamp(v,0,1);
  const r = Math.round(lerp( 30, 255, t));
  const g = Math.round(lerp(144, 200, t));
  const b = Math.round(lerp(255,  60, t));
  return `rgb(${r},${g},${b})`;
}

function edgeColor(w){
  // w is 0..1 normalized influence; purple-ish for strong
  const t = clamp(w,0,1);
  const r = Math.round(lerp(120, 255, t));
  const g = Math.round(lerp(120, 160, t));
  const b = Math.round(lerp(180, 255, t));
  return `rgb(${r},${g},${b})`;
}

function renderFrame(frame){
  svg.innerHTML = '';
  resize();
  const layers = frame.layers || [];
  const edges = frame.edges || [];
  const L = layers.length;
  if(!L) return;

  const marginX = 90, marginY = 24;
  const colW = (W - 2*marginX) / Math.max(1, L-1);

  // compute y for each layer node index (centered vertically)
  const positions = [];
  for(let li=0; li<L; li++){
    const n = layers[li].a.length;
    const innerH = H - 2*marginY;
    const step = innerH / (n + 1);
    const xs = marginX + colW * li;
    const ys = [];
    for(let i=0;i<n;i++){ ys.push(marginY + step*(i+1)); }
    positions.push({x: xs, ys});
  }

  const NS = 'http://www.w3.org/2000/svg';

  // draw edges — ALL edges sent by play.py. Weak links are thin & faint.
  edges.forEach(edge=>{
    const sL = edge.srcLayer, dL = edge.dstLayer;
    const conns = edge.conns || [];
    conns.forEach(c=>{
      const si = c[0], di = c[1], inf = c[2]; // influence [0..1]
      const x1 = positions[sL].x, y1 = positions[sL].ys[si];
      const x2 = positions[dL].x, y2 = positions[dL].ys[di];
      const line = document.createElementNS(NS, 'line');
      line.setAttribute('x1', x1); line.setAttribute('y1', y1);
      line.setAttribute('x2', x2); line.setAttribute('y2', y2);
      line.setAttribute('stroke', edgeColor(inf));
      // **thin + faint for weak edges**
      const width = 0.15 + 3.0 * inf;                // hairline up to 3.15px
      const alpha = 0.20 + 0.75 * inf;               // 0.2 .. 0.95
      line.setAttribute('stroke-width', String(width));
      line.setAttribute('stroke-opacity', String(alpha));
      svg.appendChild(line);
    });
  });

  // draw nodes
  layers.forEach((layer, li)=>{
    const {x, ys} = positions[li];
    const a = layer.a;
    const name = layer.name || `L${li}`;
    // label
    const label = document.createElementNS(NS, 'text');
    label.textContent = name;
    label.setAttribute('x', x);
    label.setAttribute('y', 16);
    label.setAttribute('class', 'layer-label');
    svg.appendChild(label);

    // nodes
    const n = a.length;
    for(let i=0;i<n;i++){
      const v = a[i];  // already normalized 0..1
      const r = 4 + 9 * v;
      const c = colorFor(v);
      const circ = document.createElementNS(NS, 'circle');
      circ.setAttribute('cx', x);
      circ.setAttribute('cy', ys[i]);
      circ.setAttribute('r', String(r));
      circ.setAttribute('fill', c);
      circ.setAttribute('class', 'node');
      svg.appendChild(circ);

      if (li === L-1) {
        // output labels (probabilities)
        const t = document.createElementNS(NS, 'text');
        t.textContent = (layer.labels && layer.labels[i]) ? `${layer.labels[i]} ${(layer.a_raw && layer.a_raw[i] !== undefined ? layer.a_raw[i].toFixed(3) : '')}` : (layer.a_raw ? layer.a_raw[i].toFixed(3) : v.toFixed(2));
        t.setAttribute('x', x + 24);
        t.setAttribute('y', ys[i] + 4);
        t.setAttribute('class', 'value-label');
        svg.appendChild(t);
      } else if (li === 0) {
        // input raw value label
        if (layer.a_raw){
          const t = document.createElementNS(NS, 'text');
          t.textContent = layer.a_raw[i].toFixed(2);
          t.setAttribute('x', x - 24);
          t.setAttribute('y', ys[i] + 4);
          t.setAttribute('class', 'value-label');
          svg.appendChild(t);
        }
      }
    }
  });

  // meta header
  const picked = (frame.meta && frame.meta.picked !== undefined) ? frame.meta.picked : null;
  if (picked !== null) {
    const hdr = document.createElementNS(NS, 'text');
    hdr.textContent = `Picked action: ${picked+1}`;
    hdr.setAttribute('x', W - 160);
    hdr.setAttribute('y', 32);
    hdr.setAttribute('class', 'layer-label');
    svg.appendChild(hdr);
  }
}

async function poll(){
  const res = await fetch('/latest', {cache:'no-cache'});
  if (res.ok) {
    const data = await res.json();
    renderFrame(data);
  }
}

setInterval(poll, 500); // ~2 Hz
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
    httpd = HTTPServer((host, port), Handler)
    print(f"NN viz server running at http://{host}:{port}/")
    httpd.serve_forever()

if __name__ == "__main__":
    run()
