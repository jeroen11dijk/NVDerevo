from RLUtilities.Maneuvers import Drive

from util import speedController, isReachable, distance2D


def catching(agent):
    agent.drive.step(1 / 60)
    agent.controls = agent.drive.controls
    speedController(agent, agent.drive.target_pos)
    if bounceChanged(agent):
        startCatching(agent)
    if agent.eta - agent.time < 0 or agent.drive.finished:
        agent.step = "Ballchasing"


def startCatching(agent):
    for i in range(len(agent.bounces)):
        location = agent.bounces[i][0]
        bounceTime = agent.bounces[i][1]
        if location[2] < 100 and isReachable(agent, location, bounceTime):
            agent.eta = agent.time + bounceTime / 60
            agent.drive = Drive(agent.info.my_car, location, 1399)
            agent.step = "Catching"
            return


def bounceChanged(agent):
    target = agent.drive.target_pos
    for i in range(len(agent.bounces)):
        if distance2D(target, agent.bounces[i][0]) < 1:
            return False
    return True
