"""The device's own load, htop- and nvtop-like: CPU and GPU over the last 40 seconds with their temperatures, every core with its clock, memory, and the busiest processes."""
import shapes
from glb import Node

FEED = "device"

HISTORY = 40
CORES = 8
ROWS = 5
CHARS = 8
DOT = 0.0024
LEFT, RIGHT, TOP = -0.119, 0.119, 0.092
GRAPH_HEIGHT = 0.035
GRAPH_BOTTOM = 0.036
GRAPH_WIDTH = 0.098
COLUMN = GRAPH_WIDTH / HISTORY
THERMOMETER = 0.006
CORE_BOTTOM, CORE_HEIGHT = 0.014, 0.020
CORE_WIDTH, CORE_GAP = 0.010, 0.003
MEMORY_LEFT, MEMORY_WIDTH, MEMORY_HEIGHT = 0.046, 0.073, 0.012
ROW_TOP, ROW_PITCH = 0.006, 0.021
BAR_LEFT, BAR_WIDTH, BAR_GAP, BAR_HEIGHT = 0.0, 0.0377, 0.003, 0.010
COOLEST, HOTTEST = 30.0, 100.0

BACK = (0.06, 0.065, 0.08, 1)
TRACK = (0.15, 0.16, 0.19, 1)
TEXT = (0.86, 0.89, 0.93, 1)
LABEL = (0.5, 0.53, 0.6, 1)
CPU = (0.25, 0.78, 1.0, 1)
GPU = (0.38, 0.92, 0.45, 1)
MEMORY = (0.7, 0.5, 1.0, 1)
HEAT = (1.0, 0.38, 0.25, 1)
TICK = (1.0, 1.0, 1.0, 1)

GLYPHS = {
    " ": ["     "] * 7,
    "A": [" ### ", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"],
    "B": ["#### ", "#   #", "#   #", "#### ", "#   #", "#   #", "#### "],
    "C": [" ### ", "#   #", "#    ", "#    ", "#    ", "#   #", " ### "],
    "D": ["#### ", "#   #", "#   #", "#   #", "#   #", "#   #", "#### "],
    "E": ["#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#####"],
    "F": ["#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#    "],
    "G": [" ### ", "#   #", "#    ", "# ###", "#   #", "#   #", " ####"],
    "H": ["#   #", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"],
    "I": [" ### ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", " ### "],
    "J": ["  ###", "   # ", "   # ", "   # ", "   # ", "#  # ", " ##  "],
    "K": ["#   #", "#  # ", "# #  ", "##   ", "# #  ", "#  # ", "#   #"],
    "L": ["#    ", "#    ", "#    ", "#    ", "#    ", "#    ", "#####"],
    "M": ["#   #", "## ##", "# # #", "# # #", "#   #", "#   #", "#   #"],
    "N": ["#   #", "#   #", "##  #", "# # #", "#  ##", "#   #", "#   #"],
    "O": [" ### ", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "],
    "P": ["#### ", "#   #", "#   #", "#### ", "#    ", "#    ", "#    "],
    "Q": [" ### ", "#   #", "#   #", "#   #", "# # #", "#  # ", " ## #"],
    "R": ["#### ", "#   #", "#   #", "#### ", "# #  ", "#  # ", "#   #"],
    "S": [" ####", "#    ", "#    ", " ### ", "    #", "    #", "#### "],
    "T": ["#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  "],
    "U": ["#   #", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "],
    "V": ["#   #", "#   #", "#   #", "#   #", "#   #", " # # ", "  #  "],
    "W": ["#   #", "#   #", "#   #", "# # #", "# # #", "# # #", " # # "],
    "X": ["#   #", "#   #", " # # ", "  #  ", " # # ", "#   #", "#   #"],
    "Y": ["#   #", "#   #", " # # ", "  #  ", "  #  ", "  #  ", "  #  "],
    "Z": ["#####", "    #", "   # ", "  #  ", " #   ", "#    ", "#####"],
    "0": [" ### ", "#   #", "#  ##", "# # #", "##  #", "#   #", " ### "],
    "1": ["  #  ", " ##  ", "  #  ", "  #  ", "  #  ", "  #  ", " ### "],
    "2": [" ### ", "#   #", "    #", "   # ", "  #  ", " #   ", "#####"],
    "3": ["#####", "   # ", "  #  ", "   # ", "    #", "#   #", " ### "],
    "4": ["   # ", "  ## ", " # # ", "#  # ", "#####", "   # ", "   # "],
    "5": ["#####", "#    ", "#### ", "    #", "    #", "#   #", " ### "],
    "6": ["  ## ", " #   ", "#    ", "#### ", "#   #", "#   #", " ### "],
    "7": ["#####", "    #", "   # ", "  #  ", " #   ", " #   ", " #   "],
    "8": [" ### ", "#   #", "#   #", " ### ", "#   #", "#   #", " ### "],
    "9": [" ### ", "#   #", "#   #", " ####", "    #", "   # ", " ##  "],
    "-": ["     ", "     ", "     ", "#####", "     ", "     ", "     "],
    "_": ["     ", "     ", "     ", "     ", "     ", "     ", "#####"],
    ".": ["     ", "     ", "     ", "     ", "     ", " ##  ", " ##  "],
    ":": ["     ", " ##  ", " ##  ", "     ", " ##  ", " ##  ", "     "],
    "/": ["     ", "    #", "   # ", "  #  ", " #   ", "#    ", "     "],
    "+": ["     ", "  #  ", "  #  ", "#####", "  #  ", "  #  ", "     "],
    "?": [" ### ", "#   #", "    #", "   # ", "  #  ", "     ", "  #  "],
}
CHARSET = "".join(GLYPHS)


def text(name: str, word: str, at: tuple[float, float], color) -> Node:
    """Static dot-matrix text whose lower left corner is `at`, one mesh."""
    dots = [shapes.quad(DOT, DOT, (at[0] + (c * 6 + x) * DOT, at[1] + (6 - y) * DOT, 0.001)) for c, letter in enumerate(word) for y, row in enumerate(GLYPHS[letter]) for x, bit in enumerate(row) if bit == "#"]
    return Node(name, shapes.merge(*dots), color)


def font() -> list[float]:
    """Each glyph as seven rows of five bits, the leftmost dot the highest bit, in CHARSET order."""
    return [float(sum(1 << (4 - x) for x, bit in enumerate(row) if bit == "#")) for letter in CHARSET for row in GLYPHS[letter]]


def scene():
    width = RIGHT - LEFT
    back = Node("back", shapes.box(width + 0.012, 0.196, 0.006, at=(0, 0, -0.0035)), BACK)
    dot = shapes.quad(DOT, DOT)
    column = shapes.quad(COLUMN * 0.8, 1.0)
    unit = shapes.quad(1.0, 1.0)
    tick = shapes.quad(CORE_WIDTH, 0.0012, (0, -0.0006, 0))
    hidden = (0.0, 0.0, 0.0)

    def graph(name: str, left: float, color, extra: list[Node]) -> Node:
        columns = [Node(f"{name}_column{i}", column, color, translation=(i * COLUMN, 0.0, 0.001), scale=(1.0, 0.0, 1.0)) for i in range(HISTORY)]
        track = Node(f"{name}_track", shapes.quad(GRAPH_WIDTH, GRAPH_HEIGHT), TRACK)
        tube = Node(f"{name}_tube", shapes.quad(THERMOMETER, GRAPH_HEIGHT), TRACK, translation=(GRAPH_WIDTH + 0.003, 0.0, 0.0))
        heat = Node(f"{name}_heat", unit, HEAT, translation=(GRAPH_WIDTH + 0.003, 0.0, 0.001), scale=(THERMOMETER, 0.0, 1.0))
        return Node(name, translation=(left, GRAPH_BOTTOM, 0.0), children=[track, tube, heat, *columns, *extra])

    memory_dots = [Node(f"gpu_memory{i}", shapes.quad(COLUMN * 0.8, 0.0015, (0, -0.00075, 0)), MEMORY, translation=(i * COLUMN, 0.0, 0.002), scale=hidden) for i in range(HISTORY)]
    gpu_clock = Node("gpu_clock", shapes.quad(0.003, 0.0012, (0, -0.0006, 0)), TICK, translation=(GRAPH_WIDTH - 0.003, 0.0, 0.002), scale=hidden)
    cpu = graph("cpu", LEFT, CPU, [])
    gpu = graph("gpu", 0.012, GPU, [*memory_dots, gpu_clock])

    cores = []
    for i in range(CORES):
        x = LEFT + i * (CORE_WIDTH + CORE_GAP)
        cores.append(Node(f"core{i}", shapes.quad(CORE_WIDTH, CORE_HEIGHT), TRACK, translation=(x, CORE_BOTTOM, 0.0), children=[
            Node(f"core{i}_busy", shapes.quad(CORE_WIDTH, 1.0), CPU, translation=(0.0, 0.0, 0.001), scale=(1.0, 0.0, 1.0)),
            Node(f"core{i}_clock", tick, TICK, translation=(0.0, 0.0, 0.002), scale=hidden),
        ]))
    memory_y = CORE_BOTTOM + (CORE_HEIGHT - MEMORY_HEIGHT) / 2
    memory = Node("memory", shapes.quad(MEMORY_WIDTH, MEMORY_HEIGHT), TRACK, translation=(MEMORY_LEFT, memory_y, 0.0), children=[
        Node("memory_used", unit, MEMORY, translation=(0.0, 0.0, 0.001), scale=(0.0, MEMORY_HEIGHT, 1.0)),
        Node("memory_gpu", unit, GPU, translation=(0.0, 0.0, 0.002), scale=(0.0, MEMORY_HEIGHT * 0.4, 1.0)),
    ])

    rows = []
    for r in range(ROWS):
        y = ROW_TOP - r * ROW_PITCH - 7 * DOT
        letters = [Node(f"row{r}_char{c}", translation=(LEFT + c * 6 * DOT, y, 0.001), children=[Node(f"row{r}_char{c}_dot{d}", dot, TEXT, translation=(d % 5 * DOT, (6 - d // 5) * DOT, 0.0), scale=hidden) for d in range(35)]) for c in range(CHARS)]
        bars = []
        for b, color in enumerate([CPU, MEMORY, GPU]):
            x = BAR_LEFT + b * (BAR_WIDTH + BAR_GAP)
            bars.append(Node(f"row{r}_bar{b}", shapes.quad(BAR_WIDTH, BAR_HEIGHT), TRACK, translation=(x, y + (7 * DOT - BAR_HEIGHT) / 2, 0.0), children=[Node(f"row{r}_fill{b}", unit, color, translation=(0.0, 0.0, 0.001), scale=(0.0, BAR_HEIGHT, 1.0))]))
        rows.append(Node(f"row{r}", children=[*letters, *bars]))

    labels = [
        text("cpu_label", "CPU", (LEFT, TOP - 7 * DOT), LABEL),
        text("gpu_label", "GPU", (0.012, TOP - 7 * DOT), LABEL),
        text("memory_label", "MEM", (MEMORY_LEFT - 0.046, memory_y + MEMORY_HEIGHT / 2 - 3.5 * DOT), LABEL),
    ]
    constants = {
        "HISTORY": HISTORY, "CORES": CORES, "ROWS": ROWS, "CHARS": CHARS,
        "GRAPH_HEIGHT": GRAPH_HEIGHT, "CORE_HEIGHT": CORE_HEIGHT, "MEMORY_WIDTH": MEMORY_WIDTH, "BAR_WIDTH": BAR_WIDTH, "THERMOMETER": THERMOMETER,
        "COOLEST": COOLEST, "HOTTEST": HOTTEST, "FONT": font(), "CHARSET": [ord(letter) for letter in CHARSET],
        "QUESTION": CHARSET.index("?"), "SPACE": CHARSET.index(" "),
    }
    return [back, cpu, gpu, *cores, memory, *rows, *labels], 0.0, constants
