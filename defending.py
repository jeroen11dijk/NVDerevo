from RLUtilities.LinearAlgebra import vec3, normalize

from util import angle_2d, distance_2d, cap, sign


def inTheCone(agent):
    ballPos = agent.info.ball.pos
    goal = agent.info.my_goal
    leftPost = goal.corners[3]
    rightPost = goal.corners[2]
    ballLeft = angle_2d(ballPos, leftPost)
    ballRight = angle_2d(ballPos, rightPost)
    agentLeft = angle_2d(agent.info.my_car.pos, leftPost)
    agentRight = angle_2d(agent.info.my_car.pos, rightPost)

    # determining if we are left/right/inside of cone
    if agentLeft > ballLeft and agentRight > ballRight:
        return False
    elif agentLeft > ballLeft and agentRight < ballRight:
        return True
    elif agentLeft < ballLeft and agentRight < ballRight:
        return False
    else:
        return True


def defendingTarget(ballPos, car, goal, team):
    leftPost = goal.corners[3]
    rightPost = goal.corners[2]
    ballLeft = angle_2d(ballPos, leftPost)
    ballRight = angle_2d(ballPos, rightPost)
    agentLeft = angle_2d(car.pos, leftPost)
    agentRight = angle_2d(car.pos, rightPost)

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
        error = cap(distance_2d(ballPos, car.pos) / 1000, 0, 1)

    # same as Gosling's old distance calculation, but now we consider dpp_skew which helps us handle when the ball is moving
    targetDistance = cap((40 + distance_2d(ballPos, car.pos) * (error ** 2)) / 1.8, 0, 4000)
    targetLocation = ballPos + vec3((goalToBall[0] * targetDistance), goalToBall[1] * targetDistance, 0)

    # another target adjustment that applies if the ball is close to the wall
    extra = 3850 - abs(targetLocation[0])
    if extra < 0:
        # we prevent our target from going outside the wall, and extend it so that Gosling gets closer to the wall before taking a shot, makes things more reliable
        targetLocation[0] = cap(targetLocation[0], -3850, 3850)
        targetLocation[1] = targetLocation[1] + (-sign(team) * cap(extra, -800, 800))
    return targetLocation
