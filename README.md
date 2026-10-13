# wunderkammer-objects

Objects for a Wunderkammer, each a binary glTF 2 file (`.glb`) built from source: a Python scene and, for objects that move, a small Rust program compiled to WebAssembly and carried in the file under the `VOICE_program` extension. The format is specified in [voice's `vr/OBJECTS.md`](https://github.com/bddap-bot/voice/blob/main/vr/OBJECTS.md); a viewer that ignores the program shows the still scene.

```sh
nix-build            # every object into result/<name>.glb
nix-shell --run 'python3 make.py out engine orrery'   # some of them, into out/
```

| object | what it shows | program |
|---|---|---|
| `engine` | a single-cylinder four-stroke engine, cut away; scrub through one 720° cycle | yes |
| `orrery` | the Sun to Saturn on true periods and eccentric orbits; data sets the date | yes |
| `replication` | a DNA replication fork with the leading strand and Okazaki fragments | yes |
| `escapement` | a Graham deadbeat escapement beating seconds; data sets the time of day | yes |
| `tesseract` | a 4D rotation projected to 3D; data picks the planes | yes |
| `workload` | GPU dial, fan, memory, queue and running jobs from live data | yes |
| `docking` | caffeine docking into the A2A adenosine receptor, from RCSB PDB 5MZP | yes |
| `KVCrCN6` | the KV[Cr(CN)6] Prussian-blue magnet's cell with its opposed V and Cr spins | no |

## Layout

- `objects/<name>.py` defines `scene()`, returning the root nodes, the program's duration and the numbers the program shares with the geometry; `objects/<name>.rs`, if present, is the program. Inputs an object reads (`5mzp.pdb`, CIF files) sit beside it.
- `make.py` builds them: `python3 make.py [--objects DIR] OUT [name...]`. `default.nix` takes the same `objects` argument, so another directory of objects builds with this tooling.
- `glb.py` writes the file and the Rust header of node indices and rest transforms; `shapes.py` makes meshes; `common.rs` is the program prelude; `crystal.py` draws a crystal cell from a CIF and a magnetic CIF.

Built files are not committed: `nix-build` makes all of them in under a minute.

## Sources

- `objects/5mzp.pdb`: an extract of RCSB PDB entry 5MZP, CC0.
- `objects/KVCrCN6_*`: structures from [compensated-magnet-ledger](https://github.com/spicylemonade/compensated-magnet-ledger) @ 45551de, CC BY 4.0.

## License

Code is licensed under either of [Apache License, Version 2.0](LICENSE-APACHE) or [MIT license](LICENSE-MIT) at your option. Third-party data keeps the license named above.
