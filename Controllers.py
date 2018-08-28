from rlbot.agents.base_agent import  SimpleControllerState
from Util import *

def calcController(agent, targetObject, targetSpeed):
    location = toLocal(targetObject,agent.deevo)
    controllerState = SimpleControllerState()
    angleToBall = math.atan2(location.data[1],location.data[0])

    currentSpeed = velocity2D(agent.deevo)
    controllerState.steer = steer(angleToBall)
    # TODO
    # if distance2D(agent.deevo, targetObject) < 750:
    #     dodge(agent, targetObject)
    #     return agent.controller
    if targetSpeed > currentSpeed:
        controllerState.throttle = 1.0
        if targetSpeed > 1400 and currentSpeed < 2250:
            controllerState.boost = True
    elif targetSpeed < currentSpeed:
        controllerState.throttle = -1.0
    return controllerState

def diagonalKickoff(agent):
    agent.controller = SimpleControllerState()
    timeDifference = time.time() - agent.kickOffStart
    if (timeDifference > 0.5 and not agent.kickOffHasDodged):
        dodge(agent)
        return agent.controller
    if distance2D(agent.deevo, agent.ball) < 450 or agent.dodging:
        dodge(agent, future(agent.ball))
        return agent.controller
    elif agent.kickOffHasDodged:
        agent.controller = calcController
        return agent.controller(agent,agent.ball,5000)
    else:
        agent.controller.boost = True
        agent.controller.throttle = 1
        return agent.controller

def normalKickOff(agent):
    agent.controller = SimpleControllerState()
    if distance2D(agent.deevo, agent.ball) < 750 or agent.dodging:
        dodge(agent, future(agent.ball))
        return agent.controller
    else:
        agent.controller = calcController
        return agent.controller(agent,agent.ball,5000)
