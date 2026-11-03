from __future__ import annotations

from collections.abc import Sequence
from math import floor, isfinite

from panda3d.core import AmbientLight as PandaAmbientLight
from panda3d.core import DirectionalLight as PandaDirectionalLight
from panda3d.core import Light as PandaLight
from panda3d.core import NodePath, OrthographicLens, Point3, Vec3, Vec4

from engine.core.node import Node3D
from engine.core.transform import Transform


class Light(Node3D):
  """
  Own a scene light whose enabled state and resources follow the node lifecycle.
  """
  def __init__(self, light: PandaLight, color: Vec4 | None = None, enabled: bool = True) -> None:
    """
    Wrap a light without assuming a time of day or a scene shader policy.

    Args:
      light (PandaLight): Panda3D light owned by this node.
      color (Vec4 | None): Light color; white when omitted.
      enabled (bool): Whether the scene receives this light.
    """
    super().__init__()
    self._light = light
    self._root = NodePath(light)
    self._transform = Transform(self._root)
    self._enabled = enabled
    self.color = color if color is not None else Vec4(1, 1, 1, 1)

  @property
  def color(self) -> Vec4:
    """
    Get a copy of the light's color.
    """
    return Vec4(self._light.getColor())

  @color.setter
  def color(self, value: Vec4) -> None:
    """
    Set the light color independently of whether it is enabled.

    Args:
      value (Vec4): New light color.
    """
    self._light.setColor(value)

  @property
  def enabled(self) -> bool:
    """
    Get whether this light participates in scene lighting.
    """
    return self._enabled

  @enabled.setter
  def enabled(self, value: bool) -> None:
    """
    Add or remove the light from the scene, including its shadow calculations.

    Args:
      value (bool): Whether the light should participate in rendering.
    """
    if self._enabled != value:
      self._enabled = value
      if self.is_inside_tree:
        self._apply()

  def on_ready(self) -> None:
    """
    Apply the configured light state when entering the scene.
    """
    self._apply()

  def on_destroy(self) -> None:
    """
    Stop lighting the scene before releasing the light's scene graph node.
    """
    self.scene.root.clearLight(self.root)

  def _apply(self) -> None:
    """
    Synchronize the scene's light registry with the enabled state.
    """
    if self._enabled:
      self.scene.root.setLight(self.root)
    else:
      self.scene.root.clearLight(self.root)


class AmbientLight(Light):
  """
  Supply uniform fill light to the scene.
  """
  def __init__(self, color: Vec4 | None = None, enabled: bool = True) -> None:
    """
    Prepare uniform fill lighting.

    Args:
      color (Vec4 | None): Fill color; white when omitted.
      enabled (bool): Initial participation in scene lighting.
    """
    super().__init__(PandaAmbientLight('ambient'), color, enabled)


class DirectionalLight(Light):
  """
  Supply directional lighting with optional orthographic shadows fitted to world-space points.
  """
  def __init__(self, color: Vec4 | None = None, enabled: bool = True, shadows: bool = False, resolution: int = 2048) -> None:
    """
    Prepare directional light and its shadow camera.

    Args:
      color (Vec4 | None): Light color; white when omitted.
      enabled (bool): Initial participation in scene lighting.
      shadows (bool): Whether enabled lighting casts shadows; requires scene shaders.
      resolution (int): Positive shadow map width and height in texels.
    """
    if resolution <= 0:
      raise ValueError('Shadow resolution must be positive.')
    self._directional = PandaDirectionalLight('directional')
    self._directional.setLens(OrthographicLens())
    self._shadows = shadows
    self._resolution = resolution
    super().__init__(self._directional, color, enabled)

  def _apply(self) -> None:
    """
    Remove disabled lights from both lighting and shadow rendering, retaining the shadow configuration.
    """
    super()._apply()
    self._directional.setShadowCaster(self._enabled and self._shadows, self._resolution, self._resolution)

  def fit_shadows(self, points: Sequence[Point3], margin: float = 0.1) -> None:
    """
    Cover scene-space points with a square shadow map whose center snaps to whole texels.

    Args:
      points (Sequence[Point3]): Receiver and caster bounds in scene coordinates.
      margin (float): Positive finite padding around the supplied bounds.

    Raises:
      ValueError: If the bounds are empty, not finite, or the margin is invalid.
    """
    if not points or not isfinite(margin) or margin <= 0 or any(not isfinite(value) for point in points for value in point):
      raise ValueError('Shadow fitting requires finite points and a positive finite margin.')
    if not self._enabled or not self._shadows:
      return

    root = self.scene.root
    rotation = self.root.getQuat(root)
    inverse = rotation.conjugate()
    local = [inverse.xform(point) for point in points]
    left, right = min(point.x for point in local) - margin, max(point.x for point in local) + margin
    bottom, top = min(point.z for point in local) - margin, max(point.z for point in local) + margin
    near, far = min(point.y for point in local) - margin, max(point.y for point in local) + margin

    # An extra texel on each edge preserves coverage when the center is snapped.
    size = max(right - left, top - bottom)
    size += 2 * size / self._resolution
    texel = size / self._resolution
    center = Vec3(floor((left + right) / 2 / texel) * texel, near, floor((bottom + top) / 2 / texel) * texel)
    lens = self._directional.getLens()
    lens.setFilmSize(size, size)
    lens.setNearFar(0, far - near)
    self.root.setPos(root, rotation.xform(center))
