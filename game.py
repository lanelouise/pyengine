from __future__ import annotations

from contextlib import ExitStack

from direct.showbase.Loader import Loader
from direct.showbase.ShowBase import ShowBase
from direct.task.Task import TaskManager
from panda3d.core import Camera, ClockObject, NodePath

import engine.scene as scene_module
from engine.events import Events
from engine.input import Input


class Game:
  """
  Provide shared runtime services and own registered scene instances.
  """
  @property
  def context(self) -> ShowBase:
    """
    Get the shared runtime context.
    """
    return self._context

  @property
  def loader(self) -> Loader:
    """
    Get the asset loader for this game.
    """
    return self._context.loader

  @property
  def input(self) -> Input:
    """
    Get the keyboard and mouse state of the current frame.
    """
    return self._input

  @property
  def events(self) -> Events:
    """
    Get the event bus shared by every node of every scene.
    """
    return self._events

  @property
  def scenes(self) -> dict[tuple[str, str], scene_module.Scene]:
    """
    Get the scene registry keyed by module name and qualified class name.
    """
    return self._scenes

  @property
  def camera(self) -> NodePath[Camera]:
    """
    Get the shared camera root provided by the Panda3D runtime.
    """
    return self._context.cam

  @property
  def render(self) -> NodePath:
    """
    Get the scene graph root used to display loaded scenes.
    """
    return self._context.render

  @property
  def clock(self) -> ClockObject:
    """
    Get the shared frame clock.
    """
    return self._clock

  @property
  def tasks(self) -> TaskManager:
    """
    Get the shared task manager used to schedule scene updates.
    """
    return self._context.taskMgr

  def __init__(self, context: ShowBase) -> None:
    """
    Store the runtime without taking ownership of its lifetime.

    Args:
      context (ShowBase): Persistent runtime created by the entry point.
    """
    self._context = context

    # Use the runtime's shared frame clock for scene timing.
    self._clock = ClockObject.getGlobalClock()

    # Answer button queries without exposing the runtime's mouse watcher.
    self._input = Input(context)

    # Let nodes publish and react to events without knowing each other.
    self._events = Events()

    # Keep scene instances available independently of their update tasks.
    self._scenes: dict[tuple[str, str], scene_module.Scene] = {}

  def register(self, *scenes: type[scene_module.Scene]) -> None:
    """
    Instantiate and register each scene with access to this game.

    Args:
      scenes (type[scene_module.Scene]): Scene classes to instantiate and store.

    Raises:
      TypeError: If any entry is not a Scene subclass.
    """
    # Validate every entry before constructing any scene.
    for scene in scenes:
      if not isinstance(scene, type) or not issubclass(scene, scene_module.Scene):
        raise TypeError('Registered scenes must inherit from Scene.')

    # Re-registering a module and class name replaces its stored instance.
    for scene in scenes:
      self._scenes[(scene.__module__, scene.__qualname__)] = scene(self)

  def get_scene(self, scene: type[scene_module.Scene]) -> scene_module.Scene:
    """
    Retrieve an existing registered scene without constructing or loading it.

    Args:
      scene (type[scene_module.Scene]): Registered scene class to select.

    Returns:
      scene_module.Scene: Instance created by register(), whether active or not.

    Raises:
      ValueError: If the requested scene has not been registered.
    """
    # Identify scenes by module and class name rather than class object identity.
    instance = self._scenes.get((scene.__module__, scene.__qualname__))

    if instance is None:
      raise ValueError(f'Scene {scene.__qualname__} must be registered before loading.')

    return instance

  def close(self) -> None:
    """
    Destroy registered scenes while preserving the shared runtime.
    """
    with ExitStack() as resources:
      # Schedule every scene for cleanup even if a destroy method raises.
      for scene in self._scenes.values():
        resources.callback(scene.destroy)

      # Clear the registry after all destruction callbacks have been registered.
      self._scenes.clear()
