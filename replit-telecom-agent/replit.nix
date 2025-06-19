# telecom_agent/replit.nix
{ pkgs }: {
  deps = [
    pkgs.python310Full
    pkgs.poetry
  ];
  env = {
    PYTHON_LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [];
    POETRY_VIRTUALENVS_IN_PROJECT = "true";
  };
}
