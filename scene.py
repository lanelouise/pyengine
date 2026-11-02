from __future__ import annotations

from abc import ABC

from direct.task.Task import Task
from panda3d.core import NodePath, PythonTask

import engine.game as game_module


class Scene(ABC):
  """
  Own scene content and manage its activation and frame update task.
  """
  @property
  def game(self) -> game_module.Game:
    """
    Get the game that owns this scene and provides shared runtime services.
    """
    return self._game

  @property
  def dt(self) -> float:
    """
    Get the elapsed time since the previous frame, in seconds.
    """
    return self._game.clock.getDt()

  @property
  def is_active(self) -> bool:
    """
    Indicate whether this scene has a registered update task.
    """
    return self._task is not None

  def __init__(self, game: game_module.Game) -> None:
    """
    Store the owning game and prepare a detached scene root.

    Args:
      game (game_module.Game): Game that creates and owns this scene instance.
    """
    self._game = game

    # Retain the task handle so destruction removes only this scene's update.
    self._task: PythonTask | None = None

    # Keep constructed content detached until the scene is loaded.
    self._root = NodePath(type(self).__name__)

  def load(self) -> None:
    """
    Activate the prepared scene and register its update task once.
    """
    # Repeated loads must not register duplicate update tasks.
    if self._task is not None:
      return

    # Make constructed content visible and apply scene-specific camera settings.
    self.activate(self.game.render)

    # Retain the update task handle for activation checks and cleanup.
    self._task = self._game.tasks.add(self.update, f'{type(self).__name__}-update')

  def activate(self, parent: NodePath) -> None:
    """
    Attach the scene root to its parent; subclasses may configure shared resources.

    Args:
      parent (NodePath): Parent that will contain the active scene.
    """
    self._root.reparentTo(parent)

  def update(self, task: Task) -> int:
    """
    Keep the scene scheduled for the next frame.

    Args:
      task (Task): Panda3D task executing this frame.

    Returns:
      int: Status requesting execution on the next frame.
    """
    return task.cont

  def destroy(self) -> None:
    """
    Stop scene updates and remove scene-owned visual objects.
    """
    # Stop frame callbacks before removing the visual objects they may access.
    if self._task is not None:
      self.game.tasks.remove(self._task)
      self._task = None

    # Remove all scene-owned nodes through their common root.
    self._root.removeNode()
