from __future__ import annotations

from panda3d.core import Point3, Quat, Vec3

from engine.core.node import Node


class Camera(Node):
  """
  Frame a target from a fixed angle and distance by driving the game's shared camera.

  Every property change is applied right away, so nodes may move the camera in any update order.
  """
  @property
  def target(self) -> Point3:
    """
    Get the framed point, in the scene's coordinates.
    """
    return Point3(self._target)

  @target.setter
  def target(self, value: Point3) -> None:
    """
    Frame another point.

    Args:
      value (Point3): Point to keep at the center of the view, in the scene's coordinates.
    """
    self._target = Point3(value)
    self._apply()

  @property
  def distance(self) -> float:
    """
    Get the distance from the target to the camera, in units.
    """
    return self._distance

  @distance.setter
  def distance(self, value: float) -> None:
    """
    Move the camera closer to or farther from the target along its view direction.

    Args:
      value (float): New distance, in units.
    """
    self._distance = value
    self._apply()

  @property
  def rotation(self) -> Vec3:
    """
    Get the view angle as heading, pitch, and roll, in degrees, in the scene's coordinates.
    """
    return Vec3(self._rotation)

  @rotation.setter
  def rotation(self, value: Vec3) -> None:
    """
    Look at the target from another angle.

    Args:
      value (Vec3): New heading, pitch, and roll, in degrees.
    """
    self._rotation = Vec3(value)
    self._apply()

  @property
  def offset(self) -> Vec3:
    """
    Get the displacement added on top of the framing, in the scene's coordinates.
    """
    return Vec3(self._offset)

  @offset.setter
  def offset(self, value: Vec3) -> None:
    """
    Displace the camera without changing what it frames.

    Args:
      value (Vec3): New displacement, in units.
    """
    self._offset = Vec3(value)
    self._apply()

  @property
  def position(self) -> Point3:
    """
    Get where the camera is, in the scene's coordinates, including the offset.
    """
    return Point3(self._target - self.forward * self._distance + self._offset)

  @property
  def forward(self) -> Vec3:
    """
    Get the normalized view direction, in the scene's coordinates.
    """
    rotation = Quat()
    rotation.setHpr(self._rotation)

    return rotation.getForward()

  @property
  def fov(self) -> float:
    """
    Get the horizontal field of view, in degrees.
    """
    return self.game.renderer.lens.getFov().x

  @fov.setter
  def fov(self, value: float) -> None:
    """
    Widen or narrow the view, keeping the window's aspect ratio.

    Args:
      value (float): New horizontal field of view, in degrees.
    """
    lens = self.game.renderer.lens
    lens.setFov(value, value / lens.getAspectRatio())

  def __init__(self, target: Point3 | None = None, distance: float = 10.0, rotation: Vec3 | None = None) -> None:
    """
    Configure the framing, applied once the camera enters the tree.

    Args:
      target (Point3 | None): Point to keep at the center of the view, in the scene's coordinates; the origin when omitted.
      distance (float): Distance from the target to the camera, in units.
      rotation (Vec3 | None): View angle as heading, pitch, and roll, in degrees; looking 45 degrees down when omitted.
    """
    super().__init__()

    self._target = Point3(target) if target is not None else Point3(0, 0, 0)
    self._distance = distance
    self._rotation = Vec3(rotation) if rotation is not None else Vec3(0, -45, 0)
    self._offset = Vec3(0, 0, 0)

  def on_ready(self) -> None:
    """
    Take over the shared camera with this framing.
    """
    self._apply()

  def _apply(self) -> None:
    """
    Place and orient the shared camera, once the node is inside the tree.
    """
    if not self.is_inside_tree:
      return

    # The scene root sits at the origin of the rendered graph, so scene coordinates are rendered coordinates.
    renderer = self.game.renderer
    renderer.camera.setPos(renderer.root, self.position)
    renderer.camera.setHpr(renderer.root, self._rotation)
