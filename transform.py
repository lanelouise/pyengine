from __future__ import annotations

import math

from panda3d.core import NodePath, Point3, Vec3


class Transform:
  """
  Expose the position, rotation, and orientation of a scene graph node in its parent's coordinates.
  """
  @property
  def position(self) -> Point3:
    """
    Get the position in the parent's coordinates.
    """
    return self._node.getPos()

  @position.setter
  def position(self, value: Point3 | Vec3) -> None:
    """
    Move the node to a position in the parent's coordinates.

    Args:
      value (Point3 | Vec3): New position.
    """
    self._node.setPos(value)

  @property
  def rotation(self) -> Vec3:
    """
    Get the rotation as heading, pitch, and roll, in degrees, relative to the parent.
    """
    return Vec3(self._node.getHpr())

  @rotation.setter
  def rotation(self, value: Vec3) -> None:
    """
    Rotate the node to the given heading, pitch, and roll, in degrees, relative to the parent.

    Args:
      value (Vec3): New heading, pitch, and roll.
    """
    self._node.setHpr(value)

  @property
  def velocity(self) -> Vec3:
    """
    Get the velocity applied on each update, in units per second, in the parent's coordinates.
    """
    return Vec3(self._velocity)

  @velocity.setter
  def velocity(self, value: Vec3) -> None:
    """
    Set the velocity applied on each update.

    Args:
      value (Vec3): New velocity, in units per second, in the parent's coordinates.
    """
    self._velocity = Vec3(value)

  @property
  def forward(self) -> Vec3:
    """
    Get the normalized +Y axis of the node in the parent's coordinates, including any pitch.
    """
    forward = self._node.getQuat().getForward()
    forward.normalize()

    return forward

  @property
  def direction(self) -> Vec3:
    """
    Get the forward axis flattened onto the ground plane and normalized, or zero when it points straight up or down.
    """
    direction = self.forward
    direction.z = 0

    # A node looking straight up or down has no horizontal direction.
    if direction.lengthSquared() > 0:
      direction.normalize()

    return direction

  @property
  def right(self) -> Vec3:
    """
    Get the normalized +X axis of the node in the parent's coordinates.
    """
    right = self._node.getQuat().getRight()
    right.normalize()

    return right

  @property
  def scale(self) -> Vec3:
    """
    Get the scale along each axis, relative to the parent.
    """
    return Vec3(self._node.getScale())

  @scale.setter
  def scale(self, value: Vec3 | float) -> None:
    """
    Resize the node uniformly or along each axis, relative to the parent.

    Args:
      value (Vec3 | float): New scale, either one factor for every axis or one per axis.
    """
    self._node.setScale(value)

  def __init__(self, node: NodePath) -> None:
    """
    Wrap the node whose transform is exposed.

    Args:
      node (NodePath): Scene graph node moved and rotated by this transform.
    """
    self._node = node
    self._velocity = Vec3(0, 0, 0)

  def update(self, dt: float) -> None:
    """
    Move the node by its velocity over the elapsed time.

    Args:
      dt (float): Elapsed time since the previous frame, in seconds.
    """
    self.translate(Vec3(self._velocity * dt))

  def translate(self, offset: Vec3) -> None:
    """
    Move the node by an offset in the parent's coordinates.

    Args:
      offset (Vec3): Displacement to add to the current position.
    """
    self._node.setPos(self._node.getPos() + offset)

  def direction_to(self, target: Point3) -> Vec3:
    """
    Get the flat, normalized direction from the node to a target.

    Args:
      target (Point3): Point in the parent's coordinates.

    Returns:
      Vec3: Direction on the ground plane, or zero when the target is right above or below the node.
    """
    direction = self._flat_offset(target)

    if direction.lengthSquared() > 0:
      direction.normalize()

    return direction

  def distance_to(self, target: Point3) -> float:
    """
    Get the distance from the node to a target, measured on the ground plane.

    Args:
      target (Point3): Point in the parent's coordinates.

    Returns:
      float: Flat distance, in units.
    """
    return self._flat_offset(target).length()

  def move_towards(self, target: Point3, step: float) -> None:
    """
    Walk toward a target on the ground plane without stepping past it.

    Args:
      target (Point3): Point in the parent's coordinates.
      step (float): Largest distance to cover, in units.
    """
    offset = self._flat_offset(target)
    distance = offset.length()

    if distance > 0:
      self.translate(Vec3(offset * (min(step, distance) / distance)))

  def look_at(self, target: Point3) -> None:
    """
    Turn the node's heading toward a target, keeping it upright.

    Args:
      target (Point3): Point in the parent's coordinates.
    """
    direction = self.direction_to(target)

    if direction.lengthSquared() > 0:
      self._node.setH(self._heading(direction))

  def turn_towards(self, direction: Vec3, speed: float, dt: float) -> None:
    """
    Turn the node's heading gradually toward a flat direction.

    Args:
      direction (Vec3): Flat direction to face; it does not need to be normalized.
      speed (float): Fraction of the remaining angle covered per second.
      dt (float): Elapsed time since the previous frame, in seconds.
    """
    if direction.lengthSquared() == 0:
      return

    # Turn along the shortest arc so the node never spins the long way around.
    current = self._node.getH()
    delta = (self._heading(direction) - current + 180) % 360 - 180
    self._node.setH(current + delta * min(1.0, speed * dt))

  def _flat_offset(self, target: Point3) -> Vec3:
    """
    Get the offset from the node to a target with its height removed.

    Args:
      target (Point3): Point in the parent's coordinates.
    """
    offset = Vec3(target - self._node.getPos())
    offset.z = 0

    return offset

  @staticmethod
  def _heading(direction: Vec3) -> float:
    """
    Convert a flat direction into the heading that points the node's +Y axis along it.

    Args:
      direction (Vec3): Flat direction; it does not need to be normalized.
    """
    return math.degrees(math.atan2(-direction.x, direction.y))
