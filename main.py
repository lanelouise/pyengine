from __future__ import annotations

import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

# The repository root is the engine package itself, whose modules import each other as 'engine.*'.
# Register it under that name, so it runs from a clone of any folder name, such as 'pyengine'.
root = Path(__file__).resolve().parent

if 'engine' not in sys.modules:
  spec = spec_from_file_location('engine', root / '__init__.py', submodule_search_locations=[str(root)])
  assert spec is not None and spec.loader is not None
  package = module_from_spec(spec)
  sys.modules['engine'] = package
  spec.loader.exec_module(package)

from engine import run


def main() -> None:
  """
  Open the engine's default scene, to try the engine without a game.
  """
  run('scenes/default', title='pyengine')


if __name__ == '__main__':
  main()
