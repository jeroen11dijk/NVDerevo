from RLUtilities.Maneuvers import Drive

from boost import grabBoost, boostGrabbingSpeed
from shadowDefence import shadow
from shooting import shooting, canShoot, startShooting
from util import getClosestPad


def controls(agent):
    if agent.step == "Ballchasing":
        ballChase(agent)
    # elif agent.step == "Catching":
    #     catching(agent)
    elif agent.step == "Shooting":
        shooting(agent)
    elif agent.step == "Grabbing Boost":
        grabBoost(agent)
    elif agent.step == "Shadowing":
        shadow(agent)
    else:
        agent.step = "Ballchasing"


def ballChase(agent):
    if agent.drive.target_speed != 1399:
        agent.drive.target_speed = 1399
    agent.drive.target_pos = agent.info.ball.pos
    agent.drive.step(1 / 60)
    agent.controls = agent.drive.controls
    if agent.inFrontOfBall:
        agent.step = "Shadowing"
    elif canShoot(agent):
        startShooting(agent)
    # elif agent.info.ball.pos[2] > 500:
    #     startCatching(agent)
    elif agent.boostGrabs:
        agent.step = "Grabbing Boost"
        target = getClosestPad(agent).pos
        agent.drive = Drive(agent.info.my_car, target, boostGrabbingSpeed(agent, target))
