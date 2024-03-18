# import random
from typing import Optional

from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position


class JanggarLogic(BaseLogic):
    def __init__(self):
        self.goal_position: Optional[Position] = None
        self.halang = []

    def next_move(self, board_bot: GameObject, board: Board):
        current_position = board_bot.position
        # menghindari tabrakan, tombol, dan tp
        self.halang = []
        teleporter = []
        for barang in board.game_objects:
            # bot dianggap halangan jika tidak bisa ditabrak
            if barang.type == "BotGameObject" and (barang.position != current_position):
                if (barang.properties.milliseconds_left and (
                        barang.properties.milliseconds_left % 1000 - board_bot.properties.milliseconds_left % 1000) > 0):
                    self.halang.append((barang.position.x + 1, barang.position.y))
                    self.halang.append((barang.position.x, barang.position.y + 1))
                    self.halang.append((barang.position.x - 1, barang.position.y))
                    self.halang.append((barang.position.x, barang.position.y - 1))
            if barang.type == "DiamondButtonGameObject":
                self.halang.append((barang.position.x, barang.position.y))
                diabutton = barang.position
            if barang.type == "TeleportGameObject":
                print(barang)
                self.halang.append((barang.position.x, barang.position.y))
                teleporter.append((barang.position))

        props = board_bot.properties
        self.goal_position: Optional[Position] = None
        basepath = self.determinetargetndistance(current_position, teleporter, props.base)
        # kalau base sangat dekat balik
        if props.diamonds > 0 and basepath[1] <= 2:
            self.goal_position = basepath[0]
        # Sisa Waktu beda tipis dengan perjalanan ke base dan masih memegang diamond. Kembali ke base
        if props.diamonds > 0 and (board_bot.properties.milliseconds_left / 1000 - basepath[1]) <= 6:
            self.goal_position = basepath[0]
        # diamond penuh pulang ke base
        if self.goal_position == None:
            if props.diamonds >= 4:
                self.goal_position = board_bot.properties.base
                closestdia = self.diamondterdekat(board, board_bot, teleporter)
                if (closestdia[1] != 100000 and closestdia[2] == 1 and props.diamonds == 4): self.goal_position = \
                closestdia[0]
            else:
                dist = self.determinetargetndistance(current_position, teleporter, diabutton)
                if (dist):
                    distlimit = max(9, dist[1])
                else:
                    distlimit = 100000
                closestdia = self.diamondterdekat(board, board_bot, teleporter)
                if (closestdia and closestdia[1] <= distlimit):
                    self.goal_position = closestdia[0]
                else:
                    self.goal_position = diabutton
        print(self.goal_position)
        return self.selamatsampaitujuan(current_position, self.goal_position)

    def diamondterdekat(self, board: Board, board_bot: GameObject, teleporter):
        jarak = 100000
        for diamond in board.diamonds:
            curdia = self.determinetargetndistance(board_bot.position, teleporter, diamond.position)
            if (jarak > curdia[1]):
                jarak = curdia[1]
                target = curdia[0]
                points = diamond.properties.points
            # memprioritaskan diamond merah jika jaraknya tidak jauh
            if (diamond.properties.points == 2 and jarak > curdia[1] * 0.75):
                jarak = curdia[1] * 0.75
                target = curdia[0]
                points = diamond.properties.points
        return target, jarak, points

    def selamatsampaitujuan(self, curpos, target):
        dx = target.x - curpos.x
        dy = target.y - curpos.y
        adx = abs(dx)
        ady = abs(target.y - curpos.y)
        # handling bug
        if (dx == 0 and dy == 0):
            if (curpos.x + 1 < 15):
                return 1, 0
            else:
                return -1, 0
        if ((adx + ady) == 1):
            return dx, dy
        else:
            if (adx > ady):
                # tidak terhalang
                if (curpos.x + (dx / adx), curpos.y) not in self.halang:
                    return (dx / adx), 0
                # terhalang
                if (ady != 0):
                    return 0, (dy / ady)
                else:
                    # tidak di tepi
                    if (curpos.y - 1 >= 0 and curpos.y + 1 < 15):
                        if (curpos.x, curpos.y - 1) not in self.halang:
                            return 0, -1
                        else:
                            return 0, 1
                    # di tepi
                    else:
                        if (curpos.y - 1 >= 0):
                            return 0, -1
                        else:
                            return 0, 1
            # tidak terhalang
            if (curpos.x, curpos.y + (dy / ady)) not in self.halang:
                return 0, (dy / ady)
            # terhalang
            if (adx != 0):
                return (dx / adx), 0
            else:
                # tidak di tepi
                if (curpos.x - 1 >= 0 and curpos.x + 1 < 15):
                    if (curpos.x - 1, curpos.y) not in self.halang:
                        return -1, 0
                    else:
                        return 1, 0
                # di tepi
                else:
                    if (curpos.y - 1 >= 0):
                        return -1, 0
                    else:
                        return 1, 0

    # menentukan apakah perlu teleport
    def determinetargetndistance(self, position, teleporter, target):
        t1x = teleporter[0].x
        t1y = teleporter[0].y
        t2x = teleporter[1].x
        t2y = teleporter[1].y
        p1 = abs(position.x - target.x) + abs(position.y - target.y)
        p2 = abs(position.x - t1x) + abs(position.y - t1y) + abs(target.x - t1x) + abs(target.y - t2y)
        p3 = abs(position.x - t2x) + abs(position.y - t2y) + abs(target.x - t1x) + abs(target.x - t1y)
        if (p1 < p2 and p1 < p3): return target, p1  # ga tele
        if (p2 < p1 and p2 < p3): return teleporter[0], p2  # lewat teleporter 1
        return teleporter[1], p3  # lewat teleporter 2