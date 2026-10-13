"""A bevel-gear differential used as an adder, the way the analogue fire-control computers of the 1940s added (US Navy OP 1140, "Basic Fire Control Mechanisms", 1944): two input shafts turn the side gears, the spider cage turns at their average, and a 2:1 gear train through an idler turns the output shaft at their sum.

Each dial reads one turn as ten units.
"""
import numpy as np

import shapes
from glb import Mesh, Node

SPREADS = True
DURATION = 12.0
APEX = 0.03
TEETH = 12
RING_TEETH = 24
PINION_TEETH = 12
RING_PITCH = 0.048
PINION_PITCH = RING_PITCH * PINION_TEETH / RING_TEETH
SHAFT_END = 0.088
IDLER_ANGLE = np.radians(-50)
OUTPUT_ANGLE = np.radians(-90)

BRASS = (0.88, 0.7, 0.32, 1)
STEEL = (0.7, 0.72, 0.76, 1)
DARK = (0.2, 0.21, 0.24, 1)


def bevel(teeth: int, phase: float) -> Mesh:
    """A bevel gear about +y whose pitch cone has its apex at the origin and a 45° half-angle, its face centred `APEX` from the apex."""
    face = 0.011
    gear = shapes.rotate(shapes.gear(APEX * 0.9, APEX * 1.07, teeth, face), (0, 1, 0), phase)
    gear = shapes.translate(gear, (0, APEX, 0))
    p = gear.positions.copy()
    p[:, [0, 2]] *= (p[:, 1] / APEX)[:, None]
    hub = shapes.cylinder(0.009, 0.014, 16, at=(0, APEX + 0.011, 0))
    return shapes.merge(faceted(Mesh(p, gear.normals, gear.indices)), hub)


def faceted(mesh: Mesh) -> Mesh:
    """Flat normals from each triangle's winding, after a taper the old normals no longer fit; the taper keeps the winding outward."""
    corners = mesh.positions[mesh.indices]
    normals = np.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0])
    normals /= np.linalg.norm(normals, axis=1, keepdims=True)
    return Mesh(corners.reshape(-1, 3), np.repeat(normals, 3, axis=0), np.arange(3 * len(corners)).reshape(-1, 3))


def spur(pitch: float, teeth: int, width: float, phase: float = 0.0) -> Mesh:
    module = 2 * pitch / teeth
    return shapes.rotate(shapes.gear(pitch - 0.9 * module, pitch + 0.7 * module, teeth, width), (0, 1, 0), phase)


def along_x(mesh: Mesh) -> Mesh:
    return shapes.rotate(mesh, (0, 0, 1), -np.pi / 2)


def dial_face(x: float) -> Mesh:
    face = along_x(shapes.cylinder(0.022, 0.0015, 32))
    ticks = []
    for k in range(10):
        length = 0.007 if k == 0 else 0.004
        tick = shapes.box(0.0026, length, 0.0012 if k else 0.002, at=(0, 0.022 - 0.0015 - length / 2, 0))
        ticks.append(shapes.rotate(tick, (1, 0, 0), 2 * np.pi * k / 10))
    return shapes.translate(shapes.merge(face, *[shapes.translate(t, (np.sign(x) * 0.0012, 0, 0)) for t in ticks], *[shapes.translate(t, (-np.sign(x) * 0.0012, 0, 0)) for t in ticks]), (x, 0, 0))


def pointer(x: float) -> Mesh:
    return shapes.merge(shapes.box(0.007, 0.016, 0.0035, at=(x, 0.009, 0)), along_x(shapes.cylinder(0.0035, 0.007, 12, at=(0, x, 0))))


def shaft(x0: float, x1: float, radius: float = 0.0035) -> Mesh:
    return along_x(shapes.cylinder(radius, abs(x1 - x0), 12, at=(0, (x0 + x1) / 2, 0)))


def scene():
    pitch = 2 * np.pi / TEETH
    side_a = shapes.rotate(bevel(TEETH, 0.0), (0, 0, 1), np.pi / 2)
    side_b = shapes.rotate(bevel(TEETH, 0.0), (0, 0, 1), -np.pi / 2)
    input_a = Node("input_a", shaft(-SHAFT_END, -APEX), STEEL, children=[
        Node("side_gear_a", side_a, BRASS),
        Node("dial_a", dial_face(-SHAFT_END), (0.93, 0.92, 0.88, 1)),
        Node("pointer_a", pointer(-SHAFT_END - 0.004), (0.95, 0.35, 0.3, 1)),
    ])
    input_b = Node("input_b", shaft(APEX, SHAFT_END), STEEL, children=[
        Node("side_gear_b", side_b, BRASS),
        Node("dial_b", dial_face(SHAFT_END), (0.93, 0.92, 0.88, 1)),
        Node("pointer_b", pointer(SHAFT_END + 0.004), (0.3, 0.6, 1.0, 1)),
    ])

    # Phases put a gap of each gear where a tooth of its mate points, at every contact.
    contact = np.arctan2(np.cos(IDLER_ANGLE), np.sin(IDLER_ANGLE))
    ring_pitch, pinion_pitch = 2 * np.pi / RING_TEETH, 2 * np.pi / PINION_TEETH
    idler_phase = contact - pinion_pitch / 2
    output_phase = np.pi - idler_phase - pinion_pitch / 2
    module = 2 * RING_PITCH / RING_TEETH
    tooth = shapes.box(0.008, 1.6 * module, 0.5 * np.pi * module, at=(0, RING_PITCH - 0.1 * module, 0))
    ring_mesh = shapes.merge(
        shapes.merge(*[shapes.rotate(tooth, (1, 0, 0), contact + ring_pitch / 2 + ring_pitch * k) for k in range(RING_TEETH)]),
        along_x(shapes.torus(RING_PITCH - 1.6 * module, 0.004, 48, 8)),
    )
    cage = shapes.merge(
        shapes.cylinder(0.003, 2 * APEX + 0.02, 10),
        along_x(shapes.torus(0.042, 0.0025, 40, 6)),
        *[shapes.box(0.004, 0.012, 0.004, at=(0, s * 0.042, 0)) for s in (-1, 1)],
    )
    carrier = Node("carrier", ring_mesh, (0.62, 0.66, 0.72, 1), children=[
        Node("spider_cage", cage, STEEL),
        Node("spider_top", bevel(TEETH, pitch / 2), (0.95, 0.82, 0.45, 1)),
        Node("spider_bottom", shapes.rotate(bevel(TEETH, pitch / 2), (1, 0, 0), np.pi), (0.95, 0.82, 0.45, 1)),
    ])

    idler_at = (0.0, (RING_PITCH + PINION_PITCH) * np.sin(IDLER_ANGLE), (RING_PITCH + PINION_PITCH) * np.cos(IDLER_ANGLE))
    out_at = (0.0, idler_at[1] + 2 * PINION_PITCH * np.sin(OUTPUT_ANGLE), idler_at[2] + 2 * PINION_PITCH * np.cos(OUTPUT_ANGLE))
    idler = Node("idler", shapes.merge(along_x(spur(PINION_PITCH, PINION_TEETH, 0.008, idler_phase)), shaft(-0.012, 0.012, 0.003)), (0.62, 0.66, 0.72, 1), translation=idler_at)
    output = Node("output", shapes.merge(along_x(spur(PINION_PITCH, PINION_TEETH, 0.008, output_phase)), shaft(-SHAFT_END, 0.01)), STEEL, translation=out_at, children=[
        Node("dial_sum", dial_face(-SHAFT_END), (0.93, 0.92, 0.88, 1)),
        Node("pointer_sum", pointer(-SHAFT_END - 0.004), (0.4, 0.9, 0.45, 1)),
    ])

    frame = Node("frame", shapes.merge(
        shapes.box(0.2, 0.004, 0.06, at=(0, out_at[1] - 0.03, out_at[2] / 2)),
        *[shapes.box(0.006, 0.03 - out_at[1], 0.012, at=(x, out_at[1] / 2 - 0.015, 0)) for x in (-0.07, 0.07)],
        shapes.box(0.006, 0.03, 0.012, at=(-0.07, out_at[1] - 0.015, out_at[2])),
    ), DARK)

    view = shapes.quaternion((0.6, 1, 0), np.radians(24))
    roots = [Node("differential", rotation=view, children=[input_a, input_b, carrier, idler, output, frame])]
    constants = {"TEETH": TEETH, "RING_RATIO": RING_TEETH / PINION_TEETH}
    return roots, DURATION, constants
