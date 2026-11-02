from __future__ import annotations

import warnings
from collections.abc import Callable
from typing import Any


class Events:
  """
  Deliver named events from publishers to listeners that do not know each other.
  """
  def __init__(self) -> None:
    """
    Start without listeners.
    """
    self._listeners: dict[str, list[Callable[..., Any]]] = {}

  def on(self, name: str, callback: Callable[..., Any]) -> None:
    """
    Subscribe a callback to an event.

    A bound method of a Node is unsubscribed automatically when that node is destroyed.

    Args:
      name (str): Event name, such as 'player.dashed'.
      callback (Callable[..., Any]): Function receiving the event data as keyword arguments.
    """
    listeners = self._listeners.setdefault(name, [])

    # Subscribing twice must not deliver the same event twice.
    if callback not in listeners:
      listeners.append(callback)

  def off(self, name: str, callback: Callable[..., Any]) -> None:
    """
    Unsubscribe a callback from an event, if it is subscribed.

    Args:
      name (str): Event name used when subscribing.
      callback (Callable[..., Any]): Function previously passed to on().
    """
    listeners = self._listeners.get(name)

    if listeners is not None and callback in listeners:
      listeners.remove(callback)

  def emit(self, name: str, **data: Any) -> None:
    """
    Deliver an event to every current listener.

    Args:
      name (str): Event name.
      data (Any): Event data passed to each listener as keyword arguments.
    """
    # Copy the listeners so a callback may subscribe or unsubscribe while the event is delivered.
    listeners = tuple(self._listeners.get(name, ()))

    # A misspelled name would otherwise fail silently, so warn while debugging.
    if not listeners and __debug__:
      warnings.warn(f"Event '{name}' has no listeners.", stacklevel=2)

    for callback in listeners:
      callback(**data)

  def release(self, owner: object) -> None:
    """
    Unsubscribe every bound method of an object from all events.

    Args:
      owner (object): Object whose bound methods are removed, usually a destroyed node.
    """
    for listeners in self._listeners.values():
      listeners[:] = [callback for callback in listeners if getattr(callback, '__self__', None) is not owner]
