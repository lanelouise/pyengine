from __future__ import annotations

from collections.abc import Callable
from typing import Any

from engine.runtime.device import Device


class Input:
  """
  Answer which buttons are held this frame and deliver device events to nodes.
  """
  def __init__(self, device: Device) -> None:
    """
    Read the raw keyboard and mouse through the runtime device.

    Args:
      device (Device): Raw keyboard and mouse.
    """
    self._device = device

  def is_down(self, key: str) -> bool:
    """
    Check whether a button is held.

    Args:
      key (str): Button name, such as 'w', 'space', 'shift', or 'mouse1'.

    Returns:
      bool: Whether the button is held.
    """
    return self._device.is_down(key)

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

  def on(self, event: str, callback: Callable[..., Any], *args: Any) -> None:
    """
    Call a function whenever a device event fires, such as 'wheel_up'.

    A bound method of a Node stops being called automatically when that node is destroyed.

    Args:
      event (str): Device event name.
      callback (Callable[..., Any]): Function called when the event fires.
      args (Any): Extra arguments passed to the callback.
    """
    self._device.bind(getattr(callback, '__self__', callback), event, callback, *args)

  def release(self, owner: object) -> None:
    """
    Stop delivering device events to every bound method of an object.

    Args:
      owner (object): Object whose bindings are removed, usually a destroyed node.
    """
    self._device.release(owner)
