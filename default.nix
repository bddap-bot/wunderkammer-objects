{ pkgs ? import <nixpkgs> { }, objects ? ./objects }:
pkgs.runCommandCC "wunderkammer-objects" {
  nativeBuildInputs = [ (pkgs.python3.withPackages (p: [ p.numpy ])) pkgs.rustc pkgs.lld pkgs.nodejs ];
  PYTHONDONTWRITEBYTECODE = 1;
} ''
  python3 ${pkgs.lib.cleanSource ./.}/make.py --objects ${objects} $out
  ${pkgs.lib.optionalString (objects == ./objects) "node ${./feed.test.mjs} $out"}
''
