from __future__ import annotations

import sys
import traceback
from importlib import invalidate_caches, reload
from pathlib import Path
from threading import Lock, Thread
from types import FunctionType, ModuleType

from watchfiles import PythonFilter, watch

from engine.runtime.app import App

# Methods that run every frame on live objects, so editing them shows without rebuilding the scene.
LIVE = frozenset({'on_update'})


class Reloader:
  """
  Apply edits to the game's Python sources while it runs, keeping the current game state.

  Each edited module is executed again and its classes and functions are updated in place, so live objects keep their
  data and run the new code. Only per-frame code can show this way, so the running scene is rebuilt from the new code
  whenever an edit changes anything else, such as __init__, on_ready, a helper they call, or a constant.
  """
  def __init__(self, app: App, source: str) -> None:
    """
    Start monitoring the source directory for the lifetime of the process.

    Args:
      app (App): App whose running scene is rebuilt when an edit cannot be applied in place.
      source (str): Directory holding the game's Python sources.
    """
    self._app = app
    self._source = Path(source).resolve()

    # Collect edited files until the next frame can apply them.
    self._lock = Lock()
    self._changes: set[Path] = set()

    # Monitor files on a background thread, which never touches application objects.
    Thread(target=self._watch, daemon=True).start()

    # Reload on the main thread, before the scene updates.
    app.schedule(self._dispatch, sort=-200)

  def _dispatch(self) -> None:
    """
    Apply every edit received since the previous frame.
    """
    with self._lock:
      changes, self._changes = self._changes, set()

    if not changes:
      return

    invalidate_caches()

    # A broken edit is reported without closing the game, so the next save can fix it.
    try:
      if not all(self._patch(module) for module in self._modules(changes)):
        self._rebuild()
    except Exception:
      traceback.print_exc()

  def _modules(self, changes: set[Path]) -> list[ModuleType]:
    """
    Find the loaded modules backed by the edited files; files never imported need no reload.

    Args:
      changes (set[Path]): Edited files.

    Returns:
      list[ModuleType]: Modules to execute again.
    """
    modules: list[ModuleType] = []

    for module in tuple(sys.modules.values()):
      file = getattr(module, '__file__', None)
      if file is not None and Path(file).resolve() in changes:
        modules.append(module)

    return modules

  def _patch(self, module: ModuleType) -> bool:
    """
    Execute a module again and move the new definitions into the objects that already exist.

    Args:
      module (ModuleType): Module backed by an edited file.

    Returns:
      bool: Whether every definition could be updated in place, without rebuilding the scene to show the edit.
    """
    # Keep the old definitions, which live objects and other modules still reference.
    previous = dict(module.__dict__)
    reload(module)

    # Constants and functions may be used while objects are built, so a change to them only shows on a rebuilt scene.
    patched = all(self._unchanged(old, module.__dict__.get(name)) for name, old in previous.items() if not name.startswith('__') and not isinstance(old, type))

    for name, old in previous.items():
      new = module.__dict__.get(name)

      # Only definitions made by this module are updated; imported names belong to their own modules.
      if getattr(old, '__module__', None) != module.__name__ or new is None or new is old:
        continue

      if isinstance(old, type) and isinstance(new, type):
        patched = self._patch_class(old, new) and patched
      elif isinstance(old, FunctionType) and isinstance(new, FunctionType):
        self._patch_function(old, new, None)
      else:
        continue

      # Keep a single definition alive, so names imported elsewhere and isinstance() keep agreeing.
      module.__dict__[name] = old

    return patched

  def _patch_class(self, old: type, new: type) -> bool:
    """
    Replace the body of a class with the body of its new definition.

    Args:
      old (type): Class referenced by live objects.
      new (type): Class created by the new execution of its module.

    Returns:
      bool: Whether the edit shows on live objects; a change of base classes or of build-time code needs a rebuilt scene.
    """
    if [base.__qualname__ for base in old.__bases__] != [base.__qualname__ for base in new.__bases__]:
      return False

    # Only per-frame code shows on live objects; any other change may run while objects are built, so it needs a rebuilt scene.
    rebuild = any(not self._unchanged(old.__dict__.get(name), value) for name, value in new.__dict__.items() if name not in LIVE and (name == '__init__' or not name.startswith('__')))

    # Remove what the new definition dropped, then bring in what it defines.
    for name in set(old.__dict__) - set(new.__dict__) - {'__dict__', '__weakref__'}:
      delattr(old, name)

    for name, value in new.__dict__.items():
      if name in ('__dict__', '__weakref__'):
        continue

      current = old.__dict__.get(name)
      if isinstance(current, FunctionType) and isinstance(value, FunctionType):
        self._patch_function(current, value, old)
      else:
        self._retarget(value, old)
        setattr(old, name, value)

    return not rebuild

  @staticmethod
  def _unchanged(old: object, new: object) -> bool:
    """
    Tell whether a module or class value is the same in the new definition, comparing functions by their code.

    Args:
      old (object): Value before the edit.
      new (object): Value after the edit.

    Returns:
      bool: Whether the edit left the value as it was; values that cannot be compared count as unchanged.
    """
    if old is new or isinstance(old, (type, ModuleType)) or isinstance(new, (type, ModuleType)):
      return True

    if isinstance(old, FunctionType) and isinstance(new, FunctionType):
      return old.__code__.co_code == new.__code__.co_code and old.__code__.co_consts == new.__code__.co_consts and old.__code__.co_names == new.__code__.co_names

    # Properties, static methods, and other wrappers hold functions that run when called, not when objects are built.
    if isinstance(old, (property, staticmethod, classmethod)) or isinstance(new, (property, staticmethod, classmethod)):
      return True

    # Values compared only by identity, such as type variables, are created anew by every execution of the module.
    if type(old).__eq__ is object.__eq__:
      return True

    try:
      return bool(old == new)
    except Exception:
      return True

  def _patch_function(self, old: FunctionType, new: FunctionType, owner: type | None) -> None:
    """
    Make an existing function run the code of its new definition.

    Args:
      old (FunctionType): Function referenced by live objects.
      new (FunctionType): Function created by the new execution of its module.
      owner (type | None): Class the function belongs to, if any.
    """
    # Code with a different set of closure variables cannot be swapped into the old function, so replace it instead.
    if old.__code__.co_freevars != new.__code__.co_freevars:
      if owner is not None:
        self._retarget(new, owner)
        setattr(owner, new.__name__, new)
      return

    old.__code__ = new.__code__
    old.__defaults__ = new.__defaults__
    old.__kwdefaults__ = new.__kwdefaults__
    old.__doc__ = new.__doc__

  def _retarget(self, value: object, owner: type) -> None:
    """
    Point the implicit class reference used by super() at the class that is kept.

    Args:
      value (object): Attribute taken from the new class definition.
      owner (type): Class that is kept and receives the attribute.
    """
    # Properties and static or class methods wrap their functions.
    functions = [getattr(value, part, None) for part in ('fget', 'fset', 'fdel', '__func__')] + [value]

    for function in functions:
      if isinstance(function, FunctionType) and '__class__' in function.__code__.co_freevars:
        cell = function.__closure__[function.__code__.co_freevars.index('__class__')]  # type: ignore[index]
        cell.cell_contents = owner

  def _rebuild(self) -> None:
    """
    Recreate the running scene from freshly imported sources, losing its state.
    """
    # Forget every module loaded from the sources, so the next import reads the files again.
    for name, module in tuple(sys.modules.items()):
      file = getattr(module, '__file__', None)
      if file is not None and self._source in Path(file).resolve().parents:
        del sys.modules[name]

    self._app.reload()

  def _watch(self) -> None:
    """
    Collect edited files without touching application objects.
    """
    for changes in watch(self._source, watch_filter=PythonFilter()):
      with self._lock:
        self._changes.update(Path(path).resolve() for _, path in changes)
