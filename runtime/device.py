from __future__ import annotations

from collections.abc import Callable
from typing import Any

from direct.showbase.DirectObject import DirectObject
from direct.showbase.ShowBase import ShowBase
from panda3d.core import ButtonHandle, ButtonRegistry


class Device:
  """
  Read the raw keyboard and mouse: buttons held this frame and one-off events such as the mouse wheel.
  """
  def __init__(self, base: ShowBase) -> None:
    """
    Store the runtime whose window receives the input.

    Args:
      base (ShowBase): Runtime that owns the window and its mouse watcher.
    """
    self._base = base

    # One binding object per owner, so releasing an owner removes only its bindings.
    self._bindings: dict[int, DirectObject] = {}

  def is_down(self, key: str) -> bool:
    """
    Check whether a button is held.

    Args:
      key (str): Panda3D button name, such as 'w', 'space', 'shift', or 'mouse1'.

    Returns:
      bool: Whether the button is held; always False while there is no window or the name is unknown.
    """
    # The watcher only exists while a window is open.
    watcher = self._base.mouseWatcherNode
    if watcher is None:
      return False

    button = ButtonRegistry.ptr().findButton(key)
    return button != ButtonHandle.none() and watcher.isButtonDown(button)

  def bind(self, owner: object, event: str, callback: Callable[..., Any], *args: Any) -> None:
    """
    Call a function whenever a device event fires, until the owner is released.

    Args:
      owner (object): Object the binding belongs to.
      event (str): Panda3D event name, such as 'wheel_up'.
      callback (Callable[..., Any]): Function called when the event fires.
      args (Any): Extra arguments passed to the callback.
    """
    self._bindings.setdefault(id(owner), DirectObject()).accept(event, callback, list(args))

  def release(self, owner: object) -> None:
    """
    Remove every binding of an owner.

    Args:
      owner (object): Object whose bindings are removed.
    """
    bindings = self._bindings.pop(id(owner), None)

    if bindings is not None:
      bindings.ignoreAll()
