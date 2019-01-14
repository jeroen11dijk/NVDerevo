from RLUtilities.Maneuvers import Drive, AirDodge

from boost import grab_boost
from catching import catching, start_catching
from defending import defending
from dribble import dribble
from shadowDefence import shadow
from shooting import shooting, start_shooting, can_shoot
from util import get_closest_pad, can_dodge, get_speed, get_ballchase_speed, powerslide


def controls(agent):
    if agent.step == "Ballchasing":
        ballChase(agent)
    elif agent.step == "Dodge":
        agent.dodge.step(1 / 60)
        agent.controls = agent.dodge.controls
        agent.controls.boost = 0
        if agent.dodge.finished and agent.info.my_car.on_ground:
            agent.step = "Ballchasing"
    elif agent.step == "Shadowing":
        shadow(agent)
    elif agent.step == "Catching":
        catching(agent)
    elif agent.step == "Defending":
        defending(agent)
    elif agent.step == "Shooting":
        shooting(agent)
    elif agent.step == "Grabbing Boost":
        grab_boost(agent)
    elif agent.step == "Recovery":
        agent.recovery.step(1 / 60)
        agent.controls = agent.recovery.controls
        if agent.info.my_car.on_ground:
            agent.step = "Ballchasing"
    elif agent.step == "Dribbling":
        dribble(agent)
    else:
        agent.step = "Ballchasing"


def ballChase(agent):
    agent.drive.target_speed = get_ballchase_speed(agent, agent.info.ball.pos)
    agent.drive.target_pos = agent.info.ball.pos
    agent.drive.step(1 / 60)
    agent.controls = agent.drive.controls
    powerslide(agent)
    if can_dodge(agent, agent.info.ball.pos) and not can_shoot(agent):
        agent.step = "Dodge"
        agent.dodge = AirDodge(agent.info.my_car, 0.1, agent.info.ball.pos)
    elif agent.defending:
        agent.step = "Defending"
    elif agent.inFrontOfBall:
        agent.step = "Shadowing"
    elif agent.info.ball.pos[2] > 350:
        start_catching(agent)
    elif not agent.info.my_car.on_ground:
        agent.step = "Recovery"
    elif can_shoot(agent):
        start_shooting(agent)
    elif agent.boostGrabs:
        agent.step = "Grabbing Boost"
        target = get_closest_pad(agent).pos
        agent.drive = Drive(agent.info.my_car, target, get_speed(agent, target))
