from __future__ import annotations

from engine.core.node import Node3D


class Terrain(Node3D):
  """
  Hold the ground's meshes under its root and answer the ground height.

  The ground is flat at its level by default; behaviors attach the meshes and may change the level.
  """
  @property
  def level(self) -> float:
    """
    Get the height of the flat ground surface, in the terrain's coordinates.
    """
    return self._level

  @level.setter
  def level(self, value: float) -> None:
    """
    Raise or lower the flat ground surface.

    Args:
      value (float): New surface height, in units.
    """
    self._level = value

  def __init__(self, level: float = 0.0) -> None:
    """
    Create an empty, flat ground.

    Args:
      level (float): Height of the ground surface, in units.
    """
    super().__init__()
    self._level = level

  def height(self, x: float, y: float) -> float:
    """
    Get the ground height at a point.

    Args:
      x (float): Horizontal coordinate, in the terrain's coordinates.
      y (float): Depth coordinate, in the terrain's coordinates.

    Returns:
      float: Height of the ground surface at that point.
    """
    return self._level
