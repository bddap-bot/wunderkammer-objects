"""ATP synthase making ATP in a mitochondrial inner membrane: protons cross through the a subunit and turn a ten-subunit c-ring (yeast and E. coli carry c10), the ring turns the central stalk, and each of the three β subunits goes open, loose, tight once a turn, so one turn makes three ATP from ADP and phosphate.

Matrix side up. Dimensions are approximate, about 1 nm to 11 mm.
"""
import numpy as np

import shapes
from glb import Mesh, Node

SPREADS = True
DURATION = 9.0
NM = 0.011
C_SUBUNITS = 10
RING = 2.3 * NM
MEMBRANE = 2.0 * NM
HEAD_Y = 10.0 * NM
HEAD_RADIUS = 3.2 * NM
STATOR_X = 5.4 * NM
SITE_Y = HEAD_Y - 0.6 * NM
SITE_RADIUS = 2.0 * NM
OPEN = np.radians(30)
AMBIENT = 12

ALPHA = (0.88, 0.38, 0.38, 1)
BETA = (0.96, 0.8, 0.32, 1)
GAMMA = (0.3, 0.68, 0.98, 1)
C_RING = (0.42, 0.82, 0.5, 1)
STATOR = (0.72, 0.56, 0.92, 1)
PROTON = (1.0, 0.25, 0.45, 1)
ADENOSINE = (0.35, 0.55, 1.0, 1)
PHOSPHATE = (1.0, 0.6, 0.15, 1)


def ellipsoid(rx: float, ry: float, rz: float, at=(0, 0, 0)) -> Mesh:
    return shapes.translate(shapes.transform(shapes.sphere(1.0, 10, 16), np.diag([rx, ry, rz, 1.0])), at)


def nucleotide(phosphates: int) -> Mesh:
    """Adenosine and a chain of phosphates pointing out of the binding site."""
    beads = [shapes.sphere(0.45 * NM, 6, 10)] + [shapes.sphere(0.3 * NM, 5, 8, at=(0.55 * NM * (i + 1.4), 0, 0)) for i in range(phosphates)]
    return beads


def coloured(name: str, phosphates: int) -> Node:
    adenosine, *chain = nucleotide(phosphates)
    return Node(name, adenosine, ADENOSINE, scale=(0, 0, 0), children=[Node(f"{name}_phosphates", shapes.merge(*chain), PHOSPHATE)])


def scene():
    membrane = Node("membrane", shapes.box(0.16, 2 * MEMBRANE, 0.11), (0.92, 0.84, 0.6, 0.12), double_sided=True, children=[
        Node("matrix_heads", shapes.box(0.16, 0.003, 0.11, at=(0, MEMBRANE, 0)), (0.95, 0.75, 0.45, 0.18), double_sided=True),
        Node("intermembrane_heads", shapes.box(0.16, 0.003, 0.11, at=(0, -MEMBRANE, 0)), (0.95, 0.75, 0.45, 0.18), double_sided=True),
    ])

    subunit = shapes.merge(
        shapes.cylinder(0.55 * NM, 5.6 * NM, 10, at=(-0.55 * NM, 0, 0)),
        shapes.cylinder(0.55 * NM, 6.2 * NM, 10, at=(0.55 * NM, 0, 0)),
        shapes.sphere(0.55 * NM, 5, 10, at=(-0.55 * NM, 2.8 * NM, 0)),
        shapes.sphere(0.55 * NM, 5, 10, at=(0.55 * NM, 3.1 * NM, 0)),
    )
    site = shapes.sphere(0.32 * NM, 5, 8, at=(1.1 * NM, 0, 0))
    cs = []
    for k in range(C_SUBUNITS):
        angle = 2 * np.pi * k / C_SUBUNITS
        cs.append(Node(f"c_{k + 1}", shapes.rotate(shapes.translate(subunit, (RING, 0, 0)), (0, 1, 0), angle), C_RING, children=[
            Node(f"glutamate_{k + 1}", shapes.rotate(shapes.translate(site, (RING, 0, 0)), (0, 1, 0), angle), (0.95, 0.95, 0.9, 1)),
        ]))
    stalk_path = [(0.0, 3.3 * NM, 0.0), (0.15 * NM, 5.0 * NM, 0.0), (0.45 * NM, 7.0 * NM, 0.0), (0.5 * NM, 9.0 * NM, 0.0), (0.1 * NM, 11.6 * NM, 0.0)]
    stalk = np.array([np.array(stalk_path[i]) + (np.array(stalk_path[i + 1]) - stalk_path[i]) * s for i in range(len(stalk_path) - 1) for s in np.linspace(0, 1, 6, endpoint=i == len(stalk_path) - 2)])
    gamma = Node("gamma", shapes.merge(
        shapes.tube(stalk, 0.75 * NM, 10),
        ellipsoid(1.3 * NM, 0.55 * NM, 0.9 * NM, at=(0.9 * NM, 6.6 * NM, 0)),
    ), GAMMA, children=[
        Node("epsilon", ellipsoid(1.2 * NM, 0.7 * NM, 1.1 * NM, at=(-0.9 * NM, 3.9 * NM, 0.3 * NM)), (0.2, 0.5, 0.85, 1)),
        Node("c_ring_foot", shapes.cylinder(1.6 * NM, 0.5 * NM, 20, at=(0, 3.3 * NM, 0)), (0.25, 0.6, 0.9, 1)),
    ])
    rotor = Node("rotor", children=[Node("c_ring", children=cs), gamma])

    head = []
    lever = ellipsoid(1.25 * NM, 1.8 * NM, 1.25 * NM, at=(0, -1.6 * NM, 0))
    for k in range(3):
        a_angle = 2 * np.pi * k / 3
        b_angle = a_angle + np.pi / 3
        head.append(Node(f"alpha_{k + 1}", ellipsoid(1.45 * NM, 3.0 * NM, 1.45 * NM, at=(HEAD_RADIUS * np.cos(a_angle), HEAD_Y, -HEAD_RADIUS * np.sin(a_angle))), ALPHA))
        hinge = (HEAD_RADIUS * np.cos(b_angle), HEAD_Y - 0.6 * NM, -HEAD_RADIUS * np.sin(b_angle))
        head.append(Node(f"beta_{k + 1}", ellipsoid(1.45 * NM, 1.9 * NM, 1.45 * NM, at=(HEAD_RADIUS * np.cos(b_angle), HEAD_Y + 1.2 * NM, -HEAD_RADIUS * np.sin(b_angle))), BETA, children=[
            Node(f"beta_{k + 1}_lever", lever, (0.92, 0.7, 0.25, 1), translation=hinge),
        ]))
    ligands = []
    for k in range(3):
        ligands += [coloured(f"atp_{k + 1}", 3), coloured(f"adp_{k + 1}", 2), Node(f"phosphate_{k + 1}", shapes.sphere(0.3 * NM, 5, 8), PHOSPHATE, scale=(0, 0, 0))]
    f1 = Node("f1_head", children=[*head, Node("ligands", children=ligands)])

    oscp = ellipsoid(1.6 * NM, 0.9 * NM, 1.6 * NM, at=(0, HEAD_Y + 3.4 * NM, 0))
    peripheral = [(STATOR_X, -0.5 * NM, 0), (STATOR_X + 0.3 * NM, 4 * NM, 0), (HEAD_RADIUS + 1.6 * NM, 8 * NM, 0), (HEAD_RADIUS + 1.2 * NM, 11.5 * NM, 0), (1.0 * NM, HEAD_Y + 3.4 * NM, 0)]
    peripheral = np.array([np.array(peripheral[i]) + (np.array(peripheral[i + 1]) - peripheral[i]) * s for i in range(len(peripheral) - 1) for s in np.linspace(0, 1, 6, endpoint=i == len(peripheral) - 2)])
    rotate_out = lambda m: shapes.rotate(m, (0, 1, 0), -np.pi / 6)
    channel = lambda y0, y1, angle: shapes.tube([((RING + 1.3 * NM) * np.cos(angle), y, -(RING + 1.3 * NM) * np.sin(angle)) for y in np.linspace(y0, y1, 4)], 0.45 * NM, 8)
    delta = np.pi / C_SUBUNITS
    stator = Node("stator", children=[
        Node("a_subunit", ellipsoid(1.3 * NM, 2.4 * NM, 2.2 * NM, at=(RING + 1.9 * NM, 0, 0)), STATOR, children=[
            Node("entry_channel", channel(-3.0 * NM, 0, delta), (1.0, 0.55, 0.65, 0.5)),
            Node("exit_channel", channel(0, 3.0 * NM, -delta), (1.0, 0.55, 0.65, 0.5)),
        ]),
        Node("peripheral_stalk", rotate_out(shapes.merge(shapes.tube(peripheral, 0.6 * NM, 8), oscp)), STATOR),
    ])

    protons = [Node(f"proton_{k + 1}", shapes.sphere(0.36 * NM, 6, 8), PROTON, scale=(0, 0, 0)) for k in range(C_SUBUNITS)]
    ambient = [Node(f"ambient_proton_{k + 1}", shapes.sphere(0.3 * NM, 5, 8), PROTON) for k in range(AMBIENT)]
    roots = [Node("atp_synthase", rotation=shapes.quaternion((1, 0, 0), np.radians(12)), translation=(0, -0.05, 0), children=[
        membrane, stator, rotor, f1, Node("protons", children=[*protons, Node("intermembrane_protons", children=ambient)]),
    ])]
    constants = {
        "NM": NM, "C_SUBUNITS": C_SUBUNITS, "RING": RING, "HALF_MEMBRANE": MEMBRANE, "HEAD_Y": HEAD_Y, "HEAD_RADIUS": HEAD_RADIUS,
        "SITE_Y": SITE_Y, "SITE_RADIUS": SITE_RADIUS, "OPEN": OPEN, "AMBIENT": AMBIENT,
    }
    return roots, DURATION, constants
