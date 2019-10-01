""""Module that handles the kickoffs"""
from rlutilities.mechanics import Dodge, AerialTurn
from rlutilities.linear_algebra import *

import math

from util import get_closest_small_pad, sign, distance_2d, lerp
from steps import Step
from custom_drive import CustomDrive as Drive


def init_kickoff(agent):
    """"Method that initializes the kickoff"""
    if abs(agent.info.my_car.location[0]) < 250:
        pad = get_closest_small_pad(agent, vec3(0, sign(agent.team) * 4608, 18))
        target = vec3(pad.location[0], pad.location[1], pad.location[2]) + sign(agent.team) * vec3(20, 0, 0)
        agent.kickoffStart = "Center"
    elif abs(agent.info.my_car.location[0]) < 1000:
        target = vec3(0.0, sign(agent.team) * 2816.0, 70.0) + sign(agent.team) * vec3(0, 300, 0)
        agent.kickoffStart = "offCenter"
    else:
        target = agent.info.my_car.location + 300 * agent.info.my_car.forward()
        agent.kickoffStart = "Diagonal"
    agent.drive = Drive(agent.info.my_car)
    agent.drive.target = target
    agent.drive.speed = 2400
    agent.step = Step.Drive
    agent.drive.step(agent.fps)
    agent.controls = agent.drive.controls


def kick_off(agent):
    ball = agent.info.ball
    car = agent.info.my_car
    t = distance_2d(ball.location, car.location) / 2200
    batmobile_resting = 18.65
    robbies_constant = (ball.location - vec3(0, 0,
                                                        92.75 - batmobile_resting) - car.location - car.velocity * t) * 2 * t ** -2
    robbies_boost_constant = dot(normalize(xy(car.forward())), normalize(xy(robbies_constant))) > (
                0.3 if car.on_ground else 0.1)
    """"Module that performs the kickoffs"""
    if agent.kickoffStart == "Diagonal":
        if agent.step is Step.Drive:
            agent.drive.step(agent.fps)
            agent.controls = agent.drive.controls
            if agent.drive.finished:
                ball_location = ball.location + vec3(0, -sign(agent.team) * 500, 0)
                target = car.location + 250 * normalize(ball_location - car.location)
                agent.drive = Drive(car)
                agent.drive.target = target
                agent.drive.speed = 2400
                agent.step = Step.Drive_1
        if agent.step is Step.Drive_1:
            agent.drive.step(agent.fps)
            agent.controls = agent.drive.controls
            if agent.drive.finished:
                target = vec3(dot(rotation(math.radians(-sign(agent.info.team) * sign(car.location[0]) * 60)),
                                  vec2(car.forward())) * 10000)
                preorientation = dot(
                    axis_to_rotation(vec3(0, 0, math.radians(-sign(agent.info.team) * -sign(car.location[0]) * 30))),
                    car.rotation)
                setup_first_dodge(agent, 0.05, 0.3, target, preorientation)
        elif agent.step is Step.Dodge_1:
            agent.timer += agent.info.time_delta
            if agent.timer > 0.8:
                lerp_var = lerp(normalize(robbies_constant), normalize(
                    ball.location - vec3(0, 0, 92.75 - batmobile_resting) - car.location),
                                0.8)
                agent.turn.target = look_at(lerp_var, vec3(0, 0, 1))
                agent.turn.step(agent.info.time_delta)
                agent.controls = agent.turn.controls
                if car.on_ground:
                    agent.step = Step.Catching
            else:
                agent.dodge.step(agent.info.time_delta)
                agent.controls = agent.dodge.controls
            agent.controls.boost = robbies_boost_constant
    elif agent.kickoffStart == "Center":
        if agent.step is Step.Drive:
            agent.drive.step(agent.info.time_delta)
            agent.controls = agent.drive.controls
            if agent.drive.finished:
                target = vec3(dot(rotation(math.radians(-65)), vec2(car.forward())) * 10000)
                preorientation = dot(axis_to_rotation(vec3(0, 0, math.radians(45))),
                                     car.rotation)
                setup_first_dodge(agent, 0.05, 0.4, target, preorientation)
        elif agent.step is Step.Dodge_1:
            agent.timer += agent.info.time_delta
            if agent.timer > 0.8:
                agent.turn.target = look_at(xy(ball.location - car.location), vec3(0, 0, 1))
                agent.turn.step(agent.info.time_delta)
                agent.controls = agent.turn.controls
                set_steer(agent)
            else:
                agent.dodge.step(agent.info.time_delta)
                agent.controls = agent.dodge.controls
            agent.controls.boost = robbies_boost_constant
        elif agent.step is Step.Steer:
            agent.drive.step(agent.info.time_delta)
            agent.controls = agent.drive.controls
            if distance_2d(car.location, ball.location) < 800:
                agent.step = Step.Dodge_2
                agent.dodge = Dodge(car)
                agent.dodge.duration = 0.075
                agent.dodge.target = ball.location
        elif agent.step is Step.Dodge_2:
            agent.dodge.step(agent.info.time_delta)
            agent.controls = agent.dodge.controls
            if agent.dodge.finished and car.on_ground:
                agent.step = Step.Catching
    elif agent.kickoffStart == "offCenter":
        if agent.step is Step.Drive:
            agent.drive.step(agent.fps)
            agent.controls = agent.drive.controls
            if distance_2d(car.location, agent.drive.target) < 650:
                target = vec3(dot(rotation(math.radians(-sign(agent.info.team) * -sign(car.location[0]) * 100)),
                                  vec2(car.forward())) * 10000)
                preorientation = dot(
                    axis_to_rotation(vec3(0, 0, math.radians(-sign(agent.info.team) * sign(car.location[0]) * 30))),
                    car.rotation)
                setup_first_dodge(agent, 0.05, 0.4, target, preorientation)
        elif agent.step is Step.Dodge_1:
            agent.timer += agent.info.time_delta
            if agent.timer > 0.8:
                lerp_var = lerp(normalize(robbies_constant), normalize(
                    ball.location - vec3(0, 0, 92.75 - batmobile_resting) - car.location),
                                0.25)
                agent.turn.target = look_at(lerp_var, vec3(0, 0, 1))
                agent.turn.step(agent.info.time_delta)
                agent.controls = agent.turn.controls
                set_steer(agent)
            else:
                agent.dodge.step(agent.info.time_delta)
                agent.controls = agent.dodge.controls
            agent.controls.boost = robbies_boost_constant
        elif agent.step is Step.Steer:
            agent.drive.step(agent.fps)
            agent.controls = agent.drive.controls
            if distance_2d(ball.location, car.location) < 800:
                agent.step = Step.Dodge_2
                agent.dodge = Dodge(car)
                agent.dodge.duration = 0.075
                agent.dodge.target = ball.location
        elif agent.step is Step.Dodge_2:
            agent.dodge.step(agent.fps)
            agent.controls = agent.dodge.controls
            if agent.dodge.finished and car.on_ground:
                agent.step = Step.Catching


def set_steer(agent):
    if agent.info.my_car.on_ground:
        agent.step = Step.Steer
        target = agent.info.ball.location
        agent.drive = Drive(agent.info.my_car)
        agent.drive.target = target
        agent.drive.speed = 2400


def setup_first_dodge(agent, duration, delay, target, preorientation):
    agent.dodge = Dodge(agent.info.my_car)
    agent.turn = AerialTurn(agent.info.my_car)
    agent.dodge.duration = duration
    agent.dodge.delay = delay
    agent.dodge.target = target
    agent.dodge.preorientation = preorientation
    agent.timer = 0.0
    agent.step = Step.Dodge_1
