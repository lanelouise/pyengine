from __future__ import annotations

from math import exp, floor, hypot
from typing import Protocol

from panda3d.core import Vec3

from engine.core.events import Events


class Shape(Protocol):
  """
  Describe what physics needs from a collider: a circle on the ground plane whose body may be pushed and bounced.
  """
  @property
  def center(self) -> tuple[float, float]:
    """
    Get the circle's center on the ground plane, in the scene's coordinates.
    """
    ...

  @property
  def radius(self) -> float:
    """
    Get the circle's radius, in units.
    """
    ...

  @property
  def inverse_mass(self) -> float:
    """
    Get how easily the shape is pushed: 1 / mass, or 0 when nothing can push it.
    """
    ...

  @property
  def velocity(self) -> Vec3:
    """
    Get the velocity of the shape's body, in units per second, or zero when it has none.
    """
    ...

  @property
  def restitution(self) -> float:
    """
    Get how much of the approach speed the shape's body keeps as rebound, from 0 (no bounce) to 1 (full bounce).
    """
    ...

  def apply_impulse(self, impulse: Vec3) -> None:
    """
    Change the velocity of the shape's body by impulse / mass; a shape that cannot be pushed ignores it.
    """
    ...

  def push(self, x: float, y: float) -> None:
    """
    Move the shape's body along the ground plane, in the scene's coordinates.
    """
    ...


class Motion(Protocol):
  """
  Describe what physics needs from a rigid body: a velocity that moves its node and fades with drag.
  """
  @property
  def velocity(self) -> Vec3:
    """
    Get the velocity, in units per second, in the scene's coordinates.
    """
    ...

  @velocity.setter
  def velocity(self, value: Vec3) -> None:
    """
    Set the velocity.
    """
    ...

  @property
  def drag(self) -> float:
    """
    Get the fraction of the velocity lost per second, as an exponential decay rate.
    """
    ...

  def move(self, offset: Vec3) -> None:
    """
    Move the body's node, in the scene's coordinates.
    """
    ...


class Physics:
  """
  Move rigid bodies by their velocity, make colliding shapes push and bounce off each other by their masses, and
  report when two of them start touching.

  Emits 'collision.started' with the two shapes as 'a' and 'b' and the velocity of 'b' relative to 'a' as 'velocity'.
  """
  def __init__(self, events: Events, cell: float = 1.0) -> None:
    """
    Start without shapes or bodies.

    Args:
      events (Events): Event bus receiving collision events.
      cell (float): Side of the grid cells used to find nearby shapes, in units; it must be at least the widest shape's diameter.
    """
    self._events = events
    self._cell = cell
    self._shapes: list[Shape] = []
    self._bodies: list[Motion] = []

    # Pairs touching in the previous step, so only new contacts are reported.
    self._contacts: dict[tuple[int, int], tuple[Shape, Shape]] = {}

  def add_collider(self, shape: Shape) -> None:
    """
    Start resolving a shape's overlaps.

    Args:
      shape (Shape): Shape to register.
    """
    self._shapes.append(shape)

  def remove_collider(self, shape: Shape) -> None:
    """
    Stop resolving a shape's overlaps.

    Args:
      shape (Shape): Registered shape.
    """
    if shape in self._shapes:
      self._shapes.remove(shape)

  def add_rigidbody(self, body: Motion) -> None:
    """
    Start moving a body by its velocity.

    Args:
      body (Motion): Body to register.
    """
    self._bodies.append(body)

  def remove_rigidbody(self, body: Motion) -> None:
    """
    Stop moving a body.

    Args:
      body (Motion): Registered body.
    """
    if body in self._bodies:
      self._bodies.remove(body)

  def touching(self, shape: Shape) -> list[Shape]:
    """
    Get the shapes that were touching a shape in the latest step, for sensing; collision response needs no query.

    Args:
      shape (Shape): Registered shape.

    Returns:
      list[Shape]: Shapes in contact with it.
    """
    return [b if a is shape else a for a, b in self._contacts.values() if shape is a or shape is b]

  def step(self, dt: float) -> None:
    """
    Advance the bodies, resolve each overlapping pair once, and report the pairs that started touching.

    Args:
      dt (float): Elapsed time since the previous frame, in seconds.
    """
    # Move each body by its velocity, then let drag slow it down so a thrown body slides and stops.
    for body in self._bodies:
      body.move(body.velocity * dt)
      body.velocity = body.velocity * exp(-body.drag * dt)

    # Bucket the shapes by grid cell, so each shape is only tested against its neighbors.
    grid: dict[tuple[int, int], list[Shape]] = {}
    for shape in self._shapes:
      grid.setdefault(self._key(shape.center), []).append(shape)

    contacts: dict[tuple[int, int], tuple[Shape, Shape]] = {}

    for shape in self._shapes:
      column, row = self._key(shape.center)

      for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
          for other in grid.get((column + dx, row + dy), ()):
            # Test each pair once.
            if id(other) <= id(shape):
              continue

            if self._collide(shape, other):
              pair = (id(shape), id(other))
              contacts[pair] = (shape, other)

              if pair not in self._contacts:
                self._events.emit('collision.started', a=shape, b=other, velocity=other.velocity - shape.velocity)

    self._contacts = contacts

  def _collide(self, a: Shape, b: Shape) -> bool:
    """
    Resolve an overlap: push the shapes apart and exchange momentum along the line between their centers.

    The lighter shape moves more and gains more speed, so a heavy body running into a light one throws it.

    Args:
      a (Shape): First shape.
      b (Shape): Second shape.

    Returns:
      bool: Whether the shapes were overlapping.
    """
    (ax, ay), (bx, by) = a.center, b.center
    distance = hypot(bx - ax, by - ay)
    overlap = a.radius + b.radius - distance

    if overlap <= 0:
      return False

    # Two shapes that nothing can push stay where they are.
    total = a.inverse_mass + b.inverse_mass
    if total == 0:
      return True

    # Shapes at the same spot have no line between them, so pick an arbitrary one.
    nx, ny = ((bx - ax) / distance, (by - ay) / distance) if distance > 0 else (1.0, 0.0)

    # Each shape takes a share of the push inversely proportional to its mass.
    share_a = overlap * a.inverse_mass / total
    share_b = overlap * b.inverse_mass / total
    a.push(-nx * share_a, -ny * share_a)
    b.push(nx * share_b, ny * share_b)

    # Bodies already moving apart need no impulse; approaching ones exchange momentum along the normal.
    normal = Vec3(nx, ny, 0)
    approach = (b.velocity - a.velocity).dot(normal)

    if approach < 0:
      restitution = min(a.restitution, b.restitution)
      impulse = normal * (-(1 + restitution) * approach / total)
      a.apply_impulse(-impulse)
      b.apply_impulse(impulse)

    return True

  def _key(self, center: tuple[float, float]) -> tuple[int, int]:
    """
    Get the grid cell containing a point.

    Args:
      center (tuple[float, float]): Point on the ground plane.

    Returns:
      tuple[int, int]: Cell column and row.
    """
    return floor(center[0] / self._cell), floor(center[1] / self._cell)
