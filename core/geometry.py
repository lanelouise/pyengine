from __future__ import annotations

from math import isfinite
from typing import cast

from panda3d.core import GeomNode, GeomVertexData, GeomVertexFormat, GeomVertexReader, GeomVertexWriter, NodePath, RescaleNormalAttrib, Vec3

from engine.runtime.loader import Loader


def instance(source: NodePath, parent: NodePath, name: str = 'instance') -> NodePath:
  """
  Share a model under an independent placement node, leaving the source transform untouched.

  Args:
    source (NodePath): Model whose geometry and render state are shared.
    parent (NodePath): Parent of the independent placement node.
    name (str): Name of the placement node.

  Returns:
    NodePath: Unique node to position, rotate, scale, show, or hide.
  """
  placement = parent.attachNewNode(name)
  source.instanceTo(placement)
  return placement


def ellipsoid(loader: Loader, radii: Vec3) -> NodePath:
  """
  Load the bundled sphere as an ellipsoid with smooth radial normals and normal normalization.

  Args:
    loader (Loader): Asset loading service.
    radii (Vec3): Positive, finite radii along each axis.

  Returns:
    NodePath: Detached primitive with its own transform and vertex data.

  Raises:
    ValueError: If any radius is nonpositive or not finite.
  """
  if any(not isfinite(radius) or radius <= 0 for radius in radii):
    raise ValueError('Ellipsoid radii must be positive and finite.')

  shape = loader.model('models/misc/sphere')
  for path in shape.findAllMatches('**/+GeomNode'):
    node = cast(GeomNode, path.node())
    for index in range(node.getNumGeoms()):
      geom = node.modifyGeom(index)
      data = GeomVertexData(geom.getVertexData().convertTo(GeomVertexFormat.getV3n3()))
      vertices = GeomVertexReader(data, 'vertex')
      normals = GeomVertexWriter(data, 'normal')
      while not vertices.isAtEnd():
        normal = Vec3(vertices.getData3())
        normal.normalize()
        normals.addData3(normal)
      geom.setVertexData(data)

  shape.setAttrib(RescaleNormalAttrib.make(RescaleNormalAttrib.MNormalize))
  shape.setScale(radii)
  return shape
