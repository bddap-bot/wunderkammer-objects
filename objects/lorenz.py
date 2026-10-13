"""The Lorenz attractor, E. N. Lorenz, "Deterministic Nonperiodic Flow", J. Atmos. Sci. 20, 130 (1963), with his σ = 10, ρ = 28, β = 8/3: two beads start a hair apart and ride the same rules until the gap between them grows to the size of the whole attractor.

Drawn with z up; one unit of the equations is 4.2 mm.
"""
import numpy as np

import shapes
from glb import Node

SCALE = 0.0042
SIGMA, RHO, BETA = 10.0, 28.0, 8.0 / 3.0
TRAIL = 20


def flow(p: np.ndarray) -> np.ndarray:
    x, y, z = p
    return np.array([SIGMA * (y - x), x * (RHO - z) - y, x * y - BETA * z])


def orbit(start, steps: int, h: float = 0.005) -> np.ndarray:
    p = np.array(start, float)
    out = []
    for _ in range(steps):
        k1 = flow(p)
        k2 = flow(p + h / 2 * k1)
        k3 = flow(p + h / 2 * k2)
        k4 = flow(p + h * k3)
        p = p + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        out.append(p)
    return np.array(out)


def drawn(p: np.ndarray) -> np.ndarray:
    return np.stack([p[..., 0], p[..., 2] - 25.0, p[..., 1]], -1) * SCALE


def scene():
    settled = orbit((1.0, 1.0, 1.0), 4000)[-1]
    path = orbit(settled, 8000)[::8]
    ghost = Node("attractor", shapes.tube(drawn(path), 0.0005, 4), (0.55, 0.6, 0.75, 0.35))
    bead = shapes.sphere(0.0042, 8, 12)
    dot = shapes.sphere(0.0022, 4, 6)
    red = Node("bead_red", bead, (1.0, 0.35, 0.25, 1), translation=tuple(drawn(settled)))
    blue = Node("bead_blue", bead, (0.3, 0.65, 1.0, 1), translation=tuple(drawn(settled)))
    trails = [Node("trail_red", children=[Node(f"trail_red_{k}", dot, (1.0, 0.5, 0.4, 1)) for k in range(TRAIL)]), Node("trail_blue", children=[Node(f"trail_blue_{k}", dot, (0.45, 0.75, 1.0, 1)) for k in range(TRAIL)])]
    gap = Node("separation", shapes.cylinder(0.0009, 1.0, 8, at=(0, 0.5, 0)), (1.0, 1.0, 1.0, 0.8), scale=(1, 0, 1))
    view = shapes.quaternion((0, 1, 0), np.radians(-15))
    roots = [Node("lorenz", rotation=view, children=[ghost, red, blue, *trails, gap])]
    constants = {"SCALE": SCALE, "SIGMA": SIGMA, "RHO": RHO, "BETA": BETA, "START_X": settled[0], "START_Y": settled[1], "START_Z": settled[2], "TRAIL_LENGTH": TRAIL}
    return roots, 0.0, constants
