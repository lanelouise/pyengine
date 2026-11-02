from direct.showbase.DirectObject import DirectObject
from panda3d.core import NodePath

from engine.game import Game
from engine.transform import Transform


class Node:
  """
  Provide a scene graph root and lifecycle hooks for game objects.
  """
  @property
  def events(self) -> DirectObject:
    """
    Get the event handler for this node.

    Returns:
      DirectObject: Event handler for this node.
    """
    return self._events

  @property
  def transform(self) -> Transform:
    """
    Get the position and rotation of this node's root in its parent's coordinates.

    Returns:
      Transform: Transform of this node's root.
    """
    return self._transform

  def __init__(self, game: Game, parent: NodePath) -> None:
    """
    Store the owning game and create a named root under the parent.

    Args:
      game (Game): Game providing shared runtime services to this node.
      parent (NodePath): Scene graph node to which the new root is attached.
    """
    self._game = game

    # Store a direct object for event handling.
    self._events = DirectObject()

    # Group child objects under one root so they share transforms and removal.
    self._root = parent.attachNewNode(type(self).__name__)
    self._transform = Transform(self._root)

  def update(self, dt: float) -> None:
    """
    Provide a per-frame update hook for subclasses; do nothing by default.

    Args:
      dt (float): Elapsed time since the previous frame, in seconds.
    """

  def destroy(self) -> None:
    """
    Remove the root and its descendants from the scene graph.
    """
    self._root.removeNode()
    self._events.ignoreAll()
