"""A two-spool high-bypass turbofan laid out like the CFM56-7B (EASA TCDS E.004): one fan stage, 3-stage booster and 4-stage low-pressure turbine on one shaft, 9-stage compressor and 1-stage high-pressure turbine on the other, an annular combustor between."""
import numpy as np

import shapes
from glb import Mesh, Node

SPREADS = True
DURATION = 12.0
# The certified maximum speeds are 5382 rpm (N1) and 15183 rpm (N2), 2.82 to 1; 6 and 17 turns a loop is 2.83 to 1 and closes the loop.
LP_TURNS = 6
HP_TURNS = 17
BYPASS_BEADS = 20
CORE_BEADS = 4
BYPASS_LAPS = 3
CORE_LAPS = 2

INLET = -0.118
FAN_X = -0.100
FAN_TIP = 0.058
FAN_HUB = 0.018
NACELLE = 0.061
NACELLE_END = -0.004
SPLITTER = -0.086
EXIT = 0.118

LPC = [(-0.079, 0.021, 0.033), (-0.071, 0.021, 0.032), (-0.063, 0.021, 0.031)]
HPC = [(-0.052 + 0.006 * i, 0.0155 + 0.0004 * i, 0.0285 - 0.0006 * i) for i in range(9)]
HPT = [(0.037, 0.0205, 0.0285)]
LPT = [(0.048 + 0.0095 * i, 0.021, 0.029 + 0.0016 * i) for i in range(4)]
COMBUSTOR = (0.004, 0.031)

HOT = (0.85, 0.55, 0.35, 1)
STATOR = (0.45, 0.48, 0.55, 1)


def along_x(mesh: Mesh) -> Mesh:
    return shapes.rotate(mesh, (0, 0, 1), -np.pi / 2)


def sleeve(radius: float, low: float, high: float, sections: int = 40) -> Mesh:
    walls = along_x(shapes.cylinder(radius, high - low, sections, at=(0, (high + low) / 2, 0)))
    return Mesh(walls.positions, walls.normals, walls.indices[: 2 * sections])


def duct(profile: list[tuple[float, float]], sections: int = 40) -> Mesh:
    """A surface of revolution about x through (x, radius) points, open at both ends."""
    a = np.linspace(0, 2 * np.pi, sections + 1)
    xs = np.array([p[0] for p in profile])
    rs = np.array([p[1] for p in profile])
    slope = np.gradient(rs, xs)
    positions, normals, indices = [], [], []
    for i, (x, r) in enumerate(profile):
        n = np.array([-slope[i], 1.0])
        n /= np.linalg.norm(n)
        for t in a:
            positions.append([x, r * np.cos(t), r * np.sin(t)])
            normals.append([n[0], n[1] * np.cos(t), n[1] * np.sin(t)])
    for i in range(len(profile) - 1):
        for j in range(sections):
            p, q = i * (sections + 1) + j, (i + 1) * (sections + 1) + j
            indices += [[p, q, q + 1], [p, q + 1, p + 1]]
    return shapes.outward(Mesh(np.array(positions), np.array(normals), np.array(indices)))


def row(count: int, x: float, hub: float, tip: float, chord: float, twist: float, phase: float = 0.0) -> Mesh:
    """Flat blades, drawn double-sided by their nodes."""
    plate = Mesh(np.array([[-chord / 2, -(tip - hub) / 2, 0], [chord / 2, -(tip - hub) / 2, 0], [chord / 2, (tip - hub) / 2, 0], [-chord / 2, (tip - hub) / 2, 0]]), np.array([[0, 0, 1.0]] * 4), np.array([[0, 1, 2], [0, 2, 3]]))
    blades = []
    for i in range(count):
        blade = shapes.rotate(plate, (0, 1, 0), twist)
        blade = shapes.translate(blade, (x, (hub + tip) / 2, 0))
        blades.append(shapes.rotate(blade, (1, 0, 0), 2 * np.pi * i / count + phase))
    return shapes.merge(*blades)


def fan_blades(count: int = 24) -> Mesh:
    """Wide-chord blades, twisted from steep at the root to flat at the tip."""
    spans = np.linspace(FAN_HUB, FAN_TIP, 8)
    blades = []
    for i in range(count):
        positions, normals, indices = [], [], []
        for s, r in enumerate(spans):
            pitch = np.radians(62 - 32 * s / (len(spans) - 1))
            chord = 0.018 + 0.006 * s / (len(spans) - 1)
            along = np.array([np.cos(pitch), 0.0, np.sin(pitch)]) * chord / 2
            centre = np.array([FAN_X, r, 0.0])
            normal = np.array([-np.sin(pitch), 0.0, np.cos(pitch)])
            for end in (-1, 1):
                positions.append(centre + end * along)
                normals.append(normal)
            if s:
                b = 2 * s
                indices += [[b - 2, b - 1, b + 1], [b - 2, b + 1, b]]
        mesh = shapes.outward(Mesh(np.array(positions), np.array(normals), np.array(indices)))
        blades.append(shapes.rotate(mesh, (1, 0, 0), 2 * np.pi * i / count))
    return shapes.merge(*blades)


def rotor(stages, count: int, twist: float, chord: float) -> Mesh:
    return shapes.merge(*[shapes.merge(row(count, x, hub, tip, chord, twist), disc(x, hub)) for x, hub, tip in stages])


def disc(x: float, hub: float) -> Mesh:
    return along_x(shapes.cylinder(hub, 0.004, 20, at=(0, x, 0)))


def stators(stages, count: int, twist: float, chord: float, offset: float) -> Mesh:
    return shapes.merge(*[row(count, x + offset, hub, tip, chord, twist, phase=0.1) for x, hub, tip in stages])


def scene():
    spinner = shapes.transform(shapes.sphere(FAN_HUB, 10, 20), np.diag([1.4, 1.0, 1.0, 1.0]))
    fan = Node("fan", shapes.merge(fan_blades(), shapes.translate(spinner, (FAN_X - 0.004, 0, 0)), along_x(shapes.cylinder(FAN_HUB, 0.016, 24, at=(0, FAN_X + 0.004, 0)))), (0.6, 0.65, 0.74, 1), double_sided=True)
    lp_compressor = Node("lp_compressor", rotor(LPC, 28, np.radians(40), 0.0045), (0.62, 0.7, 0.8, 1), double_sided=True)
    lp_turbine = Node("lp_turbine", rotor(LPT, 34, np.radians(-40), 0.004), HOT, double_sided=True)
    lp_shaft = Node("lp_shaft", along_x(shapes.cylinder(0.0045, LPT[-1][0] - FAN_X, 12, at=(0, (LPT[-1][0] + FAN_X) / 2, 0))), (0.35, 0.65, 0.95, 1))
    lp_spool = Node("lp_spool", children=[fan, lp_compressor, lp_turbine, lp_shaft])

    hp_compressor = Node("hp_compressor", rotor(HPC, 26, np.radians(45), 0.0024), (0.8, 0.82, 0.86, 1), double_sided=True)
    hp_turbine = Node("hp_turbine", rotor(HPT, 46, np.radians(-45), 0.004), (0.95, 0.6, 0.3, 1), double_sided=True)
    hp_shaft = Node("hp_shaft", sleeve(0.0085, HPC[-1][0], HPT[0][0]), (0.95, 0.75, 0.3, 1))
    hp_spool = Node("hp_spool", children=[hp_compressor, hp_turbine, hp_shaft])

    core_profile = [(SPLITTER, 0.034), (LPC[0][0], 0.0345), (LPC[-1][0] + 0.004, 0.0325), (HPC[0][0] - 0.004, 0.0300), (HPC[-1][0] + 0.003, 0.0245), (COMBUSTOR[0], 0.031), (COMBUSTOR[1], 0.032), (HPT[0][0], 0.0300), (LPT[-1][0] + 0.004, 0.0365), (EXIT, 0.031)]
    core_casing = Node("core_casing", duct(core_profile), (0.6, 0.66, 0.74, 0.16), double_sided=True)
    plug = Node("exhaust_cone", duct([(LPT[-1][0] + 0.004, 0.021), (0.09, 0.019), (0.105, 0.013), (EXIT, 0.004)], 24), (0.5, 0.45, 0.42, 1))
    liner = duct([(COMBUSTOR[0], 0.020), (COMBUSTOR[0] + 0.005, 0.0185), (COMBUSTOR[1] - 0.004, 0.0185), (COMBUSTOR[1], 0.020)], 32)
    outer_liner = duct([(COMBUSTOR[0], 0.027), (COMBUSTOR[0] + 0.005, 0.0295), (COMBUSTOR[1] - 0.004, 0.0295), (COMBUSTOR[1], 0.027)], 32)
    flame = shapes.torus(1.0, 0.18, 32, 8)
    combustor = Node("combustor", shapes.merge(liner, outer_liner), (0.85, 0.62, 0.45, 0.45), double_sided=True, children=[
        Node("flame", along_x(flame), (1.0, 0.55, 0.12, 0.85), translation=((COMBUSTOR[0] + COMBUSTOR[1]) / 2, 0, 0), scale=(0.024, 0.024, 0.024)),
        Node("fuel_nozzles", shapes.merge(*[shapes.rotate(shapes.translate(along_x(shapes.cylinder(0.0012, 0.006, 6)), (COMBUSTOR[0] + 0.002, 0.024, 0)), (1, 0, 0), 2 * np.pi * k / 20) for k in range(20)]), (0.3, 0.3, 0.32, 1)),
    ])
    vanes = Node("stators", shapes.merge(
        stators(LPC, 32, np.radians(-30), 0.003, 0.004),
        stators(HPC, 28, np.radians(-35), 0.0018, 0.003),
        stators(HPT, 36, np.radians(30), 0.003, -0.0045),
        stators(LPT, 44, np.radians(30), 0.003, -0.0048),
        row(44, FAN_X + 0.03, 0.035, NACELLE, 0.008, np.radians(-15)),
    ), STATOR, double_sided=True)
    core = Node("core", children=[core_casing, vanes, combustor, plug])

    nacelle = Node("nacelle", duct([(INLET, 0.066), (INLET + 0.006, 0.0625), (FAN_X, NACELLE), (NACELLE_END - 0.02, NACELLE), (NACELLE_END, 0.056)], 48), (0.75, 0.8, 0.88, 0.14), double_sided=True)

    bead = shapes.sphere(0.0024, 6, 8)
    bypass = [Node(f"bypass_air_{k}", bead, (0.45, 0.75, 1.0, 1), scale=(0, 0, 0)) for k in range(BYPASS_BEADS)]
    core_cold = [Node(f"core_air_{k}", bead, (0.45, 0.75, 1.0, 1), scale=(0, 0, 0)) for k in range(CORE_BEADS)]
    core_hot = [Node(f"core_gas_{k}", bead, (1.0, 0.45, 0.15, 1), scale=(0, 0, 0)) for k in range(CORE_BEADS)]
    flow = Node("flow", children=[Node("bypass_air", children=bypass), Node("core_air", children=core_cold), Node("core_gas", children=core_hot)])

    view = shapes.quaternion((0, 1, 0), np.radians(-12))
    roots = [Node("turbofan", rotation=view, children=[nacelle, core, lp_spool, hp_spool, flow])]
    middle = lambda stages: sum((hub + tip) / 2 for _, hub, tip in stages) / len(stages)
    constants = {
        "LP_TURNS": LP_TURNS, "HP_TURNS": HP_TURNS, "BYPASS_BEADS": BYPASS_BEADS, "CORE_BEADS": CORE_BEADS, "BYPASS_LAPS": BYPASS_LAPS, "CORE_LAPS": CORE_LAPS,
        "INLET": INLET - 0.01, "EXIT": EXIT + 0.01, "BYPASS_END": NACELLE_END + 0.03, "BYPASS_INNER": 0.038, "BYPASS_OUTER": 0.055,
        "SPLITTER": SPLITTER, "BURN": COMBUSTOR[0] + 0.008, "R_LPC": middle(LPC), "R_HPC_IN": (HPC[0][1] + HPC[0][2]) / 2, "R_HPC_OUT": (HPC[-1][1] + HPC[-1][2]) / 2,
        "R_BURN": 0.024, "R_LPT": middle(LPT), "HPC_IN": HPC[0][0], "HPC_OUT": HPC[-1][0], "LPT_OUT": LPT[-1][0],
    }
    return roots, DURATION, constants
