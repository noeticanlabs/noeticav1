{ pkgs, ... }: {
  # To learn more about how to use Nix to configure your environment
  # see: https://developers.google.com/idx/guides/customize-idx-env
  
  # Which nixpkgs channel to use.
  channel = "stable-24.05"; # or "unstable"

  # Use https://search.nixos.org/packages to find packages
  packages = [
    # Base Python 3.11
    pkgs.python311
    
    # Python packages - using python311Packages for importable modules
    pkgs.python311Packages.pip
    pkgs.python311Packages.pytest
    pkgs.python311Packages.pytest-cov
    pkgs.python311Packages.mypy
    pkgs.python311Packages.markdown
    pkgs.python311Packages.numpy
    pkgs.python311Packages.scipy
  ];

  # Sets environment variables in the workspace
  env = {
    # Point to user-local packages (installed via pip --target)
    # The .local directory contains packages that pip installs
    PYTHONPATH = "/home/user/noeticav1/.local/lib/python3.11/site-packages:${pkgs.python311Packages.numpy}/lib/python3.11/site-packages:${pkgs.python311Packages.scipy}/lib/python3.11/site-packages";
  };

  idx = {
    # Search for the extensions you want on https://open-vsx.org/ and use "publisher.id"
    extensions = [
      # Add the official Python extension for VS Code
      "ms-python.python"
      "google.gemini-cli-vscode-ide-companion"
    ];
    
    # Workspace lifecycle hooks
    workspace = {
      # Runs when a workspace is first created
      onCreate = {
        # Install Python dependencies from requirements.txt using pip
        # This ensures all dependencies are available
        default.openFiles = [ ".idx/dev.nix" "README.md" ];
      };
      # Runs when the workspace is (re)started
      onStart = {
      };
    };
  };
}
