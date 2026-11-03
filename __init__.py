from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path
from typing import Any

from panda3d.core import loadPrcFileData

from engine.core.events import Events
from engine.core.game import Game
from engine.core.input import Input
from engine.core.node import Scene
from engine.core.physics import Physics
from engine.runtime.app import App
from engine.runtime.reloader import Reloader

__all__ = ['run']


def run(scene_path: str, **config: Any) -> None:
  """
  Open the window, build the scene found in a directory, and process frames until the window closes.

  Args:
    scene_path (str): Directory of the scene's Python package; a relative path starts at the entry script's directory.
    config (Any): Optional settings: 'title' (str) for the window title, 'size' (tuple[int, int]) for the window size
      in pixels, and 'reload' (bool, True by default) to apply edits to the scene's sources while the game runs.

  Raises:
    TypeError: If a setting is not one of the supported ones.
    FileNotFoundError: If the directory holds no Python package.
    LookupError: If the package does not define exactly one Scene subclass.
  """
  unknown = set(config) - {'title', 'size', 'reload'}
  if unknown:
    raise TypeError(f'Unsupported settings: {", ".join(sorted(unknown))}.')

  # Window settings must be in place before the app opens the window.
  if 'title' in config:
    loadPrcFileData('', f'window-title {config["title"]}')
  if 'size' in config:
    width, height = config['size']
    loadPrcFileData('', f'win-size {width} {height}')

  directory = _resolve(scene_path)
  factory = _scene(directory)

  # Open the window and the runtime services.
  app = App()

  # Hand every node the services it reaches through self.game.
  events = Events()
  game = Game(Input(app.device), events, Physics(events), app.loader, app.renderer)

  # Apply edits to the scene's sources without restarting.
  if config.get('reload', True):
    Reloader(app, str(directory))

  app.run(game, factory)


def _resolve(scene_path: str) -> Path:
  """
  Find the scene's directory, so the game runs the same from any working directory.

  Args:
    scene_path (str): Absolute path, or path relative to the entry script's directory.

  Returns:
    Path: Absolute directory of the scene's package.

  Raises:
    FileNotFoundError: If the directory holds no Python package.
  """
  directory = Path(scene_path)

  if not directory.is_absolute():
    script = getattr(sys.modules['__main__'], '__file__', None)
    base = Path(script).resolve().parent if script is not None else Path.cwd()
    directory = base / directory

  directory = directory.resolve()

  if not (directory / '__init__.py').is_file():
    raise FileNotFoundError(f'{directory} is not a Python package with an __init__.py.')

  return directory


def _scene(directory: Path) -> type[Scene]:
  """
  Import the scene's package and pick the scene class it defines.

  Args:
    directory (Path): Directory of the scene's package.

  Returns:
    type[Scene]: The only Scene subclass defined in the package's __init__.py.

  Raises:
    LookupError: If the package does not define exactly one Scene subclass.
  """
  # The package imports its own modules by its name, as in 'from arena.player.player import Player'.
  parent = str(directory.parent)
  if parent not in sys.path:
    sys.path.insert(0, parent)

  module = import_module(directory.name)
  scenes = [value for value in vars(module).values() if isinstance(value, type) and issubclass(value, Scene) and value.__module__ == module.__name__]

  if len(scenes) != 1:
    raise LookupError(f'{directory.name} must define exactly one Scene subclass in __init__.py, found {len(scenes)}.')

  return scenes[0]
