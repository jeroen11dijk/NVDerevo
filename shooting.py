from RLUtilities.LinearAlgebra import vec3, normalize, dot
from RLUtilities.Maneuvers import Drive

from ab0t import BaseAgent
from util import distance2D, speedController, angle2D, cap, sign, isReachable, timeZ, ETACalculator


def shootingAvailable(ball, car, goal):
    if ballReady(ball) and ballProject(ball, car, goal) > 500 - (distance2D(ball.pos, car.pos) / 2):
        return True
    return False


def shooting(agent: BaseAgent):
    agent.drive.step(1 / 60)
    agent.controls = agent.drive.controls
    target = shootingTarget(agent.target, agent.info.my_car, agent.info.their_goal, agent.team)
    speedController(agent, agent.target)
    agent.drive.target_pos = target
    if agent.inFrontOfBall:
        agent.step = "Shadowing"
    if shotChanged(agent):
        startShooting(agent)
    if agent.eta - agent.time < 0 or agent.drive.finished or agent.inFrontOfBall:
        agent.step = "Ballchasing"


def shootingTarget(ballPos, car, goal, team):
    leftPost = goal.corners[3]
    rightPost = goal.corners[2]
    ballLeft = angle2D(ballPos, leftPost)
    ballRight = angle2D(ballPos, rightPost)
    agentLeft = angle2D(car.pos, leftPost)
    agentRight = angle2D(car.pos, rightPost)

    # determining if we are left/right/inside of cone
    if agentLeft > ballLeft and agentRight > ballRight:
        target = rightPost
    elif agentLeft > ballLeft and agentRight < ballRight:
        target = None
    elif agentLeft < ballLeft and agentRight < ballRight:
        target = leftPost
    else:
        target = None

    if target != None:
        goalToBall = normalize(ballPos - target)
        goalToagent = normalize(car.pos - target)
        difference = goalToBall - goalToagent
        error = cap(abs(difference[0]) + abs(difference[1]), 1, 10)
    else:
        goalToBall = normalize(car.pos - ballPos)
        error = cap(distance2D(ballPos, car.pos) / 1000, 0, 1)

    # same as Gosling's old distance calculation, but now we consider dpp_skew which helps us handle when the ball is moving
    targetDistance = cap((40 + distance2D(ballPos, car.pos) * (error ** 2)) / 1.8, 0, 4000)
    targetLocation = ballPos + vec3((goalToBall[0] * targetDistance), goalToBall[1] * targetDistance, 0)

    # another target adjustment that applies if the ball is close to the wall
    extra = 3850 - abs(targetLocation[0])
    if extra < 0:
        # we prevent our target from going outside the wall, and extend it so that Gosling gets closer to the wall before taking a shot, makes things more reliable
        targetLocation[0] = cap(targetLocation[0], -3850, 3850)
        targetLocation[1] = targetLocation[1] + (-sign(team) * cap(extra, -800, 800))
    return targetLocation


def canShoot(agent: BaseAgent):
    for i in range(len(agent.shots)):
        location = agent.shots[i][0]
        shotTime = agent.shots[i][1]
        ourGoal = agent.info.my_goal.center
        behindTheBall = distance2D(agent.info.ball.pos, ourGoal) > distance2D(agent.info.my_car.pos, ourGoal)
        closer = ETACalculator(agent.info.my_car, location) < ETACalculator(agent.info.opponents[0], location)
        if closer and behindTheBall and isReachable(agent, location, shotTime):
            return True
    return False


def startShooting(agent: BaseAgent):
    for i in range(len(agent.shots)):
        location = agent.shots[i][0]
        shotTime = agent.shots[i][1]
        closer = ETACalculator(agent.info.my_car, location) < ETACalculator(agent.info.opponents[0], location)
        if closer and isReachable(agent, location, shotTime):
            agent.eta = agent.time + shotTime / 60
            agent.target = location
            agent.step = "Shooting"
            target = shootingTarget(agent.target, agent.info.my_car, agent.info.their_goal, agent.team)
            agent.drive = Drive(agent.info.my_car, target, 1399)
            return


def shotChanged(agent: BaseAgent):
    target = agent.target
    ball_prediction = agent.get_ball_prediction_struct()
    for i in range(ball_prediction.num_slices):
        location = vec3(ball_prediction.slices[i].physics.location.x,
                        ball_prediction.slices[i].physics.location.y,
                        ball_prediction.slices[i].physics.location.z)
        if distance2D(target, location) < 1:
            return False
    return True


def ballReady(ball):
    if abs(ball.vel[2]) < 150 and timeZ(ball) < 1:
        return True
    return False


def ballProject(ball, car, goal):
    goalToBall = normalize(ball.pos - goal.center)
    diff = car.pos - ball.pos
    return dot(diff, goalToBall)