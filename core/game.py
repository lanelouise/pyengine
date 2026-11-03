from __future__ import annotations

from engine.core.events import Events
from engine.core.input import Input
from engine.core.physics import Physics
from engine.runtime.loader import Loader
from engine.runtime.renderer import Renderer


class Game:
  """
  Hold the services every node reaches through self.game.
  """
  @property
  def input(self) -> Input:
    """
    Get the keyboard and mouse.
    """
    return self._input

  @property
  def events(self) -> Events:
    """
    Get the event bus shared by every node.
    """
    return self._events

  @property
  def physics(self) -> Physics:
    """
    Get the collision resolver shared by every collider.
    """
    return self._physics

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

  def __init__(self, input: Input, events: Events, physics: Physics, loader: Loader, renderer: Renderer) -> None:
    """
    Store the services shared by the game's nodes.

    Args:
      input (Input): Keyboard and mouse.
      events (Events): Event bus shared by every node.
      physics (Physics): Collision resolver shared by every collider.
      loader (Loader): Asset loader.
      renderer (Renderer): Scene graphs and camera that are drawn.
    """
    self._input = input
    self._events = events
    self._physics = physics
    self._loader = loader
    self._renderer = renderer
