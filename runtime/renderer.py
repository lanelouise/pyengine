from __future__ import annotations

from direct.showbase.ShowBase import ShowBase
from panda3d.core import Lens, NodePath


class Renderer:
  """
  Expose what gets drawn: the 3D scene graph, the camera that views it, and the 2D overlay.
  """
  @property
  def root(self) -> NodePath:
    """
    Get the root of the 3D scene graph.
    """
    return self._base.render

  @property
  def camera(self) -> NodePath:
    """
    Get the camera that draws the 3D scene graph.
    """
    return self._base.cam

  @property
  def lens(self) -> Lens:
    """
    Get the camera's lens.
    """
    return self._base.cam.node().getLens()

  @property
  def top_right(self) -> NodePath:
    """
    Get the 2D overlay node pinned to the window's top-right corner.
    """
    return self._base.a2dTopRight

  def __init__(self, base: ShowBase) -> None:
    """
    Store the runtime that owns the window.

    Args:
      base (ShowBase): Runtime providing the scene graphs and the camera.
    """
    self._base = base
