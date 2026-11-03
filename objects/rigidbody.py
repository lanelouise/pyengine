from __future__ import annotations

from typing import cast

from panda3d.core import Vec3

from engine.core.node import Node, Node3D


class RigidBody(Node):
  """
  Let the parent react to forces: it moves by its velocity, slows down by drag, and is pushed by colliders by its mass.

  A kinematic body is moved only by its own code: it pushes others but is never pushed.
  """
  @property
  def mass(self) -> float:
    """
    Get the mass; heavier bodies push lighter ones further and gain less speed from impulses.
    """
    return self._mass

  @property
  def inverse_mass(self) -> float:
    """
    Get how easily the body is pushed: 1 / mass, or 0 when kinematic.
    """
    return 0.0 if self._kinematic else 1.0 / self._mass

  @property
  def kinematic(self) -> bool:
    """
    Indicate whether the body ignores pushes and impulses.
    """
    return self._kinematic

  @property
  def velocity(self) -> Vec3:
    """
    Get the velocity, in units per second, in the scene's coordinates.
    """
    return Vec3(self._velocity)

  @velocity.setter
  def velocity(self, value: Vec3) -> None:
    """
    Set the velocity, ignoring its height so the body stays on the ground.

    Args:
      value (Vec3): New velocity, in units per second.
    """
    self._velocity = Vec3(value.x, value.y, 0)

  @property
  def drag(self) -> float:
    """
    Get the fraction of the velocity lost per second, as an exponential decay rate.
    """
    return self._drag

  @property
  def restitution(self) -> float:
    """
    Get how much of the approach speed is kept as rebound in a collision, from 0 (no bounce) to 1 (full bounce).
    """
    return self._restitution

  def __init__(self, mass: float = 1.0, drag: float = 0.0, restitution: float = 0.0, kinematic: bool = False) -> None:
    """
    Configure the body.

    Args:
      mass (float): Mass, which must be positive.
      drag (float): Exponential decay rate of the velocity, per second; 0 keeps moving forever.
      restitution (float): Bounce kept in collisions, from 0 to 1; a pair uses the lower of the two values.
      kinematic (bool): Whether the body ignores pushes and impulses.

    Raises:
      ValueError: If the mass is not positive.
    """
    if mass <= 0:
      raise ValueError('Mass must be positive.')

    super().__init__()
    self._mass = mass
    self._drag = drag
    self._restitution = restitution
    self._kinematic = kinematic
    self._velocity = Vec3(0, 0, 0)

  def on_ready(self) -> None:
    """
    Start moving with the physics.
    """
    self.game.physics.add_rigidbody(self)

  def on_destroy(self) -> None:
    """
    Stop moving with the physics.
    """
    self.game.physics.remove_rigidbody(self)

  def apply_impulse(self, impulse: Vec3) -> None:
    """
    Change the velocity at once, by impulse / mass; a kinematic body ignores it.

    Args:
      impulse (Vec3): Impulse, in the scene's coordinates; its height is ignored.
    """
    if not self._kinematic:
      self.velocity = self._velocity + impulse / self._mass

  def move(self, offset: Vec3) -> None:
    """
    Move the parent, in the scene's coordinates.

    Args:
      offset (Vec3): Displacement; its height is ignored.
    """
    root = cast(Node3D, self.parent).root
    position = root.getPos(self.scene.root)
    position.x += offset.x
    position.y += offset.y
    root.setPos(self.scene.root, position)
