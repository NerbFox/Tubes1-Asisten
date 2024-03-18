import random, math
from typing import Optional

from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from ..util import get_direction


"""
point diamond merah = 2
Gameobject :  DiamondGameObject,BotGameObject,DiamondButtonGameObject,TeleportGameObject 



"""


class PinjamDulu100v2(BaseLogic):

    def __init__(self):
        self.directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        self.goal_position: Optional[Position] = None
        self.current_direction = 0
        # self.list_go: Optional[List[GameObject]] = []   Initialize as an empty list

    def isDiamondAvailable(self, board: Board):
        diamond = 0
        for i in range(len(board.game_objects)):
            if (
                board.game_objects[i].type == "DiamondGameObject"
                and board.game_objects[i].properties.points == 1
            ):
                diamond += 1

        return diamond > 0

    def isRedAvailable(self, board: Board):
        red = 0
        for i in range(len(board.game_objects)):
            if (
                board.game_objects[i].type == "DiamondGameObject"
                and board.game_objects[i].properties.points == 2
            ):
                red += 1

        return red > 0

    def getRedPos(self, board: Board):
        for i in range(len(board.game_objects)):
            if (
                board.game_objects[i].type == "DiamondGameObject"
                and board.game_objects[i].properties.points == 2
            ):
                return board.game_objects[i].position

    def goTo(self, a: Position, b: Position):
        delta_x, delta_y = get_direction(a.x, a.y, b.x, b.y)
        return delta_x, delta_y

    def countDistance(self, a: Position, b: Position):
        return abs(b.x - a.x) + abs(b.y - a.y)

    def getClosestDiamondPos(self, board: Board, me: GameObject):
        temp = []
        for i in range(len(board.game_objects)):
            if (
                board.game_objects[i].type == "DiamondGameObject"
                and board.game_objects[i].properties.points == 1
            ):
                temp.append(board.game_objects[i])

        closestPos: GameObject.position
        closestDist = 99999

        for i in range(len(temp)):
            if self.countDistance(me.position, temp[i].position) < closestDist:
                closestDist = self.countDistance(me.position, temp[i].position)
                closestPos = temp[i].position

        return closestPos

    def getClosestRedPos(self, board: Board, me: GameObject):
        temp = []
        for i in range(len(board.game_objects)):
            if (
                board.game_objects[i].type == "DiamondGameObject"
                and board.game_objects[i].properties.points == 2
            ):
                temp.append(board.game_objects[i])

        closestPos: GameObject.position
        closestDist = 99999

        for i in range(len(temp)):
            if self.countDistance(me.position, temp[i].position) < closestDist:
                closestDist = self.countDistance(me.position, temp[i].position)
                closestPos = temp[i].position

        return closestPos

    def getClosestTeleportPos(self, board: Board, me: GameObject):
        temp = []
        for i in range(len(board.game_objects)):
            if board.game_objects[i].type == "TeleportGameObject":
                temp.append(board.game_objects[i].position)

        if self.countDistance(me.position, temp[0]) > self.countDistance(
            me.position, temp[1]
        ):
            return temp[1]
        else:
            return temp[0]

    def isCloseBase(self, a: Position, b: Position):
        if self.countDistance(a, b) <= 8:
            return True

    def isHomeWithPortal(self, board: Board, me: GameObject):
        base = me.properties.base
        usPos = me.position
        temp = []
        for i in range(len(board.game_objects)):
            if board.game_objects[i].type == "TeleportGameObject":
                temp.append(board.game_objects[i])

        if self.countDistance(me.position, temp[0].position) > self.countDistance(
            me.position, temp[1].position
        ):
            tPos1 = temp[1].position
            tGo1 = temp[1]
            tPos2 = temp[0].position
            tGo2 = temp[0]
        else:
            tPos1 = temp[0].position
            tGo1 = temp[0]
            tPos2 = temp[1].position
            tGo2 = temp[1]
        # tPos1 itu selalu posisi teleporter yang paling dekat sama botplayer
        j_us_to_tPos1 = self.countDistance(usPos, tPos1)
        j_tPos2_to_base = self.countDistance(tPos2, base)
        j_us_to_base = self.countDistance(usPos, base)

        if j_us_to_tPos1 + j_tPos2_to_base < j_us_to_base:
            return True
        else:
            return False

    def isBetterPortalDiamond(self, usPos: Position, board: Board, me: GameObject):
        temp = []
        for i in range(len(board.game_objects)):
            if board.game_objects[i].type == "TeleportGameObject":
                temp.append(board.game_objects[i])

        if self.countDistance(me.position, temp[0].position) > self.countDistance(
            me.position, temp[1].position
        ):
            tPos1 = temp[1].position
            tPos2 = temp[0].position
            tGo2 = temp[0]
        else:
            tPos1 = temp[0].position
            tPos2 = temp[1].position
            tGo2 = temp[1]

        dPos = self.getClosestDiamondPos(board, me)
        dPos2 = self.getClosestDiamondPos(board, tGo2)

        # Kalau jarak kita ke diamond lebih deket via portal
        j_Us_to_tPos1 = self.countDistance(usPos, tPos1)
        j_Us_to_dPos = self.countDistance(usPos, dPos)
        j_tPos2_to_dPos2 = self.countDistance(tPos2, dPos2)

        jTot = j_Us_to_tPos1 + j_tPos2_to_dPos2

        if j_Us_to_dPos > jTot:
            return True
        else:
            return False

    def checkDiamondReset(self, mePosition: Position, board: Board):
        temp = []
        for i in range(len(board.game_objects)):
            if board.game_objects[i].type == "DiamondButtonGameObject":
                temp.append(board.game_objects[i])
        if (
            mePosition.x + 1 == temp[0].position.x
            and mePosition.y == temp[0].position.y
        ):
            return temp[0].position
        elif (
            mePosition.x - 1 == temp[0].position.x
            and mePosition.y == temp[0].position.y
        ):
            return temp[0].position
        elif (
            mePosition.x == temp[0].position.x
            and mePosition.y + 1 == temp[0].position.y
        ):
            return temp[0].position
        elif (
            mePosition.x == temp[0].position.x
            and mePosition.y - 1 == temp[0].position.y
        ):
            return temp[0].position
        else:
            return mePosition

    def next_move(self, board_bot: GameObject, board: Board):

        usPos = board_bot.position
        tempUsPos = usPos
        nextPos = tempUsPos

        base = board_bot.properties.base
        tPos1 = self.getClosestTeleportPos(board, board_bot)
        positionButton = self.checkDiamondReset(usPos, board)
        time = math.floor(board_bot.properties.milliseconds_left / 1000)
        print("waktu", time)
        print("Jarak ke base ", self.countDistance(usPos, base))
        print("POSISI KITA", usPos)
        if self.isDiamondAvailable(board):
            bluePos = self.getClosestDiamondPos(board, board_bot)

        if self.isRedAvailable(board):
            redPos = self.getClosestRedPos(board, board_bot)

        if positionButton != usPos:

            delta_x, delta_y = self.goTo(usPos, positionButton)

        elif time >= 15:
            if board_bot.properties.diamonds == 5:
                print("Balik ke base (5)")
                if self.isHomeWithPortal(board, board_bot) and usPos != tPos1:
                    print("Lewat portal lebih cepat")
                    delta_x, delta_y = self.goTo(usPos, tPos1)
                else:
                    print("Langsung tanpa portal")
                    delta_x, delta_y = self.goTo(usPos, base)

                # PROTOKOL MAIN AMAN DEKET BASE============
            elif board_bot.properties.diamonds >= 3 and self.isCloseBase(usPos, base):
                if self.isRedAvailable(board) and self.isDiamondAvailable(board):
                    if (
                        self.countDistance(usPos, redPos) < 3
                        and board_bot.properties.diamonds < 4
                    ):
                        print("pengen balik ke base tapi ada merah deket banget")
                        delta_x, delta_y = self.goTo(usPos, redPos)
                    elif self.countDistance(usPos, bluePos) < 3:
                        print("pengen balik ke base tapi ada biru deket banget")
                        delta_x, delta_y = self.goTo(usPos, bluePos)
                    else:
                        print("Deket base dan ada diamond di invent")
                        if self.isHomeWithPortal(board, board_bot) and usPos != tPos1:
                            print("Lewat portal lebih cepat")
                            delta_x, delta_y = self.goTo(usPos, tPos1)
                        else:
                            print("Langsung tanpa portal")
                            delta_x, delta_y = self.goTo(usPos, base)
                else:
                    print("Deket base dan ada diamond di invent")
                    if self.isHomeWithPortal(board, board_bot) and usPos != tPos1:
                        print("Lewat portal lebih cepat")
                        delta_x, delta_y = self.goTo(usPos, tPos1)
                    else:
                        print("Langsung tanpa portal")
                        delta_x, delta_y = self.goTo(usPos, base)

                # PROTOKOL GAREP DIAMOND BANYAK=======
            elif board_bot.properties.diamonds <= 3:
                if self.isDiamondAvailable(board) and self.isRedAvailable(board):
                    if (
                        self.isBetterPortalDiamond(usPos, board, board_bot)
                        and usPos != tPos1
                    ):
                        print("Via portal lebih bagus!")
                        delta_x, delta_y = self.goTo(usPos, tPos1)
                    elif self.countDistance(usPos, bluePos) < self.countDistance(
                        usPos, redPos
                    ):
                        delta_x, delta_y = self.goTo(usPos, bluePos)
                        print("Prior Biru")
                        print("Akhir Uspos", usPos)
                    else:
                        delta_x, delta_y = self.goTo(usPos, redPos)
                        print("Prior Merah")
                        print("Akhir Uspos", usPos)
                elif (
                    self.isDiamondAvailable(board)
                    and self.isRedAvailable(board) == False
                ):
                    delta_x, delta_y = self.goTo(usPos, bluePos)
                    print("SIsa biru")
                else:
                    delta_x, delta_y = self.goTo(usPos, redPos)
                    print("SIsa merah")
            else:
                if self.isDiamondAvailable(board):
                    delta_x, delta_y = self.goTo(usPos, bluePos)
                    print("Diamond ada 4 paksa ambil biru")
                else:
                    print("Diamond ada 4 tapi gk ada biru,balik")
                    if self.isHomeWithPortal(board, board_bot) and usPos != tPos1:
                        print("Lewat portal lebih cepat")
                        delta_x, delta_y = self.goTo(usPos, tPos1)
                    else:
                        print("Langsung tanpa portal")
                        delta_x, delta_y = self.goTo(usPos, base)

        else:
            if board_bot.properties.diamonds > 0:
                print("Waktu dikit dan ada diamond,balik ke base")
                if self.isHomeWithPortal(board, board_bot) and usPos != tPos1:
                    print("Lewat portal lebih cepat")
                    delta_x, delta_y = self.goTo(usPos, tPos1)
                else:
                    print("Langsung tanpa portal")
                    delta_x, delta_y = self.goTo(usPos, base)

            else:
                if self.isDiamondAvailable(board) and self.isRedAvailable(board):
                    if self.countDistance(usPos, bluePos) < self.countDistance(
                        usPos, redPos
                    ):
                        delta_x, delta_y = self.goTo(usPos, bluePos)
                        print("Prior biru waktu dikit")
                    else:
                        delta_x, delta_y = self.goTo(usPos, redPos)
                        print("Prior Merah waktu dikit")
                elif (
                    self.isDiamondAvailable(board)
                    and self.isRedAvailable(board) == False
                ):
                    delta_x, delta_y = self.goTo(usPos, bluePos)
                    print("SIsa biru waktu dikit")
                else:
                    delta_x, delta_y = self.goTo(usPos, redPos)
                    print("SIsa merah waktu dikit")
        return delta_x, delta_y
