from RLUtilities.LinearAlgebra import vec3
from RLUtilities.Maneuvers import AirDodge

from util import get_speed, distance_2d, get_closest_small_pad, can_dodge, powerslide


def shadow(agent):
    agent.drive.step(1 / 60)
    agent.controls = agent.drive.controls
    powerslide(agent)
    target = shadow_target(agent)
    pad = get_closest_small_pad(agent)
    pad_pos = vec3(pad.pos[0], pad.pos[1], pad.pos[2])
    if distance_2d(pad_pos, target) < 400:
        target = pad_pos
    agent.drive.target_pos = target
    agent.drive.target_speed = get_speed(agent, target)
    if can_dodge(agent, target):
        agent.step = "Dodge"
        agent.dodge = AirDodge(agent.info.my_car, 0.1, target)
    if agent.defending:
        agent.step = "Defending"
    if not agent.inFrontOfBall:
        agent.step = "Ballchasing"


def shadow_target(agent):
    center_goal = agent.info.my_goal.center
    ball = agent.info.ball
    goal_to_ball = ball.pos - center_goal
    target_vector = vec3(2 / 3 * goal_to_ball[0], 2 / 3 * goal_to_ball[1], 0)
    return center_goal + target_vector
