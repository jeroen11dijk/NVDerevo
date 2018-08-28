import math, time

GOAL_WIDTH = 1784
FIELD_LENGTH = 10240
FIELD_WIDTH = 8192

class Vector3:
    def __init__(self, data):
        self.data = data
    def __add__(self,value):
        return Vector3([self.data[0]+value.data[0],self.data[1]+value.data[1],self.data[2]+value.data[2]])
    def __sub__(self,value):
        return Vector3([self.data[0]-value.data[0],self.data[1]-value.data[1],self.data[2]-value.data[2]])
    def __mul__(self,value):
        return (self.data[0]*value.data[0] + self.data[1]*value.data[1] + self.data[2]*value.data[2])
    def __str__(self):
        return str(self.data)
    def length(self):
        return math.sqrt(self*self)
    def normalize(self):
        length = self.length()
        return Vector3([self.data[0]/length,self.data[1]/length,self.data[2]/length])

class obj:
    def __init__(self):
        self.location = Vector3([0,0,0])
        self.velocity = Vector3([0,0,0])
        self.rotation = Vector3([0,0,0])
        self.rotationVelocity = Vector3([0,0,0])

        self.localLocation = Vector3([0,0,0])
        self.boost = 0

def abc(a,b,c):
    inside = (b**2) - (4*a*c)
    if inside < 0 or a == 0:
        return 0.1
    else:
        n = ((-b - math.sqrt(inside))/(2*a))
        p = ((-b + math.sqrt(inside))/(2*a))
        if p > n:
            return p
        return n

def future(ball):
    time = timeZ(ball)
    x = ball.location.data[0] + (ball.velocity.data[0] * time)
    y = ball.location.data[1] + (ball.velocity.data[1] * time)
    z = ball.location.data[2] + (ball.velocity.data[2] * time)
    return Vector3([x,y,z])

def timeZ(ball):
    rate = 0.97
    return abc(-325, ball.velocity.data[2] * rate, ball.location.data[2]-92.75)

def to_local(targetObject, ourObject):
    x = (toLocation(targetObject) - ourObject.location) * ourObject.matrix[0]
    y = (toLocation(targetObject) - ourObject.location) * ourObject.matrix[1]
    z = (toLocation(targetObject) - ourObject.location) * ourObject.matrix[2]
    return Vector3([x,y,z])

def getBigBoostPads(self):
    res = []
    for i in range(self.fieldInfo.num_boosts):
        current = self.fieldInfo.boost_pads[i]
        if current.is_full_boost:
            newVector = convertVector3(current.location)
            res.append(newVector)
    return res

def boostAvailable(agent, pad):
    index = -1
    for i in range(agent.fieldInfo.num_boosts):
        if distance2D(convertVector3(agent.fieldInfo.boost_pads[i].location),pad) < 1:
            index = i
    return agent.boosts[index].is_active

def getTheirGoalPosts(self):
    res = []
    for i in range(len(self.fieldInfo.goals)):
        current = self.fieldInfo.goals[i]
        if(sign(current.team_num) == -sign(self.team)):
            leftPost = Vector3([-sign(self.team)*GOAL_WIDTH/2, current.location.y, current.location.z])
            rightPost = Vector3([sign(self.team)*GOAL_WIDTH/2, current.location.y, current.location.z])
            res.append(leftPost)
            res.append(rightPost)
    return res

def getOurGoal(self):
    for i in range(len(self.fieldInfo.goals)):
        current = self.fieldInfo.goals[i]
        if(sign(current.team_num) == sign(self.team)):
            return convertVector3(current.location)

def getTheirGoal(self):
    for i in range(len(self.fieldInfo.goals)):
        current = self.fieldInfo.goals[i]
        if(sign(current.team_num) != sign(self.team)):
            return convertVector3(current.location)

def rotator_to_matrix(ourObject):
    r = ourObject.rotation.data
    CR = math.cos(r[2])
    SR = math.sin(r[2])
    CP = math.cos(r[0])
    SP = math.sin(r[0])
    CY = math.cos(r[1])
    SY = math.sin(r[1])

    matrix = []
    matrix.append(Vector3([CP*CY, CP*SY, SP]))
    matrix.append(Vector3([CY*SP*SR-CR*SY, SY*SP*SR+CR*CY, -CP * SR]))
    matrix.append(Vector3([-CR*CY*SP-SR*SY, -CR*SY*SP+SR*CY, CP*CR]))
    return matrix

def sign(x):
    if x <= 0:
        return -1
    else:
        return 1

def convertVector3(vector):
    return Vector3([vector.x, vector.y, vector.z])

def getClosestPad(agent):
    pads = agent.bigBoostPads
    closestPad = None
    distToClosestPad = math.inf
    for i in range(len(pads)):
        if(distance2D(agent.deevo, pads[i]) < distToClosestPad):
            distToClosestPad = distance2D(agent.deevo, pads[i])
            closestPad = pads[i]
    return closestPad

def angle2D(targetLocation, objectLocation):
    difference = toLocation(targetLocation) - toLocation(objectLocation)
    return math.atan2(difference.data[1], difference.data[0])

def velocity2D(targetObject):
    return math.sqrt(targetObject.velocity.data[0]**2 + targetObject.velocity.data[1]**2)

def toLocal(target, ourObject):
    if isinstance(target, obj):
        return target.localLocation
    else:
        return to_local(target, ourObject)

def ballReady(agent):
    ball = agent.ball
    if abs(ball.velocity.data[2]) < 100 and ball.location.data[2] < 250:
        if abs(ball.location.data[1]) < 5000:
            return True
    return False

def ballProject(agent):
    goal = agent.theirGoal
    goalToBall = (agent.ball.location - goal).normalize()
    diff = agent.deevo.location - agent.ball.location
    return diff * goalToBall

def cap(x, low, high):
    if x < low:
        return low
    elif x > high:
        return high
    else:
        return x

def steer(angle):
    final = ((9 * angle + sign(angle))**3) / 20
    return cap(final,-1,1)

def toLocation(target):
    if isinstance(target, Vector3):
        return target
    elif isinstance(target, list):
        return Vector3(target)
    else:
        return target.location

def distance2D(targetObject, ourObject):
    difference = toLocation(targetObject) - toLocation(ourObject)
    return math.sqrt(difference.data[0]**2 + difference.data[1]**2)

def dodge(self, target=None):
    timeDifference = time.time() - self.startDodgeTime
    self.controller.pitch = -1
    self.controller.jump = True
    if target != None:
        location = toLocal(target, self.deevo)
        angleToBall = math.atan2(location.data[1],location.data[0])
        self.controller.yaw = steer(angleToBall)
    if not self.dodging and self.onGround:
        self.dodging = True
        self.startDodgeTime = time.time()
    elif timeDifference > 0.1:
        if self.onGround or timeDifference > 1:
            self.dodging = False
            self.kickOffHasDodged = True
    else:
        self.controller.jump = False
