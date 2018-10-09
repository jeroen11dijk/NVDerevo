import math
import time
from Util import *
from Controllers import *
from rlbot.agents.base_agent import  SimpleControllerState

class kickOff:
    def __init__(self):
        self.expired = False
    def __str__(self):
        return "Kickoff"

    def execute(self, agent):
        if not agent.kickoff and not agent.dodging:
            self.expired = True
        agent.controller = normalKickOff
        return agent.controller(agent)

class boostManager:
    def __init__(self):
        self.expired = False
    def __str__(self):
        return "BOOST"

    def available(self,agent):
        pad = getClosestPad(agent)
        distance = distance2D(agent.deevo, pad)
        if distance < 1500 and agent.deevo.boost < 34 and boostAvailable(agent, pad):
            return True
        return False

    def execute(self, agent):
        agent.controller = calcController
        targetLocation = getClosestPad(agent)
        targetLocal = toLocal(targetLocation,agent.deevo)
        angleToTarget = math.atan2(targetLocal.data[1], targetLocal.data[0])
        distanceToTarget = distance2D(agent.deevo, targetLocation)
        speed = 2000 - (100*(1+angleToTarget)**2)
        if (agent.deevo.boost > 90 or not(boostAvailable(agent, targetLocation)) or time.time() - agent.startGrabbingBoost > 2) and not agent.dodging and not agent.halfFlipping:
            self.expired = True

        return agent.controller(agent, targetLocation, speed)

class defending:
    def __init__(self):
        self.expired = False
    def __str__(self):
        return "Defending"

    def execute(self,agent):
        agent.controller = calcController
        centerGoal = agent.ourGoal
        futureBall = future(agent.ball)
        goalToBall = (futureBall - centerGoal)
        targetVector = Vector3([3/4 * goalToBall.data[0], 3/4 * goalToBall.data[1], 0])
        targetLocation = centerGoal + targetVector
        targetLocal = toLocal(targetLocation,agent.deevo)
        angleToTarget = math.atan2(targetLocal.data[1], targetLocal.data[0])
        distanceToTarget = distance2D(agent.deevo, targetLocation)
        speed = 2000 - (100*(1+angleToTarget)**2)
        if (calcShot().available(agent) or boostManager().available(agent)) and not agent.dodging and not agent.halfFlipping:
            self.expired = True
        return agent.controller(agent,targetLocation,speed)


class recovery:
    def __init__(self):
        self.expired = False
    def __str__(self):
        return "Recovering"

    def available(self,agent):
        if not agent.onGround and not agent.dodging:
            return True
        return False

    def execute(self,agent):
        agent.controller = recoveryController
        ball = agent.ball.location
        if agent.onGround:
            self.expired = True
        return agent.controller(agent,ball)

class calcShot:
    def __init__(self):
        self.expired = False
    def __str__(self):
        return "Shooting"

    def available(self,agent):
        if (ballReady(agent) and ballProject(agent) > 500 - (distance2D(agent.ball,agent.deevo)/2)) or distance2D(agent.ball, agent.ourGoal) < 3000:
            return True
        return False

    def execute(self,agent):
        agent.controller = calcController
        leftPost = agent.theirGoalPosts[0]
        rightPost = agent.theirGoalPosts[1]
        center = agent.theirGoal
        futureBall = agent.ball.location
        # futureBall = future(agent.ball)

        ballLeft = angle2D(futureBall, leftPost)
        ballRight = angle2D(futureBall, rightPost)
        agentLeft = angle2D(agent.deevo, leftPost)
        agentRight = angle2D(agent.deevo, rightPost)

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
            goalToBall = (futureBall - target).normalize()
            goalToAgent = (agent.deevo.location - target).normalize()
            difference = goalToBall - goalToAgent
            error = cap(abs(difference.data[0]) + abs(difference.data[1]),1,10)
        else:
            goalToBall = (agent.deevo.location - agent.ball.location).normalize()
            error = cap( distance2D(futureBall,agent.deevo) /1000,0,1)

        #this is measuring how fast the ball is traveling away from us if we were stationary
        ball_dpp_skew = cap(abs(dpp(agent.ball.location, agent.ball.velocity, agent.deevo.location, [0,0,0]))/80, 1,1.5)

        #same as Gosling's old distance calculation, but now we consider dpp_skew which helps us handle when the ball is moving
        targetDistance = cap((40 + distance2D(futureBall,agent.deevo)*(error**2))/1.8, 0,4000)
        targetLocation = futureBall + Vector3([(goalToBall.data[0]*targetDistance) * ball_dpp_skew, goalToBall.data[1]*targetDistance,0])

        #this also adjusts the target location based on dpp
        ballSomething = dpp(targetLocation,agent.ball.velocity, agent.deevo,[0,0,0])**2

        if ballSomething > 100: #if we were stopped, and the ball is moving 100uu/s away from us
            ballSomething = cap(ballSomething,0,80)
            correction = agent.ball.velocity.normalize()
            correction = Vector3([correction.data[0]*ballSomething,correction.data[1]*ballSomething,correction.data[2]*ballSomething])
            targetLocation += correction #we're adding some component of the ball's velocity to the target position so that we are able to hit a faster moving ball better
            #it's important that this only happens when the ball is moving away from us.

        #another target adjustment that applies if the ball is close to the wall
        extra = 4120 - abs(targetLocation.data[0])
        if extra < 0:
            # we prevent our target from going outside the wall, and extend it so that Gosling gets closer to the wall before taking a shot, makes things more reliable
            targetLocation.data[0] = cap(targetLocation.data[0],-4120,4120)
            targetLocation.data[1] = targetLocation.data[1] + (-sign(agent.team)*cap(extra,-500,500))

        targetLocal = toLocal(targetLocation, agent.deevo)
        angleToTarget = math.atan2(targetLocal.data[1], targetLocal.data[0])
        distanceToTarget = distance2D(agent.deevo, targetLocation)
        speed = 2000 - (100*(1+angleToTarget)**2)
        if (not ballReady(agent) or recovery().available(agent)) and not agent.dodging and not agent.halfFlipping:
            self.expired = True

        return agent.controller(agent,targetLocation,speed)
