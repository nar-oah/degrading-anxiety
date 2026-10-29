{ pkgs ? import <nixpkgs> { } }:

pkgs.mkShell {
  packages = [
    pkgs.python314
    pkgs.uv
  ];

  # NumPy's PyPI wheels need the host C++ runtime on NixOS.
  LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [ pkgs.stdenv.cc.cc.lib ];
}
