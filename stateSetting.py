import random
import math
from rlbot.utils.game_state_util import Vector3, Rotator, CarState, GameState, BallState, Physics
from util import sign
from RLUtilities.LinearAlgebra import vec3


def set_kickoff(agent):
    their_goal = agent.info.their_goal.center - sign(agent.team) * vec3(0, 400, 0)
    ball_state = BallState(Physics(location=Vector3(their_goal[0], their_goal[1], their_goal[2])))
    game_state = GameState(ball=ball_state)
    agent.set_game_state(game_state)


def shot_taking(agent):
    car_pos = Vector3(0, -2500, 25)
    ball_pos = Vector3(random.uniform(-1000, 1000), random.uniform(0, 1500), 100)
    ball_state = BallState(Physics(location=ball_pos, velocity=Vector3(0, 550, 0)))
    car_state = CarState(boost_amount=87, physics=Physics(location=car_pos, rotation=Rotator(0, math.pi / 2, 0)))
    their_goal = agent.info.their_goal.center
    enemy_car = CarState(physics=Physics(location=Vector3(their_goal[0], their_goal[1], 25)))
    game_state = GameState(ball=ball_state, cars={agent.index: car_state, (1-agent.index): enemy_car})
    agent.set_game_state(game_state)


def defending(agent):
    car_pos = Vector3(0, 2500, 25)
    ball_pos = Vector3(random.uniform(-200, 200), random.uniform(0, -1500), 100)
    ball_state = BallState(Physics(location=ball_pos, velocity=Vector3(0, -550, 0)))
    car_state = CarState(boost_amount=87, physics=Physics(location=car_pos, rotation=Rotator(0, -math.pi / 2, 0)))
    enemy_car = CarState(physics=Physics(location=Vector3(10000, 10000, 10000)))
    game_state = GameState(ball=ball_state, cars={agent.index: car_state, (1-agent.index): enemy_car})
    agent.set_game_state(game_state)


def dribbling(agent):
    car_pos = Vector3(random.uniform(-3500, 3500), random.uniform(0, -4000), 25)
    ball_pos = Vector3(car_pos.x, car_pos.y + 500, 500)
    ball_state = BallState(Physics(location=ball_pos, velocity=Vector3(0, 0, 500)))
    car_state = CarState(boost_amount=87, physics=Physics(location=car_pos, rotation=Rotator(0, math.pi / 2, 0)))
    game_state = GameState(ball=ball_state, cars={agent.index: car_state})
    agent.set_game_state(game_state)
