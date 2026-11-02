from __future__ import annotations

from panda3d.core import NodePath

from engine.node import Node
from engine.transform import Transform


class Node3D(Node):
  """
  Give a node a place in the 3D scene graph, with a root that holds its models and moves with its transform.
  """
  @property
  def root(self) -> NodePath:
    """
    Get the scene graph node that holds this node's models and its 3D descendants.
    """
    return self._root

  @property
  def transform(self) -> Transform:
    """
    Get the position and rotation of this node's root in its anchor's coordinates.
    """
    return self._transform

  def __init__(self) -> None:
    """
    Create a detached root, which joins the scene graph when the node enters the tree.
    """
    super().__init__()

    # The root exists before entering the tree, so the transform can be set right after construction.
    self._root = NodePath(type(self).__name__)
    self._transform = Transform(self._root)

  def anchor(self) -> NodePath:
    """
    Choose the scene graph node the root hangs from; by default, the root of the nearest 3D ancestor.

    Override it to hang the node elsewhere, such as a window corner or the scene root.

    Returns:
      NodePath: Node whose coordinates the transform is expressed in.

    Raises:
      RuntimeError: If no ancestor has a place in the scene graph.
    """
    node = self.parent
    while node is not None:
      if isinstance(node, Node3D):
        return node.root
      node = node.parent

    raise RuntimeError(f'{type(self).__name__} needs a 3D ancestor to hang from.')

  def _mount(self) -> None:
    """
    Attach the root under its anchor.
    """
    self._root.reparentTo(self.anchor())

  def _unmount(self) -> None:
    """
    Remove the root and its models from the scene graph.
    """
    self._root.removeNode()
