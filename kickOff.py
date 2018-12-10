from RLUtilities.LinearAlgebra import vec3
from RLUtilities.Maneuvers import Drive, AirDodge

from ab0t import BaseAgent
from util import getClosestSmallPad, sign, distance2D


def initKickOff(agent: BaseAgent):
    if abs(agent.info.my_car.pos[0]) < 250:
        pad = getClosestSmallPad(agent)
        target = vec3(pad.location.x, pad.location.y, pad.location.z) - sign(agent.team) * vec3(0, 500, 0)
        agent.drive = Drive(agent.info.my_car, target, 2400)
        agent.kickoffStart = "Center"
    elif abs(agent.info.my_car.pos[0]) < 1000:
        # pad = getClosestSmallPad(agent)
        # target = vec3(pad.location.x, pad.location.y, pad.location.z)
        target = agent.info.ball.pos
        agent.drive = Drive(agent.info.my_car, target, 2400)
        agent.kickoffStart = "offCenter"
    else:
        pad = getClosestSmallPad(agent)
        vec3Pad = vec3(pad.location.x, pad.location.y, pad.location.z)
        carToPad = vec3Pad - agent.info.my_car.pos
        target = agent.info.my_car.pos + 1.425 * carToPad
        agent.drive = Drive(agent.info.my_car, target, 2300)
        agent.kickoffStart = "Diagonal"
    agent.step = "Drive"
    agent.drive.step(1 / 60)
    agent.controls = agent.drive.controls


def kickOff(agent: BaseAgent):
    if agent.kickoffStart == "Diagonal":
        if agent.step == "Drive":
            agent.drive.step(1 / 60)
            agent.controls = agent.drive.controls
            if agent.drive.finished:
                agent.step = "Dodge1"
                target = agent.info.ball.pos + sign(agent.team) * vec3(0, 150, 0)
                agent.dodge = AirDodge(agent.info.my_car, 0.035, target)
        elif agent.step == "Dodge1":
            agent.dodge.step(1 / 60)
            agent.controls = agent.dodge.controls
            agent.controls.boost = 0
            if agent.dodge.finished:
                agent.step = "Steer"
                target = agent.info.ball.pos
                agent.drive = Drive(agent.info.my_car, target, 1399)
        elif agent.step == "Steer":
            agent.drive.step(1 / 60)
            agent.controls = agent.drive.controls
            if agent.info.my_car.on_ground:
                agent.drive.target_speed = 2400
            if distance2D(agent.info.ball.pos, agent.info.my_car.pos) < 600:
                agent.step = "Dodge2"
                agent.dodge = AirDodge(agent.info.my_car, 0.1, agent.info.ball.pos)
        elif agent.step == "Dodge2":
            agent.dodge.step(1 / 60)
            agent.controls = agent.dodge.controls
            if agent.dodge.finished:
                agent.step = "Ballchasing"
    elif agent.kickoffStart == "Center":
        if agent.step == "Drive":
            agent.drive.step(1 / 60)
            agent.controls = agent.drive.controls
            if agent.drive.finished:
                agent.step = "Dodge1"
                agent.dodge = AirDodge(agent.info.my_car, 0.075, agent.info.ball.pos)
        elif agent.step == "Dodge1":
            agent.dodge.step(1 / 60)
            agent.controls = agent.dodge.controls
            agent.controls.boost = 0
            if agent.dodge.finished and agent.info.my_car.on_ground:
                agent.step = "Steer"
                target = agent.info.ball.pos + sign(agent.team) * vec3(0, 850, 0)
                agent.drive = Drive(agent.info.my_car, target, 2400)
        elif agent.step == "Steer":
            agent.drive.step(1 / 60)
            agent.controls = agent.drive.controls
            if agent.drive.finished:
                agent.step = "Dodge2"
                agent.dodge = AirDodge(agent.info.my_car, 0.075, agent.info.ball.pos)
        elif agent.step == "Dodge2":
            agent.dodge.step(1 / 60)
            agent.controls = agent.dodge.controls
            if agent.dodge.finished:
                agent.step = "Ballchasing"
    elif agent.kickoffStart == "offCenter":
        if agent.step == "Drive":
            agent.drive.step(1 / 60)
            agent.controls = agent.drive.controls
            if agent.info.my_car.boost < 15 or agent.drive.finished:
                agent.step = "Dodge1"
                agent.dodge = AirDodge(agent.info.my_car, 0.075, agent.info.ball.pos)
        elif agent.step == "Dodge1":
            agent.dodge.step(1 / 60)
            agent.controls = agent.dodge.controls
            agent.controls.boost = 0
            if agent.dodge.finished and agent.info.my_car.on_ground:
                agent.step = "Steer"
                target = agent.info.ball.pos
                agent.drive = Drive(agent.info.my_car, target, 2400)
        elif agent.step == "Steer":
            agent.drive.step(1 / 60)
            agent.controls = agent.drive.controls
            if distance2D(agent.info.ball.pos, agent.info.my_car.pos) < 850:
                agent.step = "Dodge2"
                agent.dodge = AirDodge(agent.info.my_car, 0.075, agent.info.ball.pos)
        elif agent.step == "Dodge2":
            agent.dodge.step(1 / 60)
            agent.controls = agent.dodge.controls
            if agent.dodge.finished:
                agent.step = "Ballchasing"
