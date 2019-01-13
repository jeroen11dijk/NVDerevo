from shooting import start_shooting, can_shoot
from util import get_closest_pad, distance_2d, get_speed, powerslide


def grab_boost(agent):
    agent.drive.step(1 / 60)
    agent.controls = agent.drive.controls
    powerslide(agent)
    agent.drive.target_speed = get_speed(agent, agent.drive.target_pos)
    if agent.info.my_car.boost > 90 or not get_closest_pad(agent).is_active or agent.defending:
        agent.step = "Defending"
    # elif agent.info.ball.pos[2] > 350:
    #     start_catching(agent)
    elif can_shoot(agent):
        start_shooting(agent)


def boost_grabbing_available(agent, ball):
    pad = get_closest_pad(agent)
    distance = distance_2d(agent.info.my_car.pos, pad.pos)
    future_in_front_of_ball = distance_2d(ball.pos, agent.info.my_goal.center) < distance_2d(agent.info.my_car.pos,
                                                                                             agent.info.my_goal.center)
    should_go = distance < 1500 and agent.info.my_car.boost < 34 and pad.is_active
    can_go = not agent.inFrontOfBall and not future_in_front_of_ball
    if should_go and can_go:
        return True
    return False
