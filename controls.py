from RLUtilities.Maneuvers import Drive

from boost import grabBoost, boost_grabbing_speed
from catching import catching, start_catching
from defending import defending
from dribble import aim
from shadowDefence import shadow
from shooting import shooting, start_shooting, can_shoot
from util import get_closest_pad


def controls(agent):
    if agent.step == "Ballchasing":
        ballChase(agent)
    elif agent.step == "Catching":
        catching(agent)
    elif agent.step == "Defending":
        defending(agent)
    elif agent.step == "Shooting":
        shooting(agent)
    elif agent.step == "Grabbing Boost":
        grabBoost(agent)
    elif agent.step == "Shadowing":
        shadow(agent)
    elif agent.step == "Dribbling":
        agent.controls = aim(agent)
        if agent.conceding:
            agent.step = "Defending"
        if agent.info.ball.pos[2] < 95:
            start_shooting(agent)
    else:
        agent.step = "Ballchasing"


def ballChase(agent):
    if agent.drive.target_speed != 1399:
        agent.drive.target_speed = 1399
    agent.drive.target_pos = agent.info.ball.pos
    agent.drive.step(1 / 60)
    agent.controls = agent.drive.controls
    if agent.conceding:
        agent.step = "Defending"
    elif agent.inFrontOfBall:
        agent.step = "Shadowing"
    elif agent.info.ball.pos[2] > 500:
        start_catching(agent)
    elif can_shoot(agent):
        start_shooting(agent)
    elif agent.boostGrabs:
        agent.step = "Grabbing Boost"
        target = get_closest_pad(agent).pos
        agent.drive = Drive(agent.info.my_car, target, boost_grabbing_speed(agent, target))
