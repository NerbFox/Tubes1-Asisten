from random import randint
from typing import Optional, List

from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from ..util import get_direction,clamp

def indexValid(x, y: int, width, height):
    return 0 <= x < width and 0 <= y < height

def getStep2Way(currPos, destPos : Position) -> (int,int):
    x_distance = abs(currPos.x - destPos.x)
    y_distance = abs(currPos.y - destPos.y)
    return x_distance, y_distance

class SutaLovesEmyu(BaseLogic):
    def __init__(self):
        self.directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        self.goal_position: Optional[Position] = None
        self.current_direction = 0
        self.bot = None
        self.redButton = None
        self.listOfDiamonds = []
        self.listOfTeleport = []
        self.board_width = 0
        self.board_height = 0
        self.matrix = None
    
    def stepDistance(self, object1: GameObject, object2 : GameObject) -> int:
        x_distance = abs(object1.position.x - object2.position.x)
        y_distance = abs(object1.position.y - object2.position.y)
        distance = x_distance+y_distance
        return distance
    
    def getDistance(self, pos1: Position, pos2: Position) -> int:
        x_distance = abs(pos1.x - pos2.x)
        y_distance = abs(pos1.y - pos2.y)
        distance = x_distance+y_distance
        return distance
    
    def getDistanceToBase(self) -> int:
        x_distance = abs(self.bot.properties.base.x - self.bot.position.x)
        y_distance = abs(self.bot.properties.base.y - self.bot.position.y)
        distance = x_distance+y_distance
        return distance

    def evaluateDiamond(self): # return (List of [diamondPos : Position, distance : int, relativeDistance : int, point : int] : Position)
        evaluation = []
        countDiamonds = len(self.listOfDiamonds)
        for i in range (countDiamonds):
            dist = self.stepDistance(self.bot,self.listOfDiamonds[i])
            point = self.listOfDiamonds[i].properties.points
            temp_eval = [self.listOfDiamonds[i].position,dist,0,point]
            for j in range (countDiamonds):
                temp_eval[2] += self.stepDistance(self.listOfDiamonds[i],self.listOfDiamonds[j])
            evaluation.append(temp_eval)
        return evaluation
    
    def getDirection(self, destP : Position, isVertical : int) -> (int, int):
        delta_x = clamp(destP.x - self.bot.position.x, -1, 1)
        delta_y = clamp(destP.y - self.bot.position.y, -1, 1)
        if delta_x != 0 and delta_y != 0:
            if isVertical == 1:
                delta_x = 0
            else:
                delta_y = 0
        if delta_x == 0 and delta_y == 0:
            delta_x = 1
        return delta_x, delta_y
    
    def isEqualPosition(self, pos1 : Position, pos2 : Position) -> bool :
        return pos1.x == pos2.x and pos1.y == pos2.y
    
    def getDiamondPriorityValue(self, posDiamond : Position, distance : int, relativeDistance : int, point : int) -> float:
        posBase = self.bot.properties.base
        value = self.getDistance(posDiamond, posBase)
        value = distance*distance * relativeDistance * value
        value = value/(point+3)
        return value
        
    def checkNextMoveCrash(self, xmove : int, ymove: int) -> bool :
        currPos = self.bot.position
        nextPos = Position(0, 0)
        nextPos.x = currPos.x+xmove
        nextPos.y = currPos.y+ymove
        found = False
        for i in self.listOfTeleport:
            if self.isEqualPosition(nextPos, i.position):
                found = True
                break
        return found

    def getSaveDirection(self, destPos : Position) -> (int, int):
        currPos = self.bot.position
        xmove, ymove = 0,1
        xstep , ystep = getStep2Way(currPos, destPos)
        if (xstep > ystep) :
            xmove, ymove = self.getDirection(destPos, 0)
        else :
            xmove, ymove = self.getDirection(destPos, 1)
        if self.checkNextMoveCrash(xmove, ymove) :
            currx = currPos.x
            curry = currPos.y
            destx = destPos.x
            desty = destPos.y
            if (ymove != 0):
                if currx == destx:
                    idx = 0
                    if indexValid(currx-1, curry+ymove, self.board_width, self.board_height):
                        if self.matrix[currx-1][curry+ymove]:
                            return 0,ymove
                        idx = -1
                    if indexValid(currx+1, curry+ymove, self.board_width, self.board_height):
                        if self.matrix[currx+1][curry+ymove]:
                            return 0,ymove
                        idx = 1
                    if (idx == -1):
                        return -1,0
                    else:
                        return 1,0
                elif currx < destx:
                    if self.matrix[currx+1][curry+ymove]:
                        return 0,ymove
                    else:
                        return 1,0
                else:
                    if self.matrix[currx-1][curry+ymove]:
                        return 0,ymove
                    else:
                        return -1,0
            else:
                if curry == desty:
                    idx = 0
                    if indexValid(currx+xmove, curry-1, self.board_width, self.board_height):
                        if self.matrix[currx+xmove][curry-1]:
                            return xmove,0
                        idx = -1
                    if indexValid(currx+xmove, curry+1, self.board_width, self.board_height):
                        if self.matrix[currx+xmove][curry+1]:
                            return xmove,0
                        idx = 1
                    if (idx == -1):
                        return 0,-1
                    else:
                        return 0,1
                elif curry > desty:
                    if self.matrix[currx+xmove][curry-1]:
                        return xmove,0
                    else:
                        return 0,-1
                else:
                    if self.matrix[currx+xmove][curry+1]:
                        return xmove,0
                    else:
                        return 0,1
        return xmove, ymove
    
    def isInAreaMove(self, destPos : Position, insideArea : Position) -> bool:
        currPos = self.bot.position
        x = currPos.x <= insideArea.x <= destPos.x or destPos.x <= insideArea.x <= currPos.x
        y = currPos.y <= insideArea.y <= destPos.y or destPos.y <= insideArea.y <= currPos.y
        if (currPos.x == insideArea.x and currPos.y == insideArea.y):
            return False
        return x and y
    
    def pickDiamond(self):
        evaluateD = self.evaluateDiamond()
        countDiamonds = len(evaluateD)
        if (countDiamonds > 0):
            getDiamond = (evaluateD[0],float("inf"))
            for i in range (countDiamonds):
                valueOfi = self.getDiamondPriorityValue(evaluateD[i][0], evaluateD[i][1], evaluateD[i][2], evaluateD[i][3])
                if (valueOfi < getDiamond[1] and evaluateD[i][3]+self.bot.properties.diamonds <= self.bot.properties.inventory_size):
                    getDiamond = (evaluateD[i], valueOfi)
            if countDiamonds == 1 and getDiamond[0][3]+self.bot.properties.diamonds > self.bot.properties.inventory_size:
                return None
            diamondPick = getDiamond[0][0]
            return diamondPick
        return None
    
    def getRandomMove(self):
        for i in self.directions:
            if indexValid(self.bot.position.x+i[0], self.bot.position.y+i[1], self.board_width, self.board_height):
                return i[0],i[1]

    def next_move(self, board_bot: GameObject, board: Board):

        self.bot = board_bot

        self.listOfDiamonds = []
        self.listOfTeleport = []

        self.board_width = board.width
        self.board_height = board.height

        self.redButton = None
        
        self.matrix = [[False for j in range(self.board_height)] for i in range(self.board_width)]

        # Selection of Game Objects
        for i in board.game_objects:
            if i.type == "DiamondGameObject":
                self.listOfDiamonds.append(i)
            elif i.type == "TeleportGameObject":
                self.matrix[i.position.x][i.position.y] = True
                self.listOfTeleport.append(i)
            elif i.type == "DiamondButtonGameObject":
                self.redButton = i

        # initialize the time limit
        time_left = board_bot.properties.milliseconds_left//1000

        # Start evaluate the next move
        to_base = self.getDistanceToBase()
        if time_left <= to_base + 1:
            if self.bot.properties.diamonds != 0:
                
                if (not self.isEqualPosition(self.bot.position, self.bot.properties.base)):
                    priorityDiamond = self.pickDiamond()
                    if priorityDiamond != None and self.isInAreaMove(self.bot.properties.base, priorityDiamond):
                        return self.getSaveDirection(priorityDiamond)
                    if self.isInAreaMove(board_bot.properties.base, self.redButton.position):
                        return self.getSaveDirection(self.redButton.position)
                    return self.getSaveDirection(self.bot.properties.base)
                
                else:
                    return self.getRandomMove()

            else:
                priorityDiamond = self.pickDiamond()

                if (priorityDiamond != None) and self.isInAreaMove(self.bot.properties.base, priorityDiamond):
                    return self.getSaveDirection(priorityDiamond)
                
                else:
                    if self.isInAreaMove(self.bot.properties.base, self.redButton.position):
                        return self.getSaveDirection(self.redButton.position)
                    elif  not self.isEqualPosition(self.bot.position, self.bot.properties.base):
                        return self.getSaveDirection(self.bot.properties.base)
                    else:
                        return self.getRandomMove()
        else:

            if (board_bot.properties.diamonds < board_bot.properties.inventory_size):
                priorityDiamond = self.pickDiamond()
                if (priorityDiamond != None):
                    diamondPick = priorityDiamond
                    if self.isInAreaMove(diamondPick, board_bot.properties.base):
                        return self.getSaveDirection(board_bot.properties.base)
                    elif board_bot.properties.diamonds > 0 and self.getDistance(diamondPick, self.bot.position) >= 2.103*self.getDistance(board_bot.position, board_bot.properties.base):
                        return self.getSaveDirection(board_bot.properties.base)

                    return self.getSaveDirection(diamondPick)
                else:
                    if (not self.isEqualPosition(self.bot.position, self.bot.properties.base)):
                        return self.getSaveDirection(board_bot.properties.base)

                    return self.getRandomMove()
            else:
                return self.getSaveDirection(board_bot.properties.base)
                
