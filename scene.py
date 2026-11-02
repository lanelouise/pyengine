from __future__ import annotations

from abc import ABC

from direct.task.Task import Task
from panda3d.core import NodePath, PythonTask

import engine.game as game_module
from engine.node3d import Node3D


class Scene(Node3D, ABC):
  """
  Root the scene hierarchy and manage its activation and frame update task.

  Subclasses build their tree in on_ready(), which runs when the game registers the scene.
  """
  @property
  def dt(self) -> float:
    """
    Get the elapsed time since the previous frame, in seconds.
    """
    return self.game.clock.getDt()

  @property
  def is_active(self) -> bool:
    """
    Indicate whether this scene has a registered update task.
    """
    return self._task is not None

  def __init__(self, game: game_module.Game) -> None:
    """
    Store the owning game and build the scene tree under a detached root.

    Args:
      game (game_module.Game): Game that creates and owns this scene instance.
    """
    super().__init__()

    # Retain the task handle so destruction removes only this scene's update.
    self._task: PythonTask | None = None

    # The scene is the root of its tree, so it is inside the tree from the start; content stays detached until loaded.
    self._game = game
    self.on_ready()

  def load(self) -> None:
    """
    Activate the prepared scene and register its update task once.
    """
    # Repeated loads must not register duplicate update tasks.
    if self._task is not None:
      return

    # Make constructed content visible.
    self.activate(self.game.render)

    # Retain the update task handle for activation checks and cleanup.
    self._task = self.game.tasks.add(self._tick, f'{type(self).__name__}-update')

  def activate(self, parent: NodePath) -> None:
    """
    Attach the scene root to its parent; subclasses may configure shared resources.

    Args:
      parent (NodePath): Parent that will contain the active scene.
    """
    self._root.reparentTo(parent)

  def destroy(self) -> None:
    """
    Stop scene updates, then destroy the tree and remove the scene root.
    """
    # Stop frame callbacks before removing the objects they may access.
    if self._task is not None:
      self.game.tasks.remove(self._task)
      self._task = None

    super().destroy()

  def _tick(self, task: Task) -> int:
    """
    Update the whole tree once per frame.

    Args:
      task (Task): Panda3D task executing this frame.

    Returns:
      int: Status requesting execution on the next frame.
    """
    self.update(self.dt)

    return task.cont
