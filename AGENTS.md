# Scope of the engine

This repository is pyengine, a generic engine. It is used by games as a git submodule named `engine/`, so its modules import each other as `engine.*`.

- Keep game concepts out of the engine: no players, enemies, tiles, biomes, camera shake, or any rule of a specific game. The engine offers generic building blocks; games extend them in their own repositories.
- Do not reference any game, its scenes, or its assets. Only `scenes/default/` lives here, and it must use nothing but the engine and the models that ship with Panda3D.
- Respect the layers, each of which only imports from the ones below it:
  - `runtime/`: what keeps the program running (window, frame loop, devices, loading, rendering, hot reload). Games never import it.
  - `core/`: services and base classes games import but do not put in the tree (`Node`, `Node3D`, `Scene`, events, input, physics, transform).
  - `objects/`: ready-made nodes games put in the tree (camera, terrain, colliders, rigid bodies).
- Create a module only when something uses it now; do not anticipate features.
- Update `README.md` whenever a public behavior or API changes.

# Python code conventions

Change this document only when the user explicitly asks. Do not alter these conventions as part of other tasks.

These conventions apply to new, suggested, or changed Python code. Avoid reformatting code unrelated to the task.

## Indentation and organization

- Use exactly two spaces per indentation level in classes, methods, functions, conditionals, loops, and exception handling blocks.
- Do not use tabs or mix indentation styles.
- Organize imports in three groups: standard library, external dependencies, and project modules. Separate the groups with a blank line.
- Use two blank lines between top-level definitions and one between methods.
- Inside classes, place `__init__` before the other methods, when there is one.

```python
from pathlib import Path

from external_library import Client

from project.settings import Settings


class Service:
  """
  Coordinate operations with an external service.
  """
  @property
  def client() -> Client:
    """
    Get the client used to execute requests.
    """
    return self._client

  def __init__(self, client: Client, settings: Settings) -> None:
    """
    Initialize the service dependencies.

    Args:
      client (Client): Client used to execute requests.
      settings (Settings): Configuration for service operations.
    """
    self._client = client
    self._settings = settings

  def execute(self) -> None:
    """
    Execute the configured operation.
    """
    self._client.execute(self._settings.operation)
```

The imports and types in this example are illustrative.

## Function and method signatures

- Write the whole signature on a single line, including the parameters, their type annotations, and the return type.
- Do not split the parameters across several lines. This also applies to constructors, static methods, and class methods.

Use:

```python
def method(self, arg1: str, arg2: int, arg3: bool) -> None:
  ...
```

Do not use:

```python
def method(
  self,
  arg1: str,
  arg2: int,
  arg3: bool,
) -> None:
  ...
```

## Strings

Prefer single quotes (`'`). Use double quotes when they avoid escapes or when a tool requires them.

```python
status = 'pending'
message = "The user's account is active."
```

## Docstrings

- Use triple double quotes (`"""`), with the opening and closing quotes on lines separate from the content.
- Document classes, constructors, functions, and methods with a short description of their responsibility.
- Use `Args:` for relevant parameters, in the format `name (type): description`.
- Use `Returns:` and `Raises:` when they help explain the contract.
- Do not document `self` or repeat information without adding meaning.

```python
def calculate_total(price: float, quantity: int) -> float:
  """
  Calculate the total price for the requested quantity.

  Args:
    price (float): Unit price.
    quantity (int): Number of units, which must be positive.

  Returns:
    float: Total price before taxes.

  Raises:
    ValueError: If the quantity is not positive.
  """
  if quantity <= 0:
    raise ValueError('Quantity must be positive.')

  return price * quantity
```

## Type annotations

Annotate parameters and return values. Use `-> None` when the function returns no value. Annotate attributes and local variables when that clarifies the contract or resolves an ambiguous inference.

```python
class Registry:
  """
  Store unique item names.
  """
  def __init__(self) -> None:
    """
    Initialize an empty registry.
    """
    self._items: set[str] = set()

  def register(self, name: str) -> None:
    """
    Register an item name.

    Args:
      name (str): Name to add to the registry.
    """
    self._items.add(name)
```

Do not call functions in argument defaults, such as `Vec3(0, 0, 0)`; default to `None` and create the value inside the function.

## Logical blocks and comments

- Separate distinct steps with a blank line.
- Introduce business rule blocks with a `#` comment on its own line, right above the block.
- Explain the intent, the rule, or the reason for the decision.
- Avoid comments that merely translate the next statement.
- Do not comment every line; group statements that perform the same step.

```python
def calculate_shipping(subtotal: float, standard_fee: float) -> float:
  """
  Calculate the shipping fee according to the order subtotal.

  Args:
    subtotal (float): Order total before shipping.
    standard_fee (float): Fee applied below the free shipping threshold.

  Returns:
    float: Shipping fee for the order.
  """
  # Orders of at least 100 qualify for free shipping.
  if subtotal >= 100:
    return 0.0

  # Orders below the threshold pay the standard fee.
  return standard_fee
```

Avoid redundant comments:

```python
# Set the status to pending.
status = 'pending'
```

Prefer explaining the rule that determines the value:

```python
# New requests require approval before processing.
status = 'pending'
```

## Language and maintenance

Write comments, docstrings, and documentation in English. Update the documentation whenever the corresponding behavior changes.
