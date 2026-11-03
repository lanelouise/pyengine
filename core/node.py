from __future__ import annotations

from typing import TypeVar

from panda3d.core import NodePath

from engine.core.game import Game
from engine.core.transform import Transform

N = TypeVar('N', bound='Node')


class Node:
  """
  Form the scene hierarchy: a node owns its children, which are updated and destroyed along with it.

  Subclasses react to the lifecycle through on_ready(), on_update(dt), and on_destroy() instead of overriding
  update() and destroy(), which the app calls on the scene and which propagate down the tree.
  """
  @property
  def game(self) -> Game:
    """
    Get the services shared by the game's nodes.

    Raises:
      RuntimeError: If the node has not entered a scene yet.
    """
    if self._game is None:
      raise RuntimeError(f'{type(self).__name__} must be added to a scene before using the game.')

    return self._game

  @property
  def parent(self) -> Node | None:
    """
    Get the node this one was added to, or None for a scene.
    """
    return self._parent

  @property
  def children(self) -> tuple[Node, ...]:
    """
    Get the child nodes, in the order they are updated.
    """
    return tuple(self._children)

  @property
  def scene(self) -> Scene:
    """
    Get the scene at the root of this node's tree.
    """
    node = self
    while node._parent is not None:
      node = node._parent

    return node  # type: ignore[return-value]

  @property
  def is_inside_tree(self) -> bool:
    """
    Indicate whether the node has entered a scene and can use the game.
    """
    return self._game is not None

  def __init__(self) -> None:
    """
    Create a detached node; it enters the tree when added to a node that is already inside one.
    """
    self._game: Game | None = None
    self._parent: Node | None = None
    self._children: list[Node] = []
    self._destroyed = False

  def add(self, node: N) -> N:
    """
    Attach a child node, which enters the tree right away when this node is already inside one.

    Args:
      node (N): Detached node to attach.

    Returns:
      N: The attached node, so it can be kept in a single expression.

    Raises:
      ValueError: If the node already has a parent.
    """
    if node._parent is not None:
      raise ValueError(f'{type(node).__name__} already belongs to {type(node._parent).__name__}.')

    node._parent = self
    self._children.append(node)

    # Children added before this node enters the tree enter together with it.
    if self._game is not None:
      node._enter(self._game)

    return node

  def update(self, dt: float) -> None:
    """
    Update the children, in the order they were added, and then this node.

    Children run first so a node sees the result of its behaviors in the same frame.

    Args:
      dt (float): Elapsed time since the previous frame, in seconds.
    """
    for child in tuple(self._children):
      if not child._destroyed:
        child.update(dt)

    if not self._destroyed:
      self.on_update(dt)

  def destroy(self) -> None:
    """
    Destroy the children, then this node, and detach it from its parent.
    """
    if self._destroyed:
      return

    self._destroyed = True

    # Destroy in reverse order so later nodes, which may depend on earlier siblings, go first.
    for child in reversed(tuple(self._children)):
      child.destroy()

    self.on_destroy()

    # Release event subscriptions and device bindings so nothing calls into a destroyed node.
    if self._game is not None:
      self._game.events.release(self)
      self._game.input.release(self)

    self._unmount()

    if self._parent is not None:
      self._parent._children.remove(self)

  def on_ready(self) -> None:
    """
    Run once when the node enters the tree, before the children added earlier; do nothing by default.
    """

  def on_update(self, dt: float) -> None:
    """
    Run every frame after the children have updated; do nothing by default.

    Args:
      dt (float): Elapsed time since the previous frame, in seconds.
    """

  def on_destroy(self) -> None:
    """
    Run once when the node is destroyed, after its children; do nothing by default.
    """

  def _enter(self, game: Game) -> None:
    """
    Bind the node to the game, signal it is ready, and bring its pending children into the tree.

    Args:
      game (Game): Services of the tree the node is entering.
    """
    # Children added during on_ready() enter immediately, so only the earlier ones are pending.
    pending = tuple(self._children)

    self._game = game
    self._mount()
    self.on_ready()

    for child in pending:
      if not child._destroyed:
        child._enter(game)

  def _mount(self) -> None:
    """
    Attach scene graph resources once the node enters the tree; plain nodes have none.
    """

  def _unmount(self) -> None:
    """
    Release scene graph resources when the node is destroyed; plain nodes have none.
    """


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


class Scene(Node3D):
  """
  Root a tree of nodes; the app shows it, updates it every frame, and destroys it when switching scenes.

  Subclasses build their tree in on_ready(), which runs as soon as the scene is created.
  """
  def __init__(self, game: Game) -> None:
    """
    Enter the tree as its root and build the scene's content.

    Args:
      game (Game): Services shared by the scene's nodes.
    """
    super().__init__()
    self._game = game
    self.on_ready()

  def update(self, dt: float) -> None:
    """
    Advance the physics, then update the whole tree, so nodes see where their bodies ended up this frame.

    Args:
      dt (float): Elapsed time since the previous frame, in seconds.
    """
    self.game.physics.step(dt)
    super().update(dt)
