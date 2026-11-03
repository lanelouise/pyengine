from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
from typing import Any, Protocol

from direct.showbase.ShowBase import ShowBase
from direct.task.Task import Task
from panda3d.core import NodePath

from engine.runtime.device import Device
from engine.runtime.loader import Loader
from engine.runtime.renderer import Renderer
from engine.runtime.time import Time


class Scene(Protocol):
  """
  Describe what the app needs from a scene, without depending on the layers built on top of the runtime.
  """
  @property
  def root(self) -> NodePath:
    """
    Get the scene graph node holding the scene's content.
    """
    ...

  def update(self, dt: float) -> None:
    """
    Advance the scene by one frame.
    """
    ...

  def destroy(self) -> None:
    """
    Remove the scene's content.
    """
    ...


class App:
  """
  Own the window and the frame loop, provide the runtime services, and run one scene at a time.
  """
  @property
  def device(self) -> Device:
    """
    Get the raw keyboard and mouse.
    """
    return self._device

  @property
  def loader(self) -> Loader:
    """
    Get the asset loader.
    """
    return self._loader

  @property
  def renderer(self) -> Renderer:
    """
    Get the scene graphs and camera that are drawn.
    """
    return self._renderer

  @property
  def time(self) -> Time:
    """
    Get the frame timing.
    """
    return self._time

  def __init__(self) -> None:
    """
    Open the window and prepare the runtime services.
    """
    self._base = ShowBase()

    # Leave camera positioning to the scenes.
    self._base.disableMouse()

    self._device = Device(self._base)
    self._loader = Loader(self._base)
    self._renderer = Renderer(self._base)
    self._time = Time()

    # The running scene, the game it was built with, and the factory that rebuilds it.
    self._scene: Scene | None = None
    self._game: Any = None
    self._factory: Callable[[Any], Scene] | None = None

  def schedule(self, callback: Callable[[], None], sort: int = 0) -> None:
    """
    Call a function once per frame for the lifetime of the app.

    Args:
      callback (Callable[[], None]): Function to call.
      sort (int): Order among frame callbacks; lower values run first, and scenes run at 0.
    """
    def tick(task: Task) -> int:
      callback()
      return task.cont

    self._base.taskMgr.add(tick, f'app-{callback.__qualname__}', sort=sort)

  def change(self, factory: Callable[[Any], Scene]) -> None:
    """
    Replace the running scene with a new one built for the same game.

    Args:
      factory (Callable[[Any], Scene]): Scene class, called with the game to build the scene.
    """
    if self._scene is not None:
      self._scene.destroy()
      self._scene = None

    self._factory = factory
    self._scene = factory(self._game)
    self._scene.root.reparentTo(self._renderer.root)

  def reload(self) -> None:
    """
    Rebuild the running scene from a freshly imported definition of its class.
    """
    if self._factory is None:
      return

    # Resolve the class again by name, so a reimported module provides its new definition.
    module, name = self._factory.__module__, getattr(self._factory, '__qualname__', '')
    self.change(getattr(import_module(module), name))

  def run(self, game: Any, factory: Callable[[Any], Scene]) -> None:
    """
    Show the first scene and process frames until the window closes.

    Args:
      game (Any): Services handed to every scene.
      factory (Callable[[Any], Scene]): Scene class, called with the game to build the first scene.
    """
    self._game = game
    self.change(factory)
    self.schedule(self._update)

    try:
      self._base.run()
    finally:
      # Remove the scene's content before the runtime it depends on.
      if self._scene is not None:
        self._scene.destroy()
      self._base.destroy()

  def _update(self) -> None:
    """
    Advance the running scene by one frame.
    """
    if self._scene is not None:
      self._scene.update(self._time.dt)
