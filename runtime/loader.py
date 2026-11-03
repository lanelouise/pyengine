from __future__ import annotations

from typing import cast

from direct.showbase.ShowBase import ShowBase
from panda3d.core import NodePath


class Loader:
  """
  Load assets from disk through the runtime.
  """
  def __init__(self, base: ShowBase) -> None:
    """
    Use the runtime's asset loader, which caches what it has read.

    Args:
      base (ShowBase): Runtime providing the loader.
    """
    self._loader = base.loader

  def model(self, path: str) -> NodePath:
    """
    Load a model.

    Args:
      path (str): Model path relative to the project root, such as 'resources/objects/cat/cat.bam'.

    Returns:
      NodePath: Detached copy of the model.

    Raises:
      OSError: If the model cannot be found or read.
    """
    return cast(NodePath, self._loader.loadModel(path))
