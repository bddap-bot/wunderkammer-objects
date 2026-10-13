"""Round trips across the Internet against the speed of light in glass: a globe with a home and up to eight far ends, each with a coloured packet racing a white pulse that moves at the fastest light in fibre could, there and back, slowed so 1 ms takes 20 ms.

Land outlines: Natural Earth 1:110m land (`ne_110m_land.geojson`), public domain.
"""
import json
from pathlib import Path

import numpy as np

import shapes
from glb import Mesh, Node

RADIUS = 0.085
TARGETS = 8
ARC_BEADS = 18
TILES = 4500
# Corning SMF-28 single-mode fibre has a group index of 1.4682 at 1550 nm: light covers 204.19 km per millisecond in it.
FIBRE_KM_PER_MS = 299792.458 / 1.4682 / 1000
EARTH_KM = 6371.0
SLOW = 0.02
COLOURS = [(1.0, 0.45, 0.3, 1), (1.0, 0.8, 0.25, 1), (0.55, 0.9, 0.35, 1), (0.3, 0.85, 0.85, 1), (0.45, 0.6, 1.0, 1), (0.75, 0.5, 1.0, 1), (1.0, 0.5, 0.8, 1), (0.85, 0.85, 0.85, 1)]


def rings() -> list[np.ndarray]:
    data = json.loads((Path(__file__).parent / "ne_110m_land.geojson").read_text())
    out = []
    for feature in data["features"]:
        geometry = feature["geometry"]
        polygons = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
        out += [np.array(ring, float) for polygon in polygons for ring in polygon]
    return out


def on_land(lon: np.ndarray, lat: np.ndarray) -> np.ndarray:
    """Even-odd ray casting in longitude and latitude, over every ring at once."""
    inside = np.zeros(len(lon), bool)
    for ring in rings():
        x0, y0 = ring[:-1, 0][None], ring[:-1, 1][None]
        x1, y1 = ring[1:, 0][None], ring[1:, 1][None]
        px, py = lon[:, None], lat[:, None]
        crosses = (y0 > py) != (y1 > py)
        with np.errstate(divide="ignore", invalid="ignore"):
            at = x0 + (py - y0) * (x1 - x0) / (y1 - y0)
        inside ^= (crosses & (px < at)).sum(1) % 2 == 1
    return inside


def unit(lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
    lat, lon = np.radians(lat), np.radians(lon)
    return np.stack([np.cos(lat) * np.sin(lon), np.sin(lat), np.cos(lat) * np.cos(lon)], -1)


def land() -> Mesh:
    """A hexagonal tile on every point of a Fibonacci lattice that falls on land."""
    k = np.arange(TILES) + 0.5
    lat = np.degrees(np.arcsin(1 - 2 * k / TILES))
    lon = (np.degrees(np.pi * (1 + 5**0.5) * k) + 180) % 360 - 180
    keep = on_land(lon, lat)
    centres = unit(lat[keep], lon[keep])
    size = RADIUS * np.sqrt(4 * np.pi / TILES) * 0.6
    positions, normals, indices = [], [], []
    for n in centres:
        side = np.cross(n, [0, 1, 0])
        side = side / np.linalg.norm(side) if np.linalg.norm(side) > 1e-6 else np.array([1.0, 0, 0])
        up = np.cross(side, n)
        base = len(positions)
        positions.append(n * RADIUS * 1.006)
        normals.append(n)
        for a in np.linspace(0, 2 * np.pi, 6, endpoint=False):
            positions.append(n * RADIUS * 1.006 + (np.cos(a) * side + np.sin(a) * up) * size)
            normals.append(n)
        indices += [[base, base + 1 + i, base + 1 + (i + 1) % 6] for i in range(6)]
    return shapes.outward(Mesh(np.array(positions), np.array(normals), np.array(indices)))


def pin() -> Mesh:
    return shapes.merge(shapes.cylinder(0.0012, 0.012, 8, at=(0, 0.006, 0)), shapes.sphere(0.0038, 6, 10, at=(0, 0.013, 0)))


def scene():
    ocean = Node("ocean", shapes.sphere(RADIUS, 24, 40), (0.08, 0.14, 0.3, 1))
    continents = Node("land", land(), (0.45, 0.78, 0.45, 1))
    home = Node("home", pin(), (1.0, 1.0, 1.0, 1), scale=(1.3, 1.3, 1.3))
    bead = shapes.sphere(0.0015, 3, 6)
    targets = []
    for t in range(TARGETS):
        colour = COLOURS[t]
        targets.append(Node(f"target_{t}", children=[
            Node(f"target_{t}_pin", pin(), colour, scale=(0, 0, 0)),
            Node(f"target_{t}_arc", children=[Node(f"target_{t}_arc_{b}", bead, colour, scale=(0, 0, 0)) for b in range(ARC_BEADS)]),
            Node(f"target_{t}_packet", shapes.sphere(0.0045, 6, 10), colour, scale=(0, 0, 0)),
            Node(f"target_{t}_light", shapes.sphere(0.0036, 6, 10), (1.0, 1.0, 1.0, 1), scale=(0, 0, 0)),
        ]))
    globe = Node("globe", children=[ocean, continents, home, Node("targets", children=targets)])
    constants = {"RADIUS": RADIUS, "TARGET_COUNT": TARGETS, "ARC_BEADS": ARC_BEADS, "FIBRE_KM_PER_MS": FIBRE_KM_PER_MS, "EARTH_KM": EARTH_KM, "SLOW": SLOW}
    return [globe], 0.0, constants
