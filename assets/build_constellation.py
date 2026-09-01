"""Skill constellation — one layout, two outputs.

Every skill is an edge away from the work that proves it, so nothing on the
page is an unbacked claim. Node size is the number of projects a skill appears
in, deliberately *not* bytes of code: by volume this repo set is dominated by
Dart and Python, which would argue against the web-first framing.

Emits:
  assets/skills.svg   self-animating (SMIL), for the GitHub profile README,
                      which strips JavaScript
  index.html          layout injected as inline JSON for the live version

    python3 build_constellation.py
"""
import json
import math
import os
import re

W, H = 1060, 680
CX, CY = W / 2, H / 2 + 6
PR = (236, 180)     # project ring radii (x, y)
SR = (380, 288)     # skill ring radii

INK = "#120c26"
PAPER = "#f6f1e8"
MUTED = "#b3a2bd"
AMBER = "#f5b96a"
VERMIL = "#c42e26"
CYAN = "#98eaee"

# ── the graph ────────────────────────────────────────────────────────────────
PROJECTS = [
    ("wildid",    "WildID",          "team"),
    ("thesis",    "Bone Scaffold",   "thesis"),
    ("nielit",    "NIELIT",          "internship"),
    ("agentapi",  "Agent-Ready API", "project"),
    ("medlab",    "Medlab",          "internship"),
    ("portfolio", "This Site",       "project"),
    ("voter",     "Voter Lookup",    "project"),
    ("zsi",       "ZSI Field App",   "project"),
]

SKILLS = {
    "javascript": "JavaScript", "typescript": "TypeScript", "nodejs": "Node.js",
    "express": "Express", "htmlcss": "HTML/CSS", "python": "Python",
    "django": "Django", "flask": "Flask", "pytorch": "PyTorch",
    "sklearn": "scikit-learn", "numpy": "NumPy", "scipy": "SciPy",
    "pandas": "pandas", "flutter": "Flutter", "dart": "Dart",
}

EDGES = [
    ("wildid", s) for s in ("flutter", "dart", "pytorch", "python", "flask")
] + [
    ("thesis", s) for s in ("python", "numpy", "scipy", "sklearn", "pandas")
] + [
    ("nielit", s) for s in ("python", "django", "sklearn", "pandas")
] + [
    ("agentapi", s) for s in ("nodejs", "express", "javascript")
] + [
    ("medlab", s) for s in ("htmlcss", "javascript")
] + [
    ("portfolio", s) for s in ("javascript", "htmlcss")
] + [
    ("voter", s) for s in ("typescript", "htmlcss")
] + [
    ("zsi", s) for s in ("flutter", "dart")
]

# ── layout ───────────────────────────────────────────────────────────────────
pang = {p[0]: -math.pi / 2 + i * (2 * math.pi / len(PROJECTS))
        for i, p in enumerate(PROJECTS)}

conn = {s: [p for p, k in EDGES if k == s] for s in SKILLS}


def circ_mean(angles):
    x = sum(math.cos(a) for a in angles)
    y = sum(math.sin(a) for a in angles)
    return math.atan2(y, x)


want = {s: circ_mean([pang[p] for p in ps]) for s, ps in conn.items()}
order = sorted(SKILLS, key=lambda s: want[s] % (2 * math.pi))
n = len(order)
step = 2 * math.pi / n


def ang_diff(a, b):
    return abs((a - b + math.pi) % (2 * math.pi) - math.pi)


# evenly space the skills (guarantees no label collisions) but rotate the whole
# ring to sit as close as possible to where each skill actually wants to be
best, best_cost = 0.0, 1e9
for k in range(360):
    off = k * math.pi / 180
    cost = sum(ang_diff(off + i * step, want[s]) for i, s in enumerate(order))
    if cost < best_cost:
        best, best_cost = off, cost

sang = {s: best + i * step for i, s in enumerate(order)}

nodes = {}
for pid, label, kind in PROJECTS:
    a = pang[pid]
    nodes[pid] = {"id": pid, "label": label, "type": "project", "kind": kind,
                  "x": round(CX + PR[0] * math.cos(a), 1),
                  "y": round(CY + PR[1] * math.sin(a), 1),
                  "r": 9, "ang": a}
for sid, label in SKILLS.items():
    a = sang[sid]
    c = len(conn[sid])
    nodes[sid] = {"id": sid, "label": label, "type": "skill", "count": c,
                  "x": round(CX + SR[0] * math.cos(a), 1),
                  "y": round(CY + SR[1] * math.sin(a), 1),
                  "r": 8 + (c - 1) * 4.5, "ang": a}


def curve(a, b):
    """Quadratic path bowed toward the centre, so edges weave."""
    mx, my = (a["x"] + b["x"]) / 2, (a["y"] + b["y"]) / 2
    qx, qy = mx + (CX - mx) * 0.42, my + (CY - my) * 0.42
    return (f'M{a["x"]:.1f},{a["y"]:.1f} Q{qx:.1f},{qy:.1f} '
            f'{b["x"]:.1f},{b["y"]:.1f}')


edges = [{"p": p, "s": s, "d": curve(nodes[p], nodes[s])} for p, s in EDGES]

# ── output 1: animated SVG for the README ────────────────────────────────────
def label_anchor(node):
    ca = math.cos(node["ang"])
    r = node["r"]
    if abs(ca) < 0.30:
        return "middle", 0, (-(r + 10) if math.sin(node["ang"]) < 0 else r + 19)
    if ca > 0:
        return "start", r + 9, 4
    return "end", -(r + 9), 4


out = [
    f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
    f'viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
    f'aria-label="Skill constellation: each skill linked to the projects that use it">',
    '<defs>',
    f'<radialGradient id="bg"><stop offset="0" stop-color="#1c1140"/>'
    f'<stop offset="1" stop-color="{INK}"/></radialGradient>',
    '<filter id="glow" x="-60%" y="-60%" width="220%" height="220%">'
    '<feGaussianBlur stdDeviation="5" result="b"/>'
    '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
    '</defs>',
    f'<rect width="{W}" height="{H}" rx="18" fill="url(#bg)"/>',
]

for i, e in enumerate(edges):
    out.append(f'<path id="e{i}" d="{e["d"]}" fill="none" stroke="{PAPER}" '
               f'stroke-opacity=".13" stroke-width="1.1"/>')

# a pulse of light travels each edge, staggered so the graph reads as alive
for i, e in enumerate(edges):
    dur, delay = 3.2, (i % 10) * 0.62
    out.append(
        f'<circle r="2.6" fill="{CYAN}" opacity="0">'
        f'<animateMotion dur="{dur}s" begin="{delay:.2f}s" repeatCount="indefinite">'
        f'<mpath xlink:href="#e{i}"/></animateMotion>'
        f'<animate attributeName="opacity" values="0;.95;.95;0" keyTimes="0;.12;.85;1" '
        f'dur="{dur}s" begin="{delay:.2f}s" repeatCount="indefinite"/></circle>')

for pid, label, kind in PROJECTS:
    nd = nodes[pid]
    a, dx, dy = label_anchor(nd)
    out.append(
        f'<g><path d="M{nd["x"]},{nd["y"]-11} L{nd["x"]+11},{nd["y"]} '
        f'L{nd["x"]},{nd["y"]+11} L{nd["x"]-11},{nd["y"]} Z" fill="{AMBER}" '
        f'filter="url(#glow)"><animate attributeName="opacity" values=".75;1;.75" '
        f'dur="4.4s" begin="{hash(pid)%7*0.4:.1f}s" repeatCount="indefinite"/></path>'
        f'<text x="{nd["x"]+dx}" y="{nd["y"]+dy}" fill="{PAPER}" font-size="14.5" '
        f'font-weight="600" text-anchor="{a}" '
        f'font-family="Helvetica Neue,Helvetica,Arial,sans-serif">{label}</text></g>')

for sid, label in SKILLS.items():
    nd = nodes[sid]
    a, dx, dy = label_anchor(nd)
    out.append(
        f'<g><circle cx="{nd["x"]}" cy="{nd["y"]}" r="{nd["r"]:.1f}" fill="{VERMIL}" '
        f'stroke="{PAPER}" stroke-opacity=".55" stroke-width="1.2">'
        f'<animate attributeName="r" values="{nd["r"]:.1f};{nd["r"]+1.6:.1f};{nd["r"]:.1f}" '
        f'dur="5s" begin="{(hash(sid)%9)*0.5:.1f}s" repeatCount="indefinite"/></circle>'
        f'<text x="{nd["x"]+dx}" y="{nd["y"]+dy}" fill="{MUTED}" font-size="13" '
        f'text-anchor="{a}" font-family="Menlo,DejaVu Sans Mono,monospace">{label}</text></g>')

out.append(f'<ellipse cx="{CX}" cy="{CY}" rx="118" ry="34" fill="{INK}" opacity=".82"/>')
out.append(f'<text x="{CX}" y="{CY-8}" text-anchor="middle" fill="{PAPER}" '
           f'font-size="17" font-weight="700" opacity=".92" '
           f'font-family="Helvetica Neue,Helvetica,Arial,sans-serif">Every skill,</text>')
out.append(f'<text x="{CX}" y="{CY+14}" text-anchor="middle" fill="{AMBER}" '
           f'font-size="17" font-weight="700" opacity=".92" '
           f'font-family="Helvetica Neue,Helvetica,Arial,sans-serif">wired to the proof</text>')
out.append('</svg>')

svg = "\n".join(out)
open("skills.svg", "w", encoding="utf-8").write(svg)

# ── output 2: layout inlined into the portfolio ──────────────────────────────
payload = {
    "w": W, "h": H,
    "nodes": [{k: v for k, v in nd.items() if k != "ang"} for nd in nodes.values()],
    "edges": edges,
}
blob = json.dumps(payload, separators=(",", ":"))

idx = "../index.html"
html = open(idx, encoding="utf-8").read()
new = (f'<script type="application/json" id="graph-data">{blob}</script>')
html2, n_sub = re.subn(
    r'<script type="application/json" id="graph-data">.*?</script>',
    lambda _: new, html, count=1, flags=re.DOTALL)
if n_sub:
    open(idx, "w", encoding="utf-8").write(html2)

print(f"skills.svg  {os.path.getsize('skills.svg')/1024:.0f}KB   "
      f"nodes={len(nodes)} edges={len(edges)}   html injected={bool(n_sub)}")
print("skill fan-out:", ", ".join(
    f"{SKILLS[s]}={len(conn[s])}" for s in sorted(conn, key=lambda k: -len(conn[k]))[:5]))
