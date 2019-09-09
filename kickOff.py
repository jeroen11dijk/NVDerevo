from rlutilities.linear_algebra import vec3
from rlutilities.mechanics import Dodge, Drive
from util import get_closest_small_pad, sign, distance_2d


def init_kickoff(agent):
    if abs(agent.info.my_car.location[0]) < 250:
        pad = get_closest_small_pad(agent)
        target = vec3(pad.location[0], pad.location[1], pad.location[2]) - sign(agent.team) * vec3(0, 500, 0)
        agent.drive = Drive(agent.info.my_car)
        agent.drive.target = target
        agent.drive.speed = 2400
        agent.kickoffStart = "Center"
    elif abs(agent.info.my_car.location[0]) < 1000:
        target = agent.info.ball.location
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
    agent.drive.step(agent.FPS)
    agent.controls = agent.drive.controls


def kickOff(agent):
    if agent.kickoffStart == "Diagonal":
        if agent.step == "Drive":
            agent.drive.step(agent.FPS)
            agent.controls = agent.drive.controls
            if distance_2d(agent.info.ball.location, agent.info.my_car.location) < 850:
                agent.step = "Dodge"
                agent.dodge = Dodge(agent.info.my_car)
                agent.dodge.duration = 0.075
                agent.dodge.target = agent.info.ball.location
        elif agent.step == "Dodge":
            agent.dodge.step(agent.FPS)
            agent.controls = agent.dodge.controls
            if agent.dodge.finished and agent.info.my_car.on_ground:
                agent.step = "Catching"
    elif agent.kickoffStart == "Center":
        if agent.step == "Drive":
            agent.drive.step(agent.FPS)
            agent.controls = agent.drive.controls
            if agent.drive.finished:
                agent.step = "Dodge1"
                agent.dodge = Dodge(agent.info.my_car)
                agent.dodge.duration = 0.075
                agent.dodge.target = agent.info.ball.location
        elif agent.step == "Dodge1":
            agent.dodge.step(agent.FPS)
            agent.controls = agent.dodge.controls
            agent.controls.boost = 0
            if agent.dodge.finished and agent.info.my_car.on_ground:
                agent.step = "Steer"
                target = agent.info.ball.location + sign(agent.team) * vec3(0, 850, 0)
                agent.drive = Drive(agent.info.my_car)
                agent.drive.target = target
                agent.drive.speed = 2400
        elif agent.step == "Steer":
            agent.drive.step(agent.FPS)
            agent.controls = agent.drive.controls
            if agent.drive.finished:
                agent.step = "Dodge2"
                agent.dodge = Dodge(agent.info.my_car)
                agent.dodge.duration = 0.075
                agent.dodge.target = agent.info.ball.location
        elif agent.step == "Dodge2":
            agent.dodge.step(agent.FPS)
            agent.controls = agent.dodge.controls
            if agent.dodge.finished and agent.info.my_car.on_ground:
                agent.step = "Catching"
    elif agent.kickoffStart == "offCenter":
        if agent.step == "Drive":
            agent.drive.step(agent.FPS)
            agent.controls = agent.drive.controls
            if agent.info.my_car.boost < 15 or agent.drive.finished:
                agent.step = "Dodge1"
                agent.dodge = Dodge(agent.info.my_car)
                agent.dodge.duration = 0.075
                agent.dodge.target = agent.info.ball.location
        elif agent.step == "Dodge1":
            agent.dodge.step(agent.FPS)
            agent.controls = agent.dodge.controls
            agent.controls.boost = 0
            if agent.dodge.finished and agent.info.my_car.on_ground:
                agent.step = "Steer"
                target = agent.info.ball.location
                agent.drive = Drive(agent.info.my_car)
                agent.drive.target = target
                agent.drive.speed = 2400
        elif agent.step == "Steer":
            agent.drive.step(agent.FPS)
            agent.controls = agent.drive.controls
            if distance_2d(agent.info.ball.location, agent.info.my_car.location) < 850:
                agent.step = "Dodge2"
                agent.dodge = Dodge(agent.info.my_car)
                agent.dodge.duration = 0.075
                agent.dodge.target = agent.info.ball.location
        elif agent.step == "Dodge2":
            agent.dodge.step(agent.FPS)
            agent.controls = agent.dodge.controls
            if agent.dodge.finished and agent.info.my_car.on_ground:
                agent.step = "Catching"
