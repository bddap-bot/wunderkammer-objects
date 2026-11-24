{ pkgs ? import <nixpkgs> { }, objects ? ./objects }:
pkgs.runCommandCC "wunderkammer-objects" {
  nativeBuildInputs = [ (pkgs.python3.withPackages (p: [ p.numpy ])) pkgs.rustc pkgs.lld ];
  PYTHONDONTWRITEBYTECODE = 1;
} ''
  rustc --edition 2021 --test -A dead_code -o common-tests ${./common.rs}
  ./common-tests
  python3 ${pkgs.lib.cleanSource ./.}/make.py --objects ${objects} $out
''
