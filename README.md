# pyengine

3D game engine in Python built on Panda3D. Node-tree scenes, 2D physics with colliders and rigidbodies (mass, impulse, restitution), an event system, and hot reload that swaps code without losing game state.

## Requirements

- Python 3.10+
- [panda3d](https://pypi.org/project/panda3d/) and [watchfiles](https://pypi.org/project/watchfiles/) (hot reload)

```bash
uv sync          # or: pip install panda3d watchfiles
uv run main.py   # opens the default scene
```

## Using it in a game

The engine is meant to live inside the game's repository as a git submodule named `engine/`, so its modules import as `engine.*`:

```bash
git submodule add https://github.com/lanelouise/pyengine.git engine
```

```
my-game/
├── engine/          # this repository (submodule)
├── main.py          # tells the engine which scene to open
├── resources/       # the game's models and textures
└── src/
    └── arena/       # a scene: a Python package
        └── __init__.py
```

The game's `main.py` only names its first scene:

```python
from engine import run

run('src/arena', title='My game')
```

Clone a game that uses it with `git clone --recurse-submodules`, or run `git submodule update --init` after a plain clone. Changes made inside `engine/` are committed and pushed from that folder, to this repository; the game's repository then records which engine commit it uses (`git add engine`).

### `run(scene_path, **config)`

Opens the window, builds the scene, and runs frames until the window closes.

- `scene_path`: directory of the scene's Python package. A relative path starts at the entry script's directory, so the game runs the same from any working directory. The directory's parent is put on `sys.path`, so the scene imports its own modules by name (`from arena.player.player import Player`).
- The package's `__init__.py` must define exactly one `Scene` subclass, which is the scene that opens.
- Settings: `title` (window title), `size` (`(width, height)` in pixels), and `reload` (`True` by default) to apply edits to the scene's sources while the game runs. Any other setting raises `TypeError`.

## Layout

```
engine/
├── __init__.py      # run()
├── main.py          # opens scenes/default, to try the engine on its own
├── runtime/         # what keeps the program running; games never import it
│   ├── app.py       # window, frame loop, scene switching
│   ├── device.py    # raw keyboard and mouse
│   ├── loader.py    # models from disk
│   ├── renderer.py  # scene graphs and camera
│   ├── time.py      # frame timing
│   └── reloader.py  # hot reload
├── core/            # what games import but do not put in the tree
│   ├── node.py      # Node, Node3D, Scene
│   ├── game.py      # the services reached through self.game
│   ├── events.py    # self.game.events
│   ├── input.py     # self.game.input
│   ├── physics.py   # self.game.physics
│   └── transform.py
├── objects/         # ready-made nodes games put in the tree
│   ├── camera.py
│   ├── terrain.py
│   ├── collider.py  # CircleCollider
│   └── rigidbody.py # RigidBody
└── scenes/
    └── default/     # minimal scene: ground, a turning box, a camera
```

Each layer only looks down: `runtime` ← `core` ← `objects` ← the game.

## Nodes

Everything in a scene is a `Node`. A node owns its children: they are updated and destroyed along with it, so nobody calls `update()` or `destroy()` by hand. React to the lifecycle by overriding the hooks:

- `on_ready()`: once, when the node enters the tree. `self.game` is available from here on.
- `on_update(dt)`: every frame, after the children have updated.
- `on_destroy()`: once, after the children were destroyed.

`Node3D` adds a place in the 3D scene graph: a `root` (Panda3D `NodePath`) that holds its models and a `transform`. `Scene` is the `Node3D` at the root of the tree; build the tree in its `on_ready()`.

Behaviors are plain child nodes that act on `self.parent`:

```python
from engine.core.node import Node, Node3D, Scene
from engine.objects.camera import Camera
from engine.objects.collider import CircleCollider
from engine.objects.rigidbody import RigidBody


class Spin(Node):
  def on_update(self, dt: float) -> None:
    root = self.parent.root
    root.setH(root.getH() + 90 * dt)


class Crate(Node3D):
  def on_ready(self) -> None:
    self.game.loader.model('models/box').reparentTo(self.root)
    self.add(RigidBody(mass=2.0, drag=4.0))
    self.add(CircleCollider(radius=0.5, layer='crate'))
    self.add(Spin())


class Level(Scene):
  def on_ready(self) -> None:
    self.add(Camera(distance=10.0))
    self.add(Crate())
```

## Services: `self.game`

- `events`: `on(name, callback)`, `off(name, callback)`, `emit(name, **data)`. Event names are plain strings such as `'player.dashed'`. Subscriptions made by a node's bound methods are removed when the node is destroyed, and emitting an event nobody listens to warns while debugging.
- `input`: `is_down(key)`, `axis(negative, positive)`, and `on(event, callback)` for device events such as `'wheel_up'`.
- `physics`: steps the rigidbodies and colliders (see below); `touching(collider)` lists what a collider overlaps.
- `loader`: `model(path)` loads a model, relative to the project root.
- `renderer`: the 3D root, the camera, its lens, and the 2D overlay.

Use a direct call when one node controls another (a player moving the camera), and an event when a node only reacts to something (a camera shake when the player dashes).

## Physics

Physics is 2D on the ground plane, which suits top-down games.

- `CircleCollider(radius, layer)`: the shape. On its own it is a static obstacle that blocks others but is never pushed.
- `RigidBody(mass, drag, restitution, kinematic)`: a sibling of the collider that gives the node a `velocity`. Move bodies by setting their velocity or calling `apply_impulse()`, not by moving the transform, so the solver knows how fast they go.
- `kinematic=True`: the body moves only by its own code; it pushes others and is never pushed.

Every frame, before the tree updates, the physics moves each body by its velocity (fading it by its drag), separates overlapping shapes by their masses, and applies the collision impulse, so a heavy body sends a light one flying without any game code. When two shapes start touching it emits `'collision.started'` with `a`, `b`, and their relative `velocity`, for damage, sounds, or particles.

## Hot reload

While the game runs, saving a file of the scene's package re-executes that module and updates its classes and functions in place: live objects keep their state and run the new code. Limits:

- Fields added to `__init__` or work added to `on_ready()` only reach objects created afterwards.
- Changing a class's base classes rebuilds the scene, losing its state.
- Changes to the engine itself need a restart.

## Default scene

`python main.py` in this repository opens `scenes/default`: a lit ground, a turning box, and a camera, using only the engine and the models that ship with Panda3D. It is the place to check that the engine works without a game.
