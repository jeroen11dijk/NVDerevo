from rlbot.agents.base_agent import  SimpleControllerState
from Util import *

def calcController(agent, targetObject, targetSpeed):
    location = toLocal(targetObject,agent.deevo)
    controllerState = SimpleControllerState()
    angleToTarget = math.atan2(location.data[1],location.data[0])
    currentSpeed = velocity2D(agent.deevo)
    controllerState.steer = steer(angleToTarget)
    if (angleToTarget > 0.5 * math.pi and agent.onGround and distance2D(agent.deevo, targetObject) > 1500) or agent.halfFlipping:
        agent.controller = SimpleControllerState()
        halfFlip(agent)
        #render(agent, str(math.degrees(agent.deevo.rotation.data[0])) + " the current pitch is " + str(agent.controller.pitch) + "the degrees of roll " + str(math.degrees(agent.deevo.rotation.data[2])) +  " the current roll is " + str(agent.controller.roll))
        return agent.controller
    if targetSpeed > currentSpeed:
        controllerState.throttle = 1.0
        if targetSpeed > 1400 and currentSpeed < 2250:
            controllerState.boost = True
    elif targetSpeed < currentSpeed:
        controllerState.throttle = -1.0
    return controllerState

def normalKickOff(agent):
    agent.controller = SimpleControllerState()
    if distance2D(agent.deevo, agent.ball) < 750 or agent.dodging:
        dodge(agent, future(agent.ball))
        return agent.controller
    else:
        agent.controller = calcController
        return agent.controller(agent,agent.ball,5000)
