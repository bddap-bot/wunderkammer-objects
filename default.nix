{ pkgs ? import <nixpkgs> { }, objects ? ./objects }:
pkgs.runCommand "wunderkammer-objects" {
  nativeBuildInputs = [ (pkgs.python3.withPackages (p: [ p.numpy ])) pkgs.rustc pkgs.lld ];
  PYTHONDONTWRITEBYTECODE = 1;
} ''
  python3 ${pkgs.lib.cleanSource ./.}/make.py --objects ${objects} $out
''
