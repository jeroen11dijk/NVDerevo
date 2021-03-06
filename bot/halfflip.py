from rlbot.agents.base_agent import SimpleControllerState

from rlutilities.linear_algebra import vec3, dot, look_at
from rlutilities.mechanics import AerialTurn


class HalfFlip:

    def __init__(self, car):
        self.timer = 0
        self.car = car
        self.direction = vec3(car.forward() * -1)
        self.target = self.direction * 1000 + self.car.position
        self.aerial_turn = AerialTurn(car)
        self.aerial_turn.target = look_at(self.direction, vec3(0, 0, 1))
        self.controls = SimpleControllerState()
        self.finished = False

    def step(self, dt: float):
        self.controls = SimpleControllerState()

        self.aerial_turn.step(dt)
        aerial_turn_controls = self.aerial_turn.controls

        if self.timer < 0.7:
            self.controls.jump = True
            if 0.075 < self.timer < 0.1:
                self.controls.jump = False
            self.controls.pitch = (-1 if self.timer > 0.425 else 1)
            self.controls.roll = aerial_turn_controls.roll
        else:
            self.controls = aerial_turn_controls
            if (self.car.on_ground and self.timer > 0.25) or self.timer > 1.1:
                self.finished = True

        self.controls.boost = (dot(self.car.forward(), self.direction) > 0.8)

        self.timer += dt
