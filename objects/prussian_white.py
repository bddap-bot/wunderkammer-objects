"""One cubic cell of Prussian white, Na2Fe[Fe(CN)6], the sodium-ion cathode, charging and discharging: low-spin iron bonded to carbon and high-spin iron bonded to nitrogen on a rock-salt lattice bridged by cyanide, with a sodium ion in each of the eight cavities.

Charging pulls the sodium out through the cell's open faces, and each ion leaves an electron behind for the current collector: first the high-spin iron gives up its electron (Prussian white to Prussian blue, NaFe[Fe(CN)6]), then the low-spin iron (Prussian yellow, Fe[Fe(CN)6]). Discharge runs it backward.
Bond lengths: the DFT cubic Prussian white of Baumgart, Sotoudeh and Groß, "Rhombohedral (R-3) Prussian White as cathode material: an ab-initio study" (ChemRxiv 2023, Table 1): Fe-C 1.878 Å, C-N 1.181 Å, N-Fe 2.190 Å. The sodium-full material is really rhombohedral; this draws the cubic cell.
"""
import numpy as np

import shapes
from glb import Node

SPREADS = True
DURATION = 16.0
ANGSTROM = 0.016
FE_C = 1.878
C_N = 1.181
N_FE = 2.190
HALF = FE_C + C_N + N_FE
CELL = 2 * HALF

FE2 = (0.88, 0.4, 0.2, 1)
FE3 = (0.98, 0.82, 0.3, 1)
CARBON = (0.38, 0.38, 0.4, 1)
NITROGEN = (0.2, 0.3, 0.97, 1)
SODIUM = (0.67, 0.36, 0.95, 1)
ELECTRON = (0.35, 0.95, 1.0, 1)


def site(i: int, j: int, k: int) -> np.ndarray:
    return (np.array([i, j, k]) - 1) * HALF * ANGSTROM


def scene():
    low_spin = [(i, j, k) for i in range(3) for j in range(3) for k in range(3) if (i + j + k) % 2 == 0]
    high_spin = [(i, j, k) for i in range(3) for j in range(3) for k in range(3) if (i + j + k) % 2 == 1]
    carbons, nitrogens, bonds = [], [], []
    atom = shapes.sphere(0.3 * ANGSTROM, 4, 7)
    for i, j, k in low_spin:
        for axis in range(3):
            for step in (-1, 1):
                other = [i, j, k]
                other[axis] += step
                if not 0 <= other[axis] <= 2:
                    continue
                start, end = site(i, j, k), site(*other)
                direction = (end - start) / np.linalg.norm(end - start)
                carbons.append(shapes.translate(atom, start + direction * FE_C * ANGSTROM))
                nitrogens.append(shapes.translate(atom, start + direction * (FE_C + C_N) * ANGSTROM))
                rod = shapes.cylinder(0.11 * ANGSTROM, HALF * ANGSTROM, 6)
                m = shapes.rotation(np.cross([0, 1, 0], direction) if axis != 1 else [1, 0, 0], np.pi / 2 if axis != 1 else 0.0)
                m[:3, 3] = (start + end) / 2
                bonds.append(shapes.transform(rod, m))
    framework = Node("framework", children=[
        Node("carbon", shapes.merge(*carbons), CARBON),
        Node("nitrogen", shapes.merge(*nitrogens), NITROGEN),
        Node("cyanide_bridges", shapes.merge(*bonds), (0.72, 0.72, 0.74, 1)),
    ])

    def iron(name: str, at, radius: float) -> list[Node]:
        ball = shapes.sphere(radius * ANGSTROM, 6, 10)
        return [Node(name, ball, FE2, translation=tuple(at)), Node(f"{name}_oxidised", ball, FE3, translation=tuple(at), scale=(0, 0, 0))]

    low = Node("low_spin_iron", children=[node for n, s in enumerate(low_spin) for node in iron(f"fe_ls_{n}", site(*s), 0.55)])
    high = Node("high_spin_iron", children=[node for n, s in enumerate(high_spin) for node in iron(f"fe_hs_{n}", site(*s), 0.7)])

    quarter = HALF / 2 * ANGSTROM
    cavities = [(x, y, z) for x in (quarter, -quarter) for y in (quarter, -quarter) for z in (quarter, -quarter)]
    sodium = Node("sodium", children=[Node(f"na_{n + 1}", shapes.sphere(0.9 * ANGSTROM, 8, 12), SODIUM, translation=c) for n, c in enumerate(cavities)])
    electrons = Node("electrons", children=[Node(f"electron_{n + 1}", shapes.sphere(0.32 * ANGSTROM, 5, 8), ELECTRON, scale=(0, 0, 0)) for n in range(8)])

    edge = CELL * ANGSTROM
    collector = Node("current_collector", shapes.box(0.002, edge * 0.8, edge * 0.8, at=(-edge / 2 - 2.2 * ANGSTROM, 0, 0)), (0.85, 0.6, 0.4, 0.6), double_sided=True)
    electrolyte = Node("electrolyte", shapes.box(5.2 * ANGSTROM, edge * 1.1, edge * 1.1, at=(edge / 2 + 3.4 * ANGSTROM, 0, 0)), (0.55, 0.75, 0.95, 0.12), double_sided=True)

    view = shapes.quaternion((0.35, 1, 0.12), np.radians(28))
    roots = [Node("prussian_white", rotation=view, children=[framework, low, high, sodium, electrons, collector, electrolyte])]
    constants = {
        "QUARTER": quarter, "FACE": edge / 2, "ANGSTROM": ANGSTROM, "LOW_SPIN": len(low_spin), "HIGH_SPIN": len(high_spin),
        "PARK_X": edge / 2 + 1.9 * ANGSTROM, "PARK_STEP": 2.1 * ANGSTROM, "COLLECTOR_X": -edge / 2 - 2.0 * ANGSTROM,
    }
    return roots, DURATION, constants
