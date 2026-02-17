{ pkgs, ... }: {
  # To learn more about how to use Nix to configure your environment
  # see: https://developers.google.com/idx/guides/customize-idx-env
  
  # Which nixpkgs channel to use.
  channel = "stable-24.05"; # or "unstable"

  # Use https://search.nixos.org/packages to find packages
  packages = [
    # Add python, pip, and other dependencies from requirements.txt
    pkgs.python3
    pkgs.python3Packages.pip
    pkgs.python3Packages.pytest
    pkgs.python3Packages.pytest-cov
    pkgs.python3Packages.mypy
    pkgs.python3Packages.markdown
  ];

  # Sets environment variables in the workspace
  env = {};

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
        # Python dependencies are installed via Nix packages above.
        # Open editors for the following files by default, if they exist:
        default.openFiles = [ ".idx/dev.nix" "README.md" ];
      };
      # Runs when the workspace is (re)started
      onStart = {
      };
    };
  };
}
