"""Builds every object in OBJECTS (default `objects/`), or those named, into OUT: `python3 make.py [--objects OBJECTS] OUT [name...]`.

Each object is `<name>.py`, whose `scene()` returns its root nodes, its program's duration and the numbers the program shares with the geometry, and which sets `SPREADS = True` if its parts pull apart and `FEED = "device"` if its program reads the host's device feed, beside an optional `<name>.rs` program.
The program is compiled as one no_std crate: the scene's generated constants as `mod scene`, then `common.rs`, then the object's own source.
"""
import argparse
import importlib.util
import os
import subprocess
import tempfile
from pathlib import Path

import glb

HERE = Path(__file__).resolve().parent
PRELUDE = "#![no_std]\n#[panic_handler]\nfn panic(_: &core::panic::PanicInfo) -> ! {\n    loop {}\n}\n"


def program(source: Path, header: str, scratch: Path) -> bytes:
    crate = scratch / source.name
    crate.write_text(PRELUDE + "#[allow(dead_code)]\nmod scene {\n" + header + "}\n" + (HERE / "common.rs").read_text() + source.read_text())
    wasm = scratch / f"{source.stem}.wasm"
    subprocess.run(["rustc", "--edition", "2021", "--target", "wasm32-unknown-unknown", "--crate-type", "cdylib", "-O", "-C", "panic=abort", "-D", "warnings", "-o", str(wasm), str(crate)], check=True)
    return wasm.read_bytes()


def make(objects: Path, name: str, out: Path) -> Path:
    spec = importlib.util.spec_from_file_location(name, objects / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    roots, duration, constants = module.scene()
    wasm = None
    if (objects / f"{name}.rs").exists():
        with tempfile.TemporaryDirectory() as scratch:
            wasm = program(objects / f"{name}.rs", glb.rust_header(roots, duration, constants), Path(scratch))
    path = out / f"{name}.glb"
    path.write_bytes(glb.build(roots, wasm, duration, getattr(module, "SPREADS", False), getattr(module, "FEED", None)))
    return path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--objects", type=Path, default=HERE / "objects")
    parser.add_argument("out", type=Path)
    parser.add_argument("names", nargs="*")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    for name in args.names or sorted(path.stem for path in args.objects.glob("*.py")):
        path = make(args.objects, name, args.out)
        print(f"{path}: {os.path.getsize(path)} bytes")


if __name__ == "__main__":
    main()
