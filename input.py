from __future__ import annotations

from direct.showbase.ShowBase import ShowBase
from panda3d.core import ButtonHandle, ButtonRegistry


class Input:
  """
  Answer which keyboard and mouse buttons are held in the current frame.
  """
  def __init__(self, context: ShowBase) -> None:
    """
    Store the runtime whose window receives the input.

    Args:
      context (ShowBase): Runtime that owns the window and its mouse watcher.
    """
    self._context = context

  def is_down(self, key: str) -> bool:
    """
    Check whether a button is held.

    Args:
      key (str): Panda3D button name, such as 'w', 'space', 'shift', or 'mouse1'.

    Returns:
      bool: Whether the button is held; always False while there is no window or the name is unknown.
    """
    # The watcher only exists while a window is open.
    watcher = self._context.mouseWatcherNode
    if watcher is None:
      return False

    button = ButtonRegistry.ptr().findButton(key)
    return button != ButtonHandle.none() and watcher.isButtonDown(button)

  def axis(self, negative: str, positive: str) -> int:
    """
    Combine two opposing buttons into one axis, so holding both cancels out.

    Args:
      negative (str): Button that pushes the axis toward -1.
      positive (str): Button that pushes the axis toward +1.

    Returns:
      int: -1, 0, or 1.
    """
    return int(self.is_down(positive)) - int(self.is_down(negative))
