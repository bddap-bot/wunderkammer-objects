"""A crystal's conventional cell as an object: atoms, bonds, the cell's edges and its spins, read from a CIF and a magnetic CIF.

Nodes: `cell`, `bonds`, one per element, and `spin-arrows`, whose children are `<element>-spins`; gold is up, teal down.
"""
import shlex
from pathlib import Path

import numpy as np

from glb import Mesh, Node, flatten
from shapes import cylinder, merge, rotation, sphere, transform, translate

SIZE = 0.25
COLOR = {
    "Ba": (0.0, 0.72, 0.15, 1), "Y": (0.45, 0.85, 0.9, 1), "Mn": (0.6, 0.45, 0.8, 1), "Fe": (0.88, 0.4, 0.2, 1),
    "O": (0.93, 0.12, 0.1, 1), "K": (0.56, 0.25, 0.83, 1), "V": (0.68, 0.68, 0.7, 1), "Cr": (0.35, 0.5, 0.88, 1),
    "C": (0.38, 0.38, 0.4, 1), "N": (0.2, 0.3, 0.97, 1),
}
RADIUS = {"Ba": 0.6, "Y": 0.5, "Mn": 0.5, "Fe": 0.5, "O": 0.33, "K": 0.7, "V": 0.5, "Cr": 0.5, "C": 0.28, "N": 0.28}
BONDS = {frozenset(p): d for p, d in [(("Mn", "O"), 2.4), (("Fe", "O"), 2.4), (("Cr", "C"), 2.3), (("C", "N"), 1.3), (("V", "N"), 2.3)]}
UP, DOWN = (1.0, 0.78, 0.1, 1), (0.1, 0.85, 0.8, 1)
CELL = (0.82, 0.82, 0.86, 1)
BOND = (0.72, 0.72, 0.74, 1)


def read_cif(path: Path) -> tuple[dict[str, str], list[dict[str, str]]]:
    """Its single values, and each loop as one dict per row; dotted and underscored tag spellings read alike."""
    values: dict[str, str] = {}
    loops: list[dict[str, list[str]]] = []
    tags: list[str] = []
    rows: list[list[str]] = []
    reading = False

    def close() -> None:
        if tags:
            loops.append({"tags": list(tags), "rows": list(rows)})
        tags.clear()
        rows.clear()

    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line == "loop_":
            close()
            reading = True
            continue
        if line.startswith("_"):
            tag, *rest = line.split(None, 1)
            tag = tag.replace(".", "_")
            if reading and not rows and not rest:
                tags.append(tag)
                continue
            close()
            reading = False
            if rest:
                values[tag] = rest[0].strip("'\"")
            continue
        if reading:
            rows.append(shlex.split(line))
    close()
    return values, [dict(zip(loop["tags"], row)) for loop in loops for row in loop["rows"] if len(row) == len(loop["tags"])]


def lattice(values: dict[str, str]) -> np.ndarray:
    a, b, c = (float(values[f"_cell_length_{axis}"]) for axis in "abc")
    alpha, beta, gamma = (np.radians(float(values[f"_cell_angle_{angle}"])) for angle in ("alpha", "beta", "gamma"))
    cx = c * np.cos(beta)
    cy = c * (np.cos(alpha) - np.cos(beta) * np.cos(gamma)) / np.sin(gamma)
    return np.array([[a, 0, 0], [b * np.cos(gamma), b * np.sin(gamma), 0], [cx, cy, np.sqrt(c * c - cx * cx - cy * cy)]])


def operation(text: str):
    terms = [compile(term.strip(), text, "eval") for term in text.split(",")[:3]]
    return lambda f: np.array([eval(term, {}, {"x": f[0], "y": f[1], "z": f[2]}) for term in terms]) % 1


def sites(path: Path) -> tuple[np.ndarray, list[tuple[str, np.ndarray]]]:
    """Every atom of the cell, in fractional coordinates in [0, 1), from the asymmetric unit and the symmetry operations."""
    values, rows = read_cif(path)
    operations = [operation(row[tag]) for row in rows for tag in ("_symmetry_equiv_pos_as_xyz", "_space_group_symop_operation_xyz") if tag in row] or [operation("x,y,z")]
    atoms: list[tuple[str, np.ndarray]] = []
    for row in rows:
        if "_atom_site_fract_x" not in row:
            continue
        element = row["_atom_site_type_symbol"]
        frac = np.array([float(row[f"_atom_site_fract_{axis}"]) for axis in "xyz"])
        for apply in operations:
            f = apply(frac)
            if not any(e == element and np.allclose((f - g + 0.5) % 1 - 0.5, 0, atol=1e-4) for e, g in atoms):
                atoms.append((element, f))
    return lattice(values), atoms


def spins(path: Path) -> dict[str, int]:
    """Each magnetic element's moment, +1 or -1 against the first listed; only which spins are opposite is read, not their axis."""
    _, rows = read_cif(path)
    element = {row["_atom_site_label"]: row["_atom_site_type_symbol"] for row in rows if "_atom_site_type_symbol" in row and "_atom_site_label" in row}
    moments = [(element[row["_atom_site_moment_label"]], np.array([float(row[f"_atom_site_moment_crystalaxis_{axis}"]) for axis in "xyz"])) for row in rows if "_atom_site_moment_label" in row]
    reference = moments[0][1]
    signs: dict[str, int] = {}
    for name, moment in moments:
        sign = 1 if moment @ reference > 0 else -1
        assert signs.setdefault(name, sign) == sign, f"{path}: {name} carries both spins"
    return signs


def images(cell: np.ndarray, atoms: list[tuple[str, np.ndarray]], tol: float = 1e-3) -> list[tuple[str, np.ndarray]]:
    """Every atom whose periodic image lies in the closed cell, in Cartesian angstroms."""
    out = []
    for element, frac in atoms:
        for shift in np.ndindex(2, 2, 2):
            f = frac + shift
            if np.all(f <= 1 + tol) and not any(e == element and np.allclose(f, g) for e, g in out):
                out.append((element, f))
    return [(e, f @ cell) for e, f in out]


def rod(a, b, radius, sections=10):
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    length = np.linalg.norm(d)
    mesh = cylinder(radius, length, sections)
    axis = np.cross([0, 1, 0], d / length)
    if np.linalg.norm(axis) > 1e-9:
        mesh = transform(mesh, rotation(axis, np.arccos(np.clip(d[1] / length, -1, 1))))
    elif d[1] < 0:
        mesh = transform(mesh, rotation([1, 0, 0], np.pi))
    return translate(mesh, (a + b) / 2)


def cone(base, tip, radius, sections=16):
    base, tip = np.asarray(base, float), np.asarray(tip, float)
    d = (tip - base) / np.linalg.norm(tip - base)
    u = np.cross(d, [1, 0, 0] if abs(d[0]) < 0.9 else [0, 0, 1])
    u /= np.linalg.norm(u)
    v = np.cross(d, u)
    angles = np.linspace(0, 2 * np.pi, sections, endpoint=False)
    ring = np.cos(angles)[:, None] * u + np.sin(angles)[:, None] * v
    slope = radius / np.linalg.norm(tip - base)
    side_n = ring + slope * d
    side_n /= np.linalg.norm(side_n, axis=1, keepdims=True)
    positions = np.concatenate([base + radius * ring, np.repeat(tip[None], sections, 0), base + radius * ring, base[None]])
    normals = np.concatenate([side_n, side_n, np.repeat(-d[None], sections + 1, 0)])
    faces = []
    for i in range(sections):
        j = (i + 1) % sections
        faces.append([i, j, sections + i])
        faces.append([2 * sections + j, 2 * sections + i, 3 * sections])
    faces = np.array(faces)
    p = positions
    facing = np.cross(p[faces[:, 1]] - p[faces[:, 0]], p[faces[:, 2]] - p[faces[:, 0]])
    flip = (facing * normals[faces].sum(1)).sum(1) < 0
    faces[flip] = faces[flip][:, ::-1]
    return Mesh(positions, normals, faces)


def arrow(centre, axis, sign, length, shaft=0.1, head=0.27, head_length=0.65):
    up = np.asarray(axis, float) / np.linalg.norm(axis) * sign
    tail, tip = centre - up * length / 2, centre + up * length / 2
    return merge(rod(tail, tip - up * head_length, shaft), cone(tip - up * head_length, tip, head))


def scene(structure: Path, magnetic: Path, axis, arrow_length: float) -> list[Node]:
    """`axis` is the spin axis drawn, in Cartesian crystal coordinates, chosen off every bond so no arrow hides behind one."""
    cell, atoms = sites(structure)
    atoms = images(cell, atoms)
    signs = spins(magnetic)
    centre = np.ones(3) @ cell / 2
    to_gl = lambda p: np.array([p[0], p[2], -p[1]])
    gl = lambda mesh: Mesh(np.array([to_gl(q) for q in mesh.positions - centre]), np.array([to_gl(n) for n in mesh.normals]), mesh.indices)

    nodes = []
    corners = [np.array(c) @ cell for c in np.ndindex(2, 2, 2)]
    edges = [rod(corners[i], corners[i ^ bit], 0.035, 8) for i in range(8) for bit in (1, 2, 4) if not i & bit]
    nodes.append(Node("cell", gl(merge(*edges)), CELL))

    bonds = []
    for i, (e1, p1) in enumerate(atoms):
        for e2, p2 in atoms[i + 1:]:
            cut = BONDS.get(frozenset((e1, e2)))
            if cut and np.linalg.norm(p1 - p2) < cut:
                bonds.append(rod(p1, p2, 0.11, 6))
    nodes.append(Node("bonds", gl(merge(*bonds)), BOND))

    for element in dict.fromkeys(e for e, _ in atoms):
        rings, sections = (10, 16) if RADIUS[element] >= 0.45 else (5, 8)
        balls = [sphere(RADIUS[element], rings, sections, at=p) for e, p in atoms if e == element]
        nodes.append(Node(element, gl(merge(*balls)), COLOR[element]))

    arrows = []
    for element, sign in signs.items():
        meshes = [arrow(p, axis, sign, arrow_length) for e, p in atoms if e == element]
        arrows.append(Node(f"{element}-spins", gl(merge(*meshes)), UP if sign > 0 else DOWN))
    nodes.append(Node("spin-arrows", children=arrows))

    every = np.concatenate([n.mesh.positions for n in flatten(nodes) if n.mesh is not None])
    scale = SIZE / (every.max(0) - every.min(0)).max()
    for node in flatten(nodes):
        if node.mesh is not None:
            node.mesh = Mesh(node.mesh.positions * scale, node.mesh.normals, node.mesh.indices)
    return nodes
