from rlbot.agents.base_agent import  SimpleControllerState
from Util import *

def calcController(agent, targetObject, targetSpeed):
    location = toLocal(targetObject,agent.deevo)
    controllerState = SimpleControllerState()
    angleToTarget = math.atan2(location.data[1],location.data[0])
    currentSpeed = velocity2D(agent.deevo)
    controllerState.steer = steer(angleToTarget)
    if (angleToTarget > 0.5 * math.pi and agent.onGround and distance2D(agent.deevo, targetObject) > 2000) or agent.halfFlipping:
        agent.controller = SimpleControllerState()
        halfFlip(agent)
        return agent.controller
    if targetSpeed > currentSpeed:
        controllerState.throttle = 1.0
        if targetSpeed > 1400 and currentSpeed < 2250:
            controllerState.boost = True
    elif targetSpeed < currentSpeed:
        controllerState.throttle = -1.0
    return controllerState

def recoveryController(agent, ball):
    controllerState = SimpleControllerState()
    location = toLocal(ball, agent.deevo)
    angleToTarget = math.atan2(location.data[1],location.data[0])
    steering = steer(angleToTarget)
    controllerState.yaw = steering
    roll = math.degrees(agent.deevo.rotation.data[2])
    pitch = math.degrees(agent.deevo.rotation.data[0])
    if roll > 5:
        controllerState.roll = -1
    elif roll < 5:
        controllerState.roll = 1
    else:
        controllerState.roll = 0
    if pitch > 5:
        controllerState.pitch = -1
    elif pitch < 5:
        controllerState.pitch = 1
    else:
        controllerState.pitch = 0
    render(agent, "roll is " + str(math.degrees(agent.deevo.rotation.data[2])) + " roll is " + str(controllerState.roll))
    return controllerState


def normalKickOff(agent):
    agent.controller = SimpleControllerState()
    if distance2D(agent.deevo, agent.ball) < 750 or agent.dodging:
        dodge(agent, future(agent.ball))
        return agent.controller
    else:
        agent.controller = calcController
        return agent.controller(agent,agent.ball,5000)
