import math
import time
from Util import *
from rlbot.agents.base_agent import  SimpleControllerState

class kickOff:
    def __init__(self):
        self.expired = False

    def execute(self, agent):
        if not agent.kickoff:
            self.kickOffHasDodged = False
            self.expired = True
        agent.controller = SimpleControllerState()
        timeDifference = time.time() - agent.kickOffStart
        if timeDifference > 0.75 and not agent.kickOffHasDodged:
            dodge(agent)
            return agent.controller
        elif agent.kickOffHasDodged:
            agent.controller = calcController
            return agent.controller(agent,agent.ball,5000)
        else:
            agent.controller.boost = True
            agent.controller.throttle = 1
            agent.controller.handbrake = False
            agent.controller.steer = 0
            return agent.controller

class boostManager:
    def __init__(self):
        self.expired = False

    def available(self,agent):
        pad = getClosestPad(agent)
        distance = distance2D(agent.deevo, pad)
        if distance < 2500 and agent.deevo.boost < 34 and boostAvailable(agent, pad):
            return True
        return False

    def execute(self, agent):
        agent.controller = calcController
        targetLocation = getClosestPad(agent)
        boostAvailable(agent, targetLocation)
        targetLocal = toLocal(targetLocation,agent.deevo)
        angleToTarget = math.atan2(targetLocal.data[1], targetLocal.data[0])
        distanceToTarget = distance2D(agent.deevo, targetLocation)
        speedCorrection =  ((1+ abs(angleToTarget)**2) * 300)
        speed = 1399 - speedCorrection + cap((distanceToTarget/16)**2,0,speedCorrection)

        if agent.deevo.boost > 90 or not(boostAvailable(agent, targetLocation)):
            self.expired = True

        return agent.controller(agent, targetLocation, speed)

class defending:
    def __init__(self):
        self.expired = False

    def execute(self,agent):
        agent.controller = calcController
        goal = agent.ourGoal
        goalToBall = (agent.ball.location - goal)
        targetVector = Vector3([1/2 * goalToBall.data[0], 1/2 * goalToBall.data[1], 0])
        targetLocation = goal + targetVector
        targetLocation.data[0] = cap(targetLocation.data[0],-4120,4120)
        if sign(agent.team) == 1:
            targetLocation.data[1] = cap(targetLocation.data[1],0, 5100)
        elif sign(agent.team) == -1:
            targetLocation.data[1] = cap(targetLocation.data[1],-5100, 0)

        targetLocal = toLocal(targetLocation,agent.deevo)
        angleToTarget = math.atan2(targetLocal.data[1], targetLocal.data[0])
        distanceToTarget = distance2D(agent.deevo, targetLocation)
        speedCorrection =  ((1+ abs(angleToTarget)**2) * 300)
        speed = 2300 - speedCorrection + cap((distanceToTarget/16)**2,0,speedCorrection)
        self.expired = True

        return agent.controller(agent,targetLocation,speed)

class calcShot:
    def __init__(self):
        self.expired = False

    def available(self,agent):
        if (ballReady(agent) and ballProject(agent) > 500) or distance2D(agent.ball, agent.ourGoal) < 3000:
            return True
        return False

    def execute(self,agent):
        agent.controller = calcController
        goal = agent.theirGoal
        goalToBall = (agent.ball.location - goal).normalize()

        goalToAgent = (agent.deevo.location - goal).normalize()
        difference = goalToBall - goalToAgent
        error = cap(abs(difference.data[0]) + abs(difference.data[1]),1,10)

        targetDistance = (100 +distance2D(agent.ball,agent.deevo) * (error**2) )/ 1.95
        targetLocation = agent.ball.location + Vector3([goalToBall.data[0]*targetDistance,goalToBall.data[1]*targetDistance, 0])
        targetLocation.data[0] = cap(targetLocation.data[0],-4120,4120)

        targetLocal = toLocal(targetLocation,agent.deevo)
        angleToTarget = math.atan2(targetLocal.data[1], targetLocal.data[0])
        distanceToTarget = distance2D(agent.deevo, targetLocation)
        speedCorrection =  ((1+ abs(angleToTarget)**2) * 300)
        speed = 2300 - speedCorrection + cap((distanceToTarget/16)**2,0,speedCorrection)

        if ballProject(agent) < 10:
            self.expired = True

        return agent.controller(agent,targetLocation,speed)

def calcController(agent, targetObject, targetSpeed):
    location = toLocal(targetObject,agent.deevo)
    controllerState = SimpleControllerState()
    angleToBall = math.atan2(location.data[1],location.data[0])

    currentSpeed = velocity2D(agent.deevo)
    controllerState.steer = steer(angleToBall)

    #throttle
    if targetSpeed > currentSpeed:
        controllerState.throttle = 1.0
        if targetSpeed > 1400 and agent.start > 2.2 and currentSpeed < 2250:
            controllerState.boost = True
    elif targetSpeed < currentSpeed:
        controllerState.throttle = -1.0
    return controllerState
