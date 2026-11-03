from __future__ import annotations

from panda3d.core import ClockObject


class Time:
  """
  Report frame timing from the runtime's shared clock.
  """
  @property
  def dt(self) -> float:
    """
    Get the elapsed time since the previous frame, in seconds.
    """
    return self._clock.getDt()

  def __init__(self) -> None:
    """
    Use the clock that the runtime advances once per frame.
    """
    self._clock = ClockObject.getGlobalClock()
