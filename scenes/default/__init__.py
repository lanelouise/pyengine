from __future__ import annotations

from panda3d.core import AmbientLight, CardMaker, DirectionalLight, Vec3, Vec4

from engine.core.node import Node3D, Scene
from engine.objects.camera import Camera
from engine.objects.terrain import Terrain


class Spinner(Node3D):
  """
  Show a box that turns in place, proving that models load and nodes update every frame.
  """
  def __init__(self, speed: float = 45.0) -> None:
    """
    Create the box.

    Args:
      speed (float): Turning speed, in degrees per second.
    """
    super().__init__()
    self._speed = speed

  def on_ready(self) -> None:
    """
    Load the box that ships with Panda3D and center it on the node.
    """
    model = self.game.loader.model('models/box')
    model.setPos(-0.5, -0.5, 0)
    model.setColor(0.95, 0.55, 0.2, 1)
    model.reparentTo(self.root)

  def on_update(self, dt: float) -> None:
    """
    Turn the box around the vertical axis.

    Args:
      dt (float): Elapsed time since the previous frame, in seconds.
    """
    self.root.setH(self.root.getH() + self._speed * dt)


class Default(Scene):
  """
  Minimal scene the engine opens on its own: a lit ground, a turning box, and a camera framing them.
  """
  def on_ready(self) -> None:
    """
    Build the camera, the ground, the box, and the lights.
    """
    self.add(Camera(distance=8.0, rotation=Vec3(30, -30, 0)))

    # A flat card covers the terrain's ground, since the engine has no tiles of its own.
    terrain = self.add(Terrain())
    card = CardMaker('ground')
    card.setFrame(-5, 5, -5, 5)
    ground = terrain.root.attachNewNode(card.generate())
    ground.setP(-90)
    ground.setColor(0.35, 0.6, 0.35, 1)

    self.add(Spinner())

    # Light the scene so the box's faces can be told apart.
    ambient = AmbientLight('ambient')
    ambient.setColor(Vec4(0.4, 0.4, 0.4, 1))
    sun = DirectionalLight('sun')
    sun.setColor(Vec4(0.8, 0.8, 0.8, 1))
    sun_path = self.root.attachNewNode(sun)
    sun_path.setHpr(30, -60, 0)
    self.root.setLight(self.root.attachNewNode(ambient))
    self.root.setLight(sun_path)
