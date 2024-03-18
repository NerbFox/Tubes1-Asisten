import random
import math
from typing import Tuple
from typing import Optional
from game.logic.base import BaseLogic
from game.models import Board, GameObject, Position, Properties
from ..util import get_direction


def check_blue(board: Board):
    n = 0
    for d in board.diamonds:
        if d.properties.points == 1:
            n += 1
    return n


def get_nearest_blue(board_bot: GameObject, board: Board):
    if check_blue(board) > 0:
        in_y, in_x, out_y, out_x, min = get_portal(board_bot, board)
        temp_min = 30
        for d in board.diamonds:
            if d.properties.points == 1:
                delta = abs(d.position.y - out_y) + abs(d.position.x - out_x) + abs(in_y - board_bot.position.y) + abs(
                    in_x - board_bot.position.x)
                if delta < temp_min:
                    temp_min = delta
        min += temp_min
        res_y = in_y
        res_x = in_x
        for d in board.diamonds:
            if d.properties.points == 1:
                delta = abs(d.position.y - board_bot.position.y) + abs(d.position.x - board_bot.position.x)
                if delta < min:
                    min = delta
                    res_y = d.position.y
                    res_x = d.position.x
        if res_y == board_bot.position.y and res_x == board_bot.position.x:
            res_y += 1
        return res_y, res_x, min


def check_red(board: Board):
    n = 0
    for d in board.diamonds:
        if d.properties.points == 2:
            n += 1
    return n


def get_nearest_red(board_bot: GameObject, board: Board):
    if check_red(board) > 0:
        in_y, in_x, out_y, out_x, min = get_portal(board_bot, board)
        temp_min = 30
        for d in board.diamonds:
            if d.properties.points == 2:
                delta = abs(d.position.y - out_y) + abs(d.position.x - out_x)
                if delta < temp_min:
                    temp_min = delta
        min += temp_min
        res_y = in_y
        res_x = in_x
        for d in board.diamonds:
            if d.properties.points == 2:
                delta = abs(d.position.y - board_bot.position.y) + abs(d.position.x - board_bot.position.x)
                if delta < min:
                    min = delta
                    res_y = d.position.y
                    res_x = d.position.x
        if res_y == board_bot.position.y and res_x == board_bot.position.x:
            res_y += 1
        return res_y, res_x, min


def get_portal(board_bot: GameObject, board: Board):
    min = 30
    in_y = -1
    in_x = -1
    out_y = -1
    out_x = -1
    delta0 = abs(board.game_objects[0].position.y - board_bot.position.y) + abs(
        board.game_objects[0].position.x - board_bot.position.x)
    delta1 = abs(board.game_objects[1].position.y - board_bot.position.y) + abs(
        board.game_objects[1].position.x - board_bot.position.x)
    if delta0 < delta1:
        in_y = board.game_objects[0].position.y
        in_x = board.game_objects[0].position.x
        out_y = board.game_objects[1].position.y
        out_x = board.game_objects[1].position.x
        min = delta0
    else:
        in_y = board.game_objects[1].position.y
        in_x = board.game_objects[1].position.x
        out_y = board.game_objects[0].position.y
        out_x = board.game_objects[0].position.x
        min = delta1
    return in_y, in_x, out_y, out_x, min


def go_home(board_bot: GameObject):
    base = board_bot.properties.base
    delta = abs(board_bot.position.y - base.y) + abs(board_bot.position.x - base.x)
    return delta


def go_button(board: Board):
    for g in board.game_objects:
        if g.type == "DiamondButtonGameObject":
            y_button = g.position.y
            x_button = g.position.x
    return y_button, x_button


def threesteps(board_bot: GameObject, board: Board):  # cari apakah ada diamond dalam 3 langkah dari bot
    min = 4  # tidak ada dalam 3 langkah dari posisi bot
    xtemp = 0  # untuk tampung nilai dengan jarak terkecil
    ytemp = 0  # untuk tampung nilai dengan jarak terkecil
    base = board_bot.properties.base
    for d in board.diamonds:
        if d.properties.points == 1 or d.properties.points == 2:
            jarakx = abs(d.position.x - board_bot.position.x)
            jaraky = abs(d.position.y - board_bot.position.y)
            if jarakx + jaraky < min:  # dalam tigalangkah
                xtemp = d.position.x
                ytemp = d.position.y
            elif jarakx + jaraky == min:  # sama dengan minimum
                tempbasedistance = abs(xtemp - base.x) + abs(ytemp - base.y)
                currentbasedistance = abs(d.position.x - base.x) + abs(d.position.y - base.y)
                if currentbasedistance <= tempbasedistance:
                    xtemp = d.position.x
                    ytemp = d.position.y
            elif jarakx + jaraky == 1:  # hanya beda 1 kotak sudah pasti minimum
                return ytemp, xtemp
    return ytemp, xtemp


def check_portal_and_base_align(board_bot: GameObject, board: Board):
    # menghindari portal saat ada portal yang segaris dengan home base (di koordinat y yang sama atau x yang sama)
    # akan terjadi jika self goal position = base
    # jika portal berada di tengah (bot - portal - base) atau (base - bot - portal)
    # self goal position = base
    check = False
    base_x = board_bot.properties.base.x
    base_y = board_bot.properties.base.y
    portal_y0 = board.game_objects[0].position.y
    portal_y1 = board.game_objects[1].position.y
    portal_x0 = board.game_objects[0].position.x
    portal_x1 = board.game_objects[1].position.x
    if ((board_bot.goal_position.y == base_y)):
        if ((board_bot.position.y == base_y) and (board_bot.position.y == portal_y0)):
            if (board_bot.position.y < portal_y0 < base_y):
                check = True
            elif (board_bot.position.y > portal_y1 > base_y):
                check = True
        elif ((board_bot.position.y == base_y) and (board_bot.position.y == portal_y1)):
            if (board_bot.position.y < portal_y0 < base_y):
                check = True
            elif (board_bot.position.y > portal_y1 > base_y):
                check = True
    if ((board_bot.goal_position.x == base_x)):
        if ((board_bot.position.x == base_x) and (board_bot.position.x == portal_x0)):
            if (board_bot.position.x < portal_x0 < base_x):
                check = True
            elif (board_bot.position.x > portal_x1 > base_x):
                check = True
        elif ((board_bot.position.x == base_x) and (board_bot.position.x == portal_x1)):
            if (board_bot.position.x < portal_x0 < base_x):
                check = True
            elif (board_bot.position.x > portal_x1 > base_x):
                check = True
    return check


def evade_portal(board_bot: GameObject, board: Board):
    res_y = board_bot.position.y
    res_x = board_bot.position.x
    if (check_portal_and_base_align(board_bot, board)):
        if (board_bot.position.y == 14):
            res_y -= 1
        elif (board_bot.position.y == 0):
            res_y += 1
        elif (board_bot.position.x == 14):
            res_x -= 1
        elif (board_bot.position.x == 0):
            res_x += 1
    return res_y, res_x


class TonggokuNyalegNdesLogic(BaseLogic):
    def __init__(self):
        # Initialize attributes necessary
        self.directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        self.goal_position: Optional[Position] = None
        self.current_direction = 0

    def next_move(self, board_bot: GameObject, board: Board):
        props = board_bot.properties
        time = math.floor(board_bot.properties.milliseconds_left / 1000)
        print(time)
        y_button, x_button = go_button(board)
        if check_blue(board) + check_red(board) < 17 and (
                abs(board_bot.position.y - y_button) + abs(board_bot.position.x - x_button)) < 5 and props.diamonds < 4:
            y, x = go_button(board)
            target = [y, x]
            self.goal_position = target
        else:
            if props.diamonds == 5:
                base = board_bot.properties.base
                target = [base.y, base.x]
                self.goal_position = target
            else:
                if props.diamonds < 4:
                    if go_home(board_bot) > time - 3 and props.diamonds > 0:
                        base = board_bot.properties.base
                        target = [base.y, base.x]
                        self.goal_position = target
                    else:
                        if check_red(board) > 0 and check_blue(board) > 0:
                            y_blue, x_blue, min_blue = get_nearest_blue(board_bot, board)
                            y_red, x_red, min_red = get_nearest_red(board_bot, board)
                            ytemp, xtemp = threesteps(board_bot, board)
                            delta = abs(board_bot.position.y - ytemp) + abs(board_bot.position.x - xtemp)
                            if ytemp == 0 and xtemp == 0:
                                y_blue, x_blue, min_blue = get_nearest_blue(board_bot, board)
                                y_red, x_red, min_red = get_nearest_red(board_bot, board)
                                if min_blue * 2 < min_red:
                                    target = [int(y_blue), int(x_blue)]
                                    self.goal_position = target
                                else:
                                    target = [int(y_red), int(x_red)]
                                    self.goal_position = target
                            else:
                                if delta < min_blue:
                                    target = [int(ytemp), int(xtemp)]
                                    self.goal_position = target
                                else:
                                    if min_blue * 2 < min_red:
                                        target = [int(y_blue), int(x_blue)]
                                        self.goal_position = target
                                    else:
                                        target = [int(y_red), int(x_red)]
                                    self.goal_position = target
                        if check_red(board) > 0 and check_blue(board) == 0:
                            y_red, x_red, min_red = get_nearest_red(board_bot, board)
                            target = [int(y_red), int(x_red)]
                            self.goal_position = target
                        if check_red(board) == 0 and check_blue(board) > 0:
                            y_blue, x_blue, min_blue = get_nearest_blue(board_bot, board)
                            target = [int(y_blue), int(x_blue)]
                            self.goal_position = target

                if props.diamonds == 4:
                    if go_home(board_bot) > time - 3 and props.diamonds > 0:
                        base = board_bot.properties.base
                        target = [base.y, base.x]
                        self.goal_position = target
                    else:
                        y_blue, x_blue, min_blue = get_nearest_blue(board_bot, board)
                        if check_blue(board) > 0:
                            target = [int(y_blue), int(x_blue)]
                            self.goal_position = target
                        else:
                            base = board_bot.properties.base
                            target = [base.y, base.x]
                            self.goal_position = target

        current_position = board_bot.position

        if self.goal_position:
            # We are aiming for a specific position, calculate delta
            delta_x, delta_y = get_direction(
                current_position.x,
                current_position.y,
                self.goal_position[1],
                self.goal_position[0],
            )
        else:
            # Roam around
            delta = self.directions[self.current_direction]
            delta_x = delta[0]
            delta_y = delta[1]
            if random.random() > 0.6:
                self.current_direction = (self.current_direction + 1) % len(
                    self.directions
                )

        return delta_x, delta_y