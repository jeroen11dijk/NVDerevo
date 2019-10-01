from rlbot.agents.base_agent import SimpleControllerState
from rlutilities.linear_algebra import vec3, dot, look_at
from rlutilities.mechanics import AerialTurn

from util import sign, cap

class HalfFlip:
    
    def __init__(self, car):
        self.timer = 0
        self.car = car
        self.direction = vec3(car.forward() * -1)
        self.target = self.direction * 1000 + self.car.location
        self.aerial_turn = AerialTurn(car)
        self.aerial_turn.target = look_at(self.direction, vec3(0, 0, 1))
        self.controls = SimpleControllerState()
        self.finished = False


    def step(self, dt: float):
        self.controls = SimpleControllerState()
        
        if self.timer < 0.7:
            self.controls.jump = True
            if 0.075 < self.timer < 0.1:
                self.controls.jump = False
            #self.controls.pitch = (-1 if self.car.double_jumped else 1)
            self.controls.pitch = (-1 if self.timer > 0.3 else 1)
            self.controls.roll = 0
            self.controls.yaw = 0
        elif self.car.on_ground or self.timer > 1.8:
            self.finished = True
        else:
            self.aerial_turn.step(dt)
            self.controls = self.aerial_turn.controls
            self.controls.boost = (dot(self.car.forward(), self.direction) > 0.7)

        self.timer += dt
