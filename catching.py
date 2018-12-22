from RLUtilities.Maneuvers import Drive

from util import velocity_2d, is_reachable, distance_2d


def catching(agent):
    agent.drive.step(1 / 60)
    agent.controls = agent.drive.controls
    catching_speed(agent, agent.drive.target_pos)
    if agent.defending:
        agent.step = "Defending"
    if bounce_changed(agent):
        start_catching(agent)
    if distance_2d(agent.info.my_car.pos, agent.drive.target_pos) < 200:
        agent.step = "Dribbling"
    if agent.drive.finished or agent.eta - agent.time < 0:
        agent.drive = Drive(agent.info.my_car, agent.info.ball.pos, 1399)
        agent.step = "Ballchasing"


def start_catching(agent):
    for i in range(len(agent.bounces)):
        location = agent.bounces[i][0]
        bounceTime = agent.bounces[i][1]
        if location[2] < 100 and is_reachable(agent, location, bounceTime):
            agent.eta = agent.time + bounceTime / 60
            agent.drive = Drive(agent.info.my_car, location, 1399)
            agent.step = "Catching"
            return
    agent.drive = Drive(agent.info.my_car, agent.info.ball.pos, 1399)
    agent.step = "Ballchasing"


def bounce_changed(agent):
    target = agent.drive.target_pos
    for i in range(len(agent.bounces)):
        if distance_2d(target, agent.bounces[i][0]) < 1:
            return False
    return True


def catching_speed(agent, location):
    distance = distance_2d(agent.info.my_car.pos, location)

    alpha = 1.3
    time_left = agent.eta - agent.time
    avg_vf = distance / time_left
    target_vf = (1.0 - alpha) * velocity_2d(agent.info.my_car.vel) + alpha * avg_vf

    if velocity_2d(agent.info.my_car.vel) < target_vf:
        agent.controls.throttle = 1.0
        if target_vf > 1399:
            agent.controls.boost = 1
        else:
            agent.controls.boost = 0
    else:
        if velocity_2d(agent.info.my_car.vel) - target_vf > 75:
            agent.controls.throttle = -1.0
        else:
            agent.controls.throttle = 0.0
