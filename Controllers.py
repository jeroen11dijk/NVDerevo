from rlbot.agents.base_agent import  SimpleControllerState
from Util import *

def calcController(agent, targetObject, targetSpeed):
    location = toLocal(targetObject,agent.deevo)
    controllerState = SimpleControllerState()
    angleToBall = math.atan2(location.data[1],location.data[0])

    angleToTarget = math.atan2(location.data[1],location.data[0])
    currentSpeed = velocity2D(agent.deevo)
    controllerState.steer = steer(angleToBall)
    # TODO
    # if distance2D(agent.deevo, targetObject) < 750:
    #     dodge(agent, targetObject)
    #     return agent.controller
    controllerState.steer = steer(angleToTarget)
    if (angleToTarget > 0.5 * math.pi and agent.onGround) or agent.halfFlipping:
        agent.controller = SimpleControllerState()
        halfFlip(agent)
        render(agent, str(math.degrees(agent.deevo.rotation.data[0])) + " the current pitch is " + str(agent.controller.pitch) + "the degrees of roll " + str(math.degrees(agent.deevo.rotation.data[2])) +  " the current roll is " + str(agent.controller.roll))
        return agent.controller
    if targetSpeed > currentSpeed:
        controllerState.throttle = 1.0
        if targetSpeed > 1400 and currentSpeed < 2250:
            controllerState.boost = True
    elif targetSpeed < currentSpeed:
        controllerState.throttle = -1.0
    return controllerState

<<<<<<< HEAD
# def diagonalKickoff(agent):
#     agent.controller = SimpleControllerState()
#     timeDifference = time.time() - agent.kickOffStart
#     if (timeDifference > 0.5 and not agent.kickOffHasDodged):
#         dodge(agent)
#         return agent.controller
#     if distance2D(agent.deevo, agent.ball) < 450 or agent.dodging:
#         dodge(agent, future(agent.ball))
#         return agent.controller
#     elif agent.kickOffHasDodged:
#         agent.controller = calcController
#         return agent.controller(agent,agent.ball,5000)
#     else:
#         agent.controller.boost = True
#         agent.controller.throttle = 1
#         return agent.controller

=======
>>>>>>> af1bbedbd76910e4de5859f447029c5a9f4f6c17
def normalKickOff(agent):
    agent.controller = SimpleControllerState()
    if distance2D(agent.deevo, agent.ball) < 750 or agent.dodging:
        dodge(agent, future(agent.ball))
        return agent.controller
    else:
        agent.controller = calcController
        return agent.controller(agent,agent.ball,5000)
