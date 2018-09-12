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
        speedCorrection =  ((1+ abs(angleToTarget)**2) * 300)
        speed = 1399 - speedCorrection + cap((distanceToTarget/16)**2,0,speedCorrection)
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
        speedCorrection =  ((1+ abs(angleToTarget)**2) * 300)
        speed = 2300 - speedCorrection + cap((distanceToTarget/16)**2,0,speedCorrection)
        if (calcShot().available(agent) or boostManager().available(agent)) and not agent.dodging and not agent.halfFlipping:
            self.expired = True
        return agent.controller(agent,targetLocation,speed)

class calcShot:
    def __init__(self):
        self.expired = False
    def __str__(self):
        return "Shooting"

    def available(self,agent):
        if (ballReady(agent) and ballProject(agent) > 500) or distance2D(agent.ball, agent.ourGoal) < 3000:
            return True
        return False

    def execute(self,agent):
        agent.controller = calcController
        centerGoal = agent.theirGoal
        futureBall = future(agent.ball)
        goalToBall = (futureBall - centerGoal).normalize()
        goalToAgent = (agent.deevo.location - centerGoal).normalize()
        difference = goalToBall - goalToAgent
        error = cap(abs(difference.data[0]) + abs(difference.data[1]),1,10)

        targetDistance = (100 + distance2D(futureBall, agent.deevo) * (error**2))/ 1.95
        targetLocation = futureBall + Vector3([goalToBall.data[0]*targetDistance,goalToBall.data[1]*targetDistance, 0])
        targetLocal = toLocal(targetLocation, agent.deevo)
        angleToTarget = math.atan2(targetLocal.data[1], targetLocal.data[0])
        distanceToTarget = distance2D(agent.deevo, targetLocation)
        speedCorrection =  ((1+ abs(angleToTarget)**2) * 300)
        speed = 2300 - speedCorrection + cap((distanceToTarget/16)**2,0,speedCorrection)
        if ballProject(agent) < 10 and not agent.dodging and not agent.halfFlipping:
            self.expired = True

        return agent.controller(agent,targetLocation,speed)
