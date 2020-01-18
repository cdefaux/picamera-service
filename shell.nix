{ pin         ? true
, compiler    ? "default"
, doBenchmark ? false
, withHoogle  ? true }:
let
  # pinFile contains a nix expression that evalatues to a
  # string representing the commit hash.
  pinFile = ./nixpkgs-pinned.nix; 
  pinCommit = import pinFile;
  pinOK = pin && (builtins.pathExists pinFile);
  #TODO use a local git repo instead to speed things up.
  pinnedPkgs = fetchGit {
                 name = "nixpkgs-pinned-" + (builtins.substring 0 10 pinCommit);
                 url = https://github.com/nixos/nixpkgs/;
                 rev = pinCommit;
                 };

  pkgs = import (if pinOK
                    then pinnedPkgs
                    else <nixpkgs>
                    ) {
                        config.allowUnfree = true;
                        config.allowBroken = true;
                        };

  pinMessage = if pinOK
               then "pinned git hash:  ${pinnedPkgs.rev}"
               else "To pin, add commit string to \n ${builtins.toString pinFile}";

  python = pkgs.python37;
  pythonPackages = python.pkgs;
  
in with pkgs; 
  mkShell {
  inputsFrom = [];
  buildInputs = [
    cmake
    feh # image viewer
    ffmpeg-full
    git
    git-lfs
    graphviz
    pandoc
    lsb-release
    mplayer
    readline
    vlc
    pythonPackages.virtualenv
    pythonPackages.pip
    pythonPackages.setuptools
    (python.withPackages (ps: with ps;
      let
        mypytorch = pytorchWithCuda.override {
          #cudaSupport = true;
          #cudatoolkit = pkgs.cudatoolkit_10;
          #cudnn = pkgs.cudnn_cudatoolkit_10;
        };
        mytorchvision = torchvision.override { pytorch = mypytorch; };
        myopencv4 = opencv4.override { enableFfmpeg = true;
                                       enableGStreamer = true;
                                       enableGtk2 = true;
                                     };
      in [
        # pytorch, customized above
        mypytorch
        mytorchvision
        #
        asyncssh
        colour
        Fabric
        h5py
        jupyter
        lmdb
        matplotlib
        myopencv4
        paramiko
        pillow
        pydot
        pyopenssl
        scikitlearn
        seaborn
        tensorflowWithCuda
        #(tensorflow.overridePythonAttrs (oldAttrs: { sse42Support = true;}))
        #tensorflow
        #tensorflow-tensorboard # python 3.6 not supported, use only with 3.5
        v4l_utils
        widgetsnbextension
      ]))
  ];

  MY_CUDA_PATH="${cudatoolkit}/lib";
  shellHook = ''
    # nixpkgs pinning ...
    echo "${pinMessage}"
    echo "unpinned git hash:" $(git -C ~/nixpkgs rev-parse HEAD)
    #TODO make something like the following work...
    #echo "unpinned git hash:" $(git -C <nixpkgs> rev-parse HEAD)
    echo "nix-shell with pinned nixpkgs? ${pkgs.lib.boolToString(pinOK)}"

    # Python stuff..
    # 1) Allow the use of wheels.
    SOURCE_DATE_EPOCH=$(date +%s)
    # 2) Augment the dynamic linker path
    export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${pkgs.readline}/lib
    # 3) Installing python packages that are missing from nixpkgs
    echo "Setting up virtualenv"
    VENV=venv
    #virtualenv -qq --clear venv
    if test ! -d $VENV; then
      virtualenv $VENV
    fi
    source ./$VENV/bin/activate
    export PYTHONPATH=`pwd`/$VENV/${python3.sitePackages}/:$PYTHONPATH
    echo "Installing imagezmg (dev mode, expects to find ./imagezmq)"
    pip install -e ./imagezmq
    '';

}


