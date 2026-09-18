"""Generates the key-shaped reveal path: N evenly (arc-length) spaced
points along an idealized key silhouette, drawn as ONE unbroken closed
loop (same as the rocket/star/diamond games).

The ring ("head") is a true circular arc (generated point-by-point with
sin/cos, not a hand-picked polygon) left open at the bottom — each side
of the arc flows directly into one of the two leg rails with no shared
"pinch" point and no extra neck segment. The right rail carries two
bold square-cornered teeth; the left rail is plain; a flat line closes
the bottom.

Arc-length resampling to a small point budget only draws straight
lines between whatever points survive, so two things matter: (1) a
polygon's underlying vertex count sets how curved it CAN look (more
vertices on the ring == a rounder outline), and (2) any single edge
shorter than the average gap between resampled points gets smoothed
away entirely, so square corners need generously long edges to read
as sharp right angles rather than diagonal cuts.
"""
import math, random

_RING_CX, _RING_CY, _RING_R = 0, -100, 50
_RING_GAP_DEG = 47           # total angular gap left open at the bottom
_RING_POINTS = 15           # more points here == a rounder head

def _ring_arc():
    """Points around the ring from the right-rail attachment, up and
    over the top, down to the left-rail attachment — open at the
    bottom by _RING_GAP_DEG degrees, so the two ends never touch."""
    start = 180 - _RING_GAP_DEG / 2   # lower-right end (near right rail)
    end = -180 + _RING_GAP_DEG / 2    # lower-left end (near left rail), going the long way through the top
    pts = []
    for i in range(_RING_POINTS):
        deg = start - (start - end) * i / (_RING_POINTS - 1)
        rad = math.radians(deg)
        x = _RING_CX + _RING_R * math.sin(rad)
        y = _RING_CY - _RING_R * math.cos(rad)
        pts.append((f"Ring{i}", round(x, 1), round(y, 1)))
    return pts

_ring = _ring_arc()
_ring_right_end = _ring[0]     # lower-right attachment point
_ring_left_end = _ring[-1]     # lower-left attachment point

# One single continuous outline, traversed in this order:
#   1) right rail top (flows directly out of the ring's lower-right end)
#   2) straight down the plain-ish run, through two bold square teeth
#   3) flat line across the bottom
#   4) straight up the plain left rail, flowing directly into the
#      ring's lower-left end
#   5) around the ring (open arc, through the top) back to (1)

# Straight-only leg: no intermediate "neck" point at all between the
# ring and the rails — each rail is a single dead-straight run from
# right where the ring's own last arc point sits, so there is exactly
# one (deliberately angled) segment carrying the eye from curve to
# straight line, never a soft blend that could read as more curvature.

# The rail sits at exactly the ring's own attachment x on each side —
# no separate "narrowing" offset — so the outline goes straight from
# the ring's last arc point down to the bottom with a single constant
# x per side, never a diagonal "neck" that would read as a V.
_RAIL_R = _ring_right_end[1]
_RAIL_L = _ring_left_end[1]
_LEG = [
    ("RailMidRight", _RAIL_R, 4),
    ("Tooth1Out", _RAIL_R + 32, 4),
    ("Tooth1OuterDown", _RAIL_R + 32, 29),
    ("Tooth1In", _RAIL_R, 29),
    ("GapEnd", _RAIL_R, 53),
    ("Tooth2Out", _RAIL_R + 40, 53),
    ("Tooth2OuterDown", _RAIL_R + 40, 78),
    ("BottomLeft", _RAIL_L, 78),
    ("RailMidLeft", _RAIL_L, 40),
]

# Build order: ring's lower-right end -> straight down through the two
# square teeth -> flat bottom -> straight up the plain left rail ->
# ring's lower-left end -> around the ring (open arc, through the top)
# -> back to the start (closing the loop).
_KEY = [_ring[0]] + _LEG + [_ring[-1]] + _ring[1:-1][::-1]

_FULL_LOCAL = [(x, y) for _, x, y in _KEY] + [(_KEY[0][1], _KEY[0][2])]

# scale/center into the shared 500x420 canvas frame (same viewBox as the
# rocket, star and diamond games)
_xs = [p[0] for p in _FULL_LOCAL]
_ys = [p[1] for p in _FULL_LOCAL]
_w, _h = max(_xs) - min(_xs), max(_ys) - min(_ys)
_scale = min(280 / _w, 360 / _h)
_ox = (500 - _w * _scale) / 2 - min(_xs) * _scale
_oy = (420 - _h * _scale) / 2 - min(_ys) * _scale
KEY_VERTICES = [(round(x * _scale + _ox, 1), round(y * _scale + _oy, 1)) for x, y in _FULL_LOCAL]


def _cum_lengths(pts):
    lens = [0.0]
    for i in range(len(pts) - 1):
        lens.append(lens[-1] + math.dist(pts[i], pts[i + 1]))
    return lens

def _point_at(pts, lens, target):
    for i in range(len(lens) - 1):
        if lens[i] <= target <= lens[i + 1]:
            seg = lens[i + 1] - lens[i]
            t = 0 if seg == 0 else (target - lens[i]) / seg
            x = pts[i][0] + t * (pts[i + 1][0] - pts[i][0])
            y = pts[i][1] + t * (pts[i + 1][1] - pts[i][1])
            return (round(x, 1), round(y, 1))
    return pts[-1]

def key_points(n):
    """N evenly arc-length-spaced points along the idealized key outline,
    same resampling technique used for the other three games' reveal
    shapes — works for any question count, not just the one this game
    shipped with."""
    lens = _cum_lengths(KEY_VERTICES)
    total = lens[-1]
    pts = []
    for i in range(n):
        target = total * i / (n - 1)
        pts.append(_point_at(KEY_VERTICES, lens, target))
    return pts

def wrong_points(correct_pts, seed=13, jitter=45):
    random.seed(seed)
    out = []
    cx, cy = 250, 210
    for (x, y) in correct_pts:
        dx, dy = x - cx, y - cy
        dist = math.hypot(dx, dy) or 1
        nx, ny = dx / dist, dy / dist
        ang = random.uniform(-0.9, 0.9)
        rx = nx * math.cos(ang) - ny * math.sin(ang)
        ry = nx * math.sin(ang) + ny * math.cos(ang)
        mag = random.uniform(jitter * 0.6, jitter * 1.3)
        out.append((round(x + rx * mag, 1), round(y + ry * mag, 1)))
    return out

if __name__ == "__main__":
    pts = key_points(31)
    wpts = wrong_points(pts)
    print("n:", len(pts))
    print("CORRECT:", pts)
    print("WRONG:  ", wpts)
    mind = min(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
    print("min consecutive spacing:", round(mind, 1))
