let
  pkgs = import <nixpkgs> {};
  distexprunner = pkgs.python3Packages.buildPythonPackage {
    name = "distexprunner";
    src = ./.;
    format = "pyproject";
    propagatedBuildInputs = with pkgs.python3Packages; [ setuptools ];
  };
in
pkgs.mkShell {
  packages = [
    (pkgs.python3.withPackages (python-pkgs: [
      python-pkgs.numpy
      python-pkgs.psutil
      distexprunner
    ]))
  ];
}
