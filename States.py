import math
import time
from Util import *
from RLUtilities.LinearAlgebra import *
from RLUtilities.Maneuvers import *
from rlbot.agents.base_agent import  SimpleControllerState

class kickOff:
    def __init__(self, agent):
        self.expired = False
        agent.action = Drive(agent.info.my_car, agent.info.ball.pos, 2300)
    def __str__(self):
        return "Kickoff"

    def execute(self, agent):
        if not agent.kickoff or (type(agent.action) == AirDodge and agent.info.my_car.on_ground):
            self.expired = True
            agent.action = None
        if distance2D(agent.info.my_car.pos, agent.info.ball.pos) < 750 and type(agent.action) != AirDodge:
            agent.action = AirDodge(agent.info.my_car, 5.0, agent.info.ball.pos)
        agent.action.step(0.016666)
        return convert_input(agent.action.controls)

class boostManager:
    def __init__(self):
        self.expired = False
    def __str__(self):
        return "BOOST"

    def available(self,agent):
        pad = getClosestPad(agent)
        distance = distance2D(agent.info.my_car.pos, pad.pos)
        if distance < 1500 and agent.info.my_car.boost < 34 and pad.is_active:
            return True
        return False

    def execute(self, agent):
        deevo = agent.info.my_car
        pad = getClosestPad(agent)
        targetLocation = pad.pos
        targetLocal = dot(targetLocation - deevo.pos, deevo.theta)
        angleToTarget = math.atan2(targetLocal[1], targetLocal[0])
        distanceToTarget = distance2D(deevo.pos, targetLocation)
        speed = 2000 - (100*(1+angleToTarget)**2)
        if deevo.boost > 90 or not(pad.is_active) or time.time() - agent.startGrabbingBoost > 2:
            self.expired = True
            agent.action = None
        if agent.action is None:
            agent.action = Drive(agent.info.my_car, targetLocation, speed)
        else:
            agent.action.target_pos = targetLocation
            agent.action.target_speed = speed
        agent.action.step(0.016666)
        return convert_input(agent.action.controls)

class defending:
    def __init__(self):
        self.expired = False
    def __str__(self):
        return "Defending"

    def execute(self,agent):
        centerGoal = agent.info.my_goal.center
        ball = agent.info.ball
        deevo = agent.info.my_car
        goalToBall = normalize(ball.pos - centerGoal)
        targetVector = vec3(3/4 * goalToBall[0], 3/4 * goalToBall[1], 0)
        targetLocation = centerGoal + targetVector
        targetLocal = dot(targetLocation - deevo.pos, deevo.theta)
        angleToTarget = math.atan2(targetLocal[1], targetLocal[0])
        distanceToTarget = distance2D(deevo.pos, targetLocation)
        speed = 2000 - (100*(1+angleToTarget)**2)
        if calcShot().available(agent) or boostManager().available(agent):
            self.expired = True
            agent.action = None
        if agent.action is None:
            agent.action = Drive(agent.info.my_car, targetLocation, speed)
        else:
            agent.action.target_pos = targetLocation
            agent.action.target_speed = speed
        agent.action.step(0.016666)
        return convert_input(agent.action.controls)

class calcShot:
    def __init__(self):
        self.expired = False
    def __str__(self):
        return "Shooting"

    def available(self,agent):
        if (ballReady(agent) and ballProject(agent) > 500 - (distance2D(agent.info.ball.pos,agent.info.my_car.pos)/2)) or distance2D(agent.info.ball.pos, agent.info.my_goal.center) < 3000:
            return True
        return False

    def execute(self,agent):
        leftPost = agent.info.their_goal.corners[3]
        rightPost = agent.info.their_goal.corners[2]
        center = agent.info.their_goal.center
        ball = agent.info.ball
        deevo = agent.info.my_car
        ballLeft = angle2D(ball.pos, leftPost)
        ballRight = angle2D(ball.pos, rightPost)
        agentLeft = angle2D(deevo.pos, leftPost)
        agentRight = angle2D(deevo.pos, rightPost)

        #determining if we are left/right/inside of cone
        if agentLeft > ballLeft and agentRight > ballRight:
            target = rightPost
        elif agentLeft > ballLeft and agentRight < ballRight:
            target = None
        elif agentLeft < ballLeft and agentRight < ballRight:
            target = leftPost
        else:
            target = None

        if target != None:
            goalToBall = normalize(ball.pos - target)
            goalToAgent = normalize(deevo.pos- target)
            difference = goalToBall - goalToAgent
            error = cap(abs(difference[0]) + abs(difference[1]),1,10)
        else:
            goalToBall = normalize(deevo.pos - ball.pos)
            error = cap(distance2D(ball.pos, deevo.pos) /1000,0,1)

        #this is measuring how fast the ball is traveling away from us if we were stationary
        ball_dpp_skew = cap(abs(dpp(ball.pos, ball.vel, deevo.pos, vec3(0,0,0)))/80, 1,1.5)

        #same as Gosling's old distance calculation, but now we consider dpp_skew which helps us handle when the ball is moving
        targetDistance = cap((40 + distance2D(ball.pos, deevo.pos)*(error**2))/1.8, 0,4000)
        targetLocation = ball.pos + vec3((goalToBall[0]*targetDistance) * ball_dpp_skew, goalToBall[1]*targetDistance,0)

        #this also adjusts the target location based on dpp
        ballSomething = dpp(targetLocation,ball.vel, deevo.pos,[0,0,0])**2

        if ballSomething > 100: #if we were stopped, and the ball is moving 100uu/s away from us
            ballSomething = cap(ballSomething,0,80)
            correction = normalize(ball.vel)
            correction = vec3(correction[0]*ballSomething,correction[1]*ballSomething,correction[2]*ballSomething)
            targetLocation += correction #we're adding some component of the ball's velocity to the target position so that we are able to hit a faster moving ball better
            #it's important that this only happens when the ball is moving away from us.

        #another target adjustment that applies if the ball is close to the wall
        extra = 4120 - abs(targetLocation[0])
        if extra < 0:
            # we prevent our target from going outside the wall, and extend it so that Gosling gets closer to the wall before taking a shot, makes things more reliable
            targetLocation[0] = cap(targetLocation[0],-4120,4120)
            targetLocation[1] = targetLocation[1] + (-sgn(agent.info.team)*cap(extra,-500,500))

        targetLocal = dot(targetLocation - deevo.pos, deevo.theta)
        angleToTarget = math.atan2(targetLocal[1], targetLocal[0])
        distanceToTarget = distance2D(deevo.pos, targetLocation)
        speed = 2000 - (100*(1+angleToTarget)**2)
        if not ballReady(agent):
            self.expired = True
            agent.action = None
        if agent.action is None:
            agent.action = Drive(agent.info.my_car, targetLocation, speed)
        else:
            agent.action.target_pos = targetLocation
            agent.action.target_speed = speed
        agent.action.step(0.016666)
        return convert_input(agent.action.controls)
