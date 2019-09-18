""""Module that handles the kickoffs"""
from rlutilities.linear_algebra import *
from rlutilities.mechanics import Dodge, Drive, AerialTurn

import math

from util import get_closest_small_pad, sign, distance_2d, lerp


def init_kickoff(agent):
    """"Method that initializes the kickoff"""
    if abs(agent.info.my_car.location[0]) < 250:
        pad = get_closest_small_pad(agent, vec3(0, sign(agent.team) * 4608, 18))
        target = vec3(pad.location[0], pad.location[1], pad.location[2])
        agent.drive = Drive(agent.info.my_car)
        agent.drive.target = target
        agent.drive.speed = 2400
        agent.kickoffStart = "Center"
    elif abs(agent.info.my_car.location[0]) < 1000:
        target = vec3(0.0, sign(agent.team) * 2816.0, 70.0) + -sign(agent.team) * vec3(0, 250, 0)
        agent.drive = Drive(agent.info.my_car)
        agent.drive.target = target
        agent.drive.speed = 2400
        agent.kickoffStart = "offCenter"
    else:
        target = agent.info.ball.location
        agent.drive = Drive(agent.info.my_car)
        agent.drive.target = target
        agent.drive.speed = 2400
        agent.kickoffStart = "Diagonal"
    agent.step = "Drive"
    agent.drive.step(agent.fps)
    agent.controls = agent.drive.controls


def kick_off(agent):
    """"Module that performs the kickoffs"""
    if agent.kickoffStart == "Diagonal":
        if agent.step == "Drive":
            agent.drive.step(agent.fps)
            agent.controls = agent.drive.controls
            if distance_2d(agent.info.ball.location, agent.info.my_car.location) < 500:
                agent.step = "Dodge"
                agent.dodge = Dodge(agent.info.my_car)
                agent.dodge.duration = 0.075
                agent.dodge.target = agent.info.ball.location
        elif agent.step == "Dodge":
            agent.dodge.step(agent.fps)
            agent.controls = agent.dodge.controls
            if agent.dodge.finished and agent.info.my_car.on_ground:
                agent.step = "Catching"
    elif agent.kickoffStart == "Center":
        if agent.step == "Drive":
            agent.drive.step(agent.info.time_delta)
            agent.controls = agent.drive.controls
            if agent.drive.finished:
                agent.dodge = Dodge(agent.info.my_car)
                agent.turn = AerialTurn(agent.info.my_car)
                agent.dodge.duration = 0.05
                agent.dodge.delay = 0.4
                agent.dodge.target = vec3(dot(rotation(math.radians(-65)), vec2(agent.info.my_car.forward())) * 10000)
                agent.dodge.preorientation = dot(axis_to_rotation(vec3(0, 0, math.radians(45))),
                                                agent.info.my_car.rotation)
                agent.timer = 0.0
                agent.step = "Dodge1"
        elif agent.step == "Dodge1":
            agent.timer += agent.info.time_delta
            if agent.timer > 0.8:
                agent.turn.target = look_at(xy(agent.info.ball.location - agent.info.my_car.location), vec3(0, 0, 1))
                agent.turn.step(agent.info.time_delta)
                agent.controls = agent.turn.controls
                agent.controls.boost = 0
                if agent.info.my_car.on_ground:
                    agent.step = "Steer"
                    target = agent.info.ball.location
                    agent.drive = Drive(agent.info.my_car)
                    agent.drive.target = target
                    agent.drive.speed = 2400
            else:
                agent.dodge.step(agent.info.time_delta)
                agent.controls = agent.dodge.controls
                agent.controls.boost = 1
            robbies_constant = (agent.info.ball.location - agent.info.my_car.location - agent.info.my_car.velocity)
            agent.controls.boost = dot(normalize(xy(agent.info.my_car.forward())), normalize(xy(robbies_constant))) > (0.3 if agent.info.my_car.on_ground else 0.1)
        elif agent.step == "Steer":
            agent.drive.step(agent.info.time_delta)
            agent.controls = agent.drive.controls
            if distance_2d(agent.info.my_car.location, agent.info.ball.location) < 800:
                agent.step = "Dodge2"
                agent.dodge = Dodge(agent.info.my_car)
                agent.dodge.duration = 0.075
                agent.dodge.target = agent.info.ball.location
        elif agent.step == "Dodge2":
            agent.dodge.step(agent.info.time_delta)
            agent.controls = agent.dodge.controls
    elif agent.kickoffStart == "offCenter":
        if agent.step == "Drive":
            agent.drive.step(agent.fps)
            agent.controls = agent.drive.controls
            if distance_2d(agent.info.my_car.location, agent.drive.target) < 600:
                agent.dodge = Dodge(agent.info.my_car)
                agent.turn = AerialTurn(agent.info.my_car)
                agent.dodge.duration = 0.05
                agent.dodge.delay = 0.4
                agent.dodge.target = vec3(dot(rotation(math.radians(-sign(agent.info.my_car.location[0]) * 45)), vec2(agent.info.my_car.forward())) * 10000)
                agent.dodge.preorientation = dot(axis_to_rotation(vec3(0, 0, math.radians(sign(agent.info.my_car.location[0]) * 30))), agent.info.my_car.rotation)
                agent.timer = 0.0
                agent.step = "Dodge1"
        elif agent.step == "Dodge1":
            agent.timer += agent.info.time_delta
            if agent.timer > 0.8:
                t = distance_2d(agent.info.ball.location, agent.info.my_car.location) / 2200
                robbies_constant = (agent.info.ball.location - agent.info.my_car.location - agent.info.my_car.velocity * t) * 2 * t ** -2
                lerp_var = lerp(normalize(robbies_constant), normalize(agent.info.ball.location - agent.info.my_car.location), 0.25)
                agent.turn.target = look_at(lerp_var, vec3(0, 0, 1))
                # agent.turn.target = look_at(xy(agent.info.ball.location - agent.info.my_car.location), vec3(0, 0, 1))
                agent.turn.step(agent.info.time_delta)
                agent.controls = agent.turn.controls
                # agent.controls.pitch = 0
                agent.controls.roll = 0
                if agent.info.my_car.on_ground:
                    agent.step = "Steer"
                    target = agent.info.ball.location
                    agent.drive = Drive(agent.info.my_car)
                    agent.drive.target = target
                    agent.drive.speed = 2400
            else:
                agent.dodge.step(agent.info.time_delta)
                agent.controls = agent.dodge.controls
            robbies_constant = (agent.info.ball.location - agent.info.my_car.location - agent.info.my_car.velocity)
            agent.controls.boost = dot(normalize(xy(agent.info.my_car.forward())), normalize(xy(robbies_constant))) > (0.3 if agent.info.my_car.on_ground else 0.1)
        elif agent.step == "Steer":
            agent.drive.step(agent.fps)
            agent.controls = agent.drive.controls
            if distance_2d(agent.info.ball.location, agent.info.my_car.location) < 850:
                agent.step = "Dodge2"
                agent.dodge = Dodge(agent.info.my_car)
                agent.dodge.duration = 0.075
                agent.dodge.target = agent.info.ball.location
        elif agent.step == "Dodge2":
            agent.dodge.step(agent.fps)
            agent.controls = agent.dodge.controls
            if agent.dodge.finished and agent.info.my_car.on_ground:
                agent.step = "Catching"
