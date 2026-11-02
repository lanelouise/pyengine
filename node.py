from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, TypeVar

from direct.showbase.DirectObject import DirectObject

if TYPE_CHECKING:
  from engine.game import Game
  from engine.scene import Scene

N = TypeVar('N', bound='Node')


class Node:
  """
  Form the scene hierarchy: a node owns its children, which are updated and destroyed along with it.

  Subclasses react to the lifecycle through on_ready(), on_update(dt), and on_destroy() instead of overriding
  update() and destroy(), which the engine calls on the scene root and propagates down the tree.
  """
  @property
  def game(self) -> Game:
    """
    Get the game providing shared runtime services.

    Raises:
      RuntimeError: If the node has not entered a scene yet.
    """
    if self._game is None:
      raise RuntimeError(f'{type(self).__name__} must be added to a scene before using the game.')

    return self._game

  @property
  def parent(self) -> Node | None:
    """
    Get the node this one was added to, or None for a scene root.
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

    # Bind runtime events, such as the mouse wheel, so destruction removes only this node's bindings.
    self._listener = DirectObject()

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

  def accept(self, event: str, callback: Callable[..., Any], *args: Any) -> None:
    """
    Listen for a runtime event, such as 'wheel_up', until the node is destroyed.

    Args:
      event (str): Panda3D event name.
      callback (Callable[..., Any]): Function called when the event fires.
      args (Any): Extra arguments passed to the callback.
    """
    self._listener.accept(event, callback, list(args))

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

    # Release event subscriptions and runtime bindings so nothing calls into a destroyed node.
    if self._game is not None:
      self._game.events.release(self)

    self._listener.ignoreAll()
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
      game (Game): Game owning the tree the node is entering.
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
    Attach engine resources once the node enters the tree; nodes without resources do nothing.
    """

  def _unmount(self) -> None:
    """
    Release engine resources when the node is destroyed; nodes without resources do nothing.
    """
