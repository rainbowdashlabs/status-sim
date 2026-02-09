{ pkgs ? import <nixpkgs> {}, ... }:

pkgs.mkShell {
  packages = with pkgs; [python314 python314Packages.setuptools];
}
