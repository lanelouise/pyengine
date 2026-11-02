import sys
from collections.abc import Callable
from importlib import import_module, invalidate_caches
from pathlib import Path
from threading import Event, Thread

from direct.task.Task import Task
from watchfiles import PythonFilter, watch

from engine.game import Game


class Reloader:
  """
  Monitor Python resource changes and reconstruct scenes in the existing game.
  """
  def __init__(self, source: str):
    """
    Start recursive monitoring for the lifetime of the Python process.

    Args:
      source (str): Source directory to monitor for Python file changes.
    """
    # Combine source changes until the caller can reload the instance.
    self._changes = Event()

    # Monitor files until process exit without accessing application objects.
    Thread(target=self._watch, args=(source,), daemon=True).start()

  def build(self, builder: Callable[[], Game]) -> Game:
    """
    Create and retain the game instance associated with this reloader.

    Args:
      builder (Callable[[], Game]): Factory that creates the game with its dependencies.

    Returns:
      Game: Instance created by the supplied factory.
    """
    game = builder()

    # Retain the initial instance as the source of runtime and scene registration.
    self._game = game

    return game

  def dispatch(self, task: Task) -> int:
    """
    Reload scenes once for pending resource changes on the caller thread.

    Args:
      task (Task): Panda3D task dispatching source changes.

    Returns:
      int: Status requesting execution on the next frame.
    """
    if self._changes.is_set():
      # Leave changes received during scene reconstruction pending for the next frame.
      self._changes.clear()

      # Execute application work on the caller thread rather than the monitor thread.
      self._reload()

    return task.cont

  def _reload(self) -> None:
    """
    Import updated resource classes and restore scenes in the same game instance.
    """
    if self._game is None:
      return

    # Preserve scene registration and activation before destroying scene instances.
    scenes = tuple(self._game.scenes.values())
    loaded = tuple(key for key, scene in self._game.scenes.items() if scene.is_active)

    # Refresh resource modules and bytecode while keeping engine definitions intact.
    for name, module in tuple(sys.modules.items()):
      if name.split('.')[0] == 'resources':
        cached = getattr(module, '__cached__', None)
        if cached is not None:
          Path(cached).unlink(missing_ok=True)
        del sys.modules[name]

    # Refresh all cached modules and bytecode.
    invalidate_caches()

    # Resolve fresh class definitions instead of reusing the previous objects.
    classes = tuple(getattr(import_module(type(scene).__module__), type(scene).__name__) for scene in scenes)

    # Replace scene content while preserving the game and its shared runtime.
    self._game.close()
    self._game.register(*classes)

    # Restore visibility and update tasks only for previously active scenes.
    for scene in loaded:
      self._game.scenes[scene].load()

  def _watch(self, directory: str) -> None:
    """
    Signal source changes without modifying application objects.

    Args:
      directory (str): Source directory to monitor recursively.
    """
    for _ in watch(directory, watch_filter=PythonFilter()):
      self._changes.set()
