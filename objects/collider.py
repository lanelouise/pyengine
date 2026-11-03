from __future__ import annotations

import math
from typing import cast

from panda3d.core import (
  Geom,
  GeomNode,
  GeomTriangles,
  GeomVertexData,
  GeomVertexFormat,
  GeomVertexWriter,
  NodePath,
  TransparencyAttrib,
  Vec3,
)

from engine.core.node import Node, Node3D
from engine.objects.rigidbody import RigidBody


class CircleCollider(Node):
  """
  Give the parent a circular footprint on the ground plane that other colliders cannot overlap.

  On its own the collider is a fixed obstacle; a sibling RigidBody lets it be pushed according to its mass.
  """
  @property
  def center(self) -> tuple[float, float]:
    """
    Get the parent's position on the ground plane, in the scene's coordinates.
    """
    position = self._body.root.getPos(self.scene.root)

    return position.x, position.y

  @property
  def radius(self) -> float:
    """
    Get the footprint's radius, in units.
    """
    return self._radius

  @property
  def rigidbody(self) -> RigidBody | None:
    """
    Get the sibling rigid body that lets the parent be pushed, if any.
    """
    for node in self._body.children:
      if isinstance(node, RigidBody):
        return node

    return None

  @property
  def inverse_mass(self) -> float:
    """
    Get how easily the parent is pushed: 1 / mass, or 0 without a rigid body or with a kinematic one.
    """
    rigidbody = self.rigidbody
    return rigidbody.inverse_mass if rigidbody is not None else 0.0

  @property
  def velocity(self) -> Vec3:
    """
    Get the velocity of the parent's rigid body, or zero without one.
    """
    rigidbody = self.rigidbody
    return rigidbody.velocity if rigidbody is not None else Vec3(0, 0, 0)

  @property
  def restitution(self) -> float:
    """
    Get the bounce of the parent's rigid body, or 0 without one.
    """
    rigidbody = self.rigidbody
    return rigidbody.restitution if rigidbody is not None else 0.0

  @property
  def layer(self) -> str:
    """
    Get the name telling what the collider belongs to, such as 'player' or 'enemy'.
    """
    return self._layer

  @property
  def visible(self) -> bool:
    """
    Indicate whether the footprint is drawn as a translucent cylinder, which helps tune radii.
    """
    return self._visible

  @visible.setter
  def visible(self, value: bool) -> None:
    """
    Show or hide the footprint cylinder.

    Args:
      value (bool): Whether to draw the footprint.
    """
    self._visible = value
    self._draw()

  @property
  def body(self) -> Node3D:
    """
    Get the node this collider moves, which is its parent.
    """
    return self._body

  def __init__(self, radius: float, layer: str = '', visible: bool = False) -> None:
    """
    Configure the footprint.

    Args:
      radius (float): Footprint radius, in units.
      layer (str): Name telling what the collider belongs to, so collision listeners can tell bodies apart.
      visible (bool): Whether to draw the footprint as a translucent cylinder.
    """
    super().__init__()
    self._radius = radius
    self._layer = layer
    self._visible = visible
    self._outline: NodePath | None = None

  def on_ready(self) -> None:
    """
    Start colliding.
    """
    self._body = cast(Node3D, self.parent)
    self.game.physics.add_collider(self)
    self._draw()

  def on_destroy(self) -> None:
    """
    Stop colliding and remove the footprint cylinder.
    """
    self.game.physics.remove_collider(self)

    if self._outline is not None:
      self._outline.removeNode()

  def apply_impulse(self, impulse: Vec3) -> None:
    """
    Pass a collision impulse to the parent's rigid body; without one, the parent is a fixed obstacle and ignores it.

    Args:
      impulse (Vec3): Impulse, in the scene's coordinates.
    """
    rigidbody = self.rigidbody
    if rigidbody is not None:
      rigidbody.apply_impulse(impulse)

  def push(self, x: float, y: float) -> None:
    """
    Move the parent along the ground plane.

    Args:
      x (float): Displacement along X, in the scene's coordinates.
      y (float): Displacement along Y, in the scene's coordinates.
    """
    root = self.scene.root
    position = self._body.root.getPos(root)
    position.x += x
    position.y += y
    self._body.root.setPos(root, position)

  def _draw(self) -> None:
    """
    Create or remove the footprint cylinder to match the visible flag, once the collider is inside the tree.
    """
    if not self.is_inside_tree:
      return

    if not self._visible:
      if self._outline is not None:
        self._outline.removeNode()
        self._outline = None
      return

    if self._outline is not None:
      return

    # Match the cylinder to the body's models, or use one unit when the body has none yet.
    bounds = self._body.root.getTightBounds(self._body.root)
    height = bounds[1].z if bounds is not None and bounds[1].z > 0 else 1.0

    self._outline = self._body.root.attachNewNode(self._cylinder(height))

    # A translucent, unlit, double-sided green shell lets the model show through while the footprint stays visible.
    self._outline.setColor(0.2, 1, 0.3, 0.3)
    self._outline.setTransparency(TransparencyAttrib.MAlpha)
    self._outline.setDepthWrite(False)
    self._outline.setTwoSided(True)
    self._outline.setLightOff(1)
    self._outline.setBin('transparent', 0)

  def _cylinder(self, height: float, sides: int = 24) -> GeomNode:
    """
    Build an open cylinder with a top cap, standing on the body's origin.

    Args:
      height (float): Cylinder height, in units.
      sides (int): Number of side faces approximating the circle.

    Returns:
      GeomNode: Geometry of the cylinder.
    """
    data = GeomVertexData('collider', GeomVertexFormat.getV3(), Geom.UHStatic)
    vertices = GeomVertexWriter(data, 'vertex')

    # Each side corner has a bottom and a top vertex; the last vertex is the center of the cap.
    for step in range(sides):
      angle = 2 * math.pi * step / sides
      x, y = math.cos(angle) * self._radius, math.sin(angle) * self._radius
      vertices.addData3(x, y, 0)
      vertices.addData3(x, y, height)

    vertices.addData3(0, 0, height)

    triangles = GeomTriangles(Geom.UHStatic)
    for step in range(sides):
      bottom, top = 2 * step, 2 * step + 1
      next_bottom, next_top = 2 * ((step + 1) % sides), 2 * ((step + 1) % sides) + 1
      triangles.addVertices(bottom, next_bottom, next_top)
      triangles.addVertices(bottom, next_top, top)
      triangles.addVertices(top, next_top, 2 * sides)

    geom = Geom(data)
    geom.addPrimitive(triangles)

    node = GeomNode('collider')
    node.addGeom(geom)

    return node
