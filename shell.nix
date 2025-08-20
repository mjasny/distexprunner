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

  # Prefer the system compiler if anything tries to compile:
  shellHook = ''
    if [ -x /usr/bin/g++ ]; then
      export CXX=/usr/bin/g++
    fi
    if [ -x /usr/bin/gcc ]; then
      export CC=/usr/bin/gcc
    fi
    export PATH=/usr/bin:/bin:/usr/sbin:/sbin:$PATH
  '';
}
