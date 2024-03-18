import random
from colorama import Fore, Style
from typing import Optional, Tuple

from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from ..util import position_equals


class NanangBoneng(BaseLogic):
    # GREEDY BY DIAMOND, TIMING, JIGJAG
    # akurat cari diamond terdekat
    # * kalau inventori udah 4, ketemu diamond point 2 (4 + 2 != 5), maka skip diamond tersebut (cegah error)
    # timing base: detik 46 kalau masih jauh dari base, suruh pulang, kalau dekat dengan base, suruh pulang di detik 53
    # ? modularisasi diamond terdekat
    # defense: - (gajadi)
    # attack: - (gajadi)

    def __init__(self):
        self.timer_to_base = 0
        self.directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        self.goal_position: Optional[Position] = None
        self.current_direction = 0
        self.sequenceMove = []

    def distance(self, x2, x1, y2, y1):
        # hitung jarak antara dua titik
        return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

    def red_diamonds(self, board: Board):
        # list diamond merah
        return [d for d in board.game_objects if d.properties.points == 2]

    def get_teleporter(self, board: Board):
        return [t for t in board.game_objects if t.type == "TeleportGameObject"]

    def diamond_button_position(self, board: Board):
        for temp in board.game_objects:
            if temp.type == "DiamondButtonGameObject":
                return temp.position
        return None

    def closest_diamond(self, board: Board, board_bot: GameObject):
        if board_bot.properties.diamonds == 4:
            # Kalau inventory sudah terisi 4, maka hanya search diamond biru
            self.goal_position = board_bot.properties.base
            temp_distance = 999
            # Kalau tidak ada diamond biru, defaultnya balik ke base
            for i in range(0, len(board.diamonds)):
                if board.diamonds[i].properties.points == 1:
                    distance_to_diamond = self.distance(
                        board.diamonds[i].position.x,
                        board_bot.position.x,
                        board.diamonds[i].position.y,
                        board_bot.position.y,
                    )
                    diamond_position = board.diamonds[i].position
                    if distance_to_diamond < temp_distance:
                        self.goal_position = diamond_position
                        temp_distance = distance_to_diamond

        else:
            diamond_position = board.diamonds[0].position
            self.goal_position = diamond_position
            distance_to_diamond = self.distance(
                diamond_position.x,
                board_bot.position.x,
                diamond_position.y,
                board_bot.position.y,
            )

            # Cari diamond terdekat dari bot

            for i in range(1, len(board.diamonds)):
                distance_to_diamond_i = self.distance(
                    board.diamonds[i].position.x,
                    board_bot.position.x,
                    board.diamonds[i].position.y,
                    board_bot.position.y,
                )

                # Pertukaran hanya terjadi jika
                # 1. Ada jarak yang lebih dekat
                # 2. Jarak sama tapi yg baru lebih besar poin

                if (distance_to_diamond_i < distance_to_diamond) or (
                    distance_to_diamond_i == distance_to_diamond
                    and board.diamonds[i].properties.points
                    > board.diamonds[i - 1].properties.points
                ):
                    diamond_position = board.diamonds[i].position
                    self.goal_position = diamond_position
                    distance_to_diamond = distance_to_diamond_i

        return self.goal_position

    def defense_from_enemy(self, board: Board, board_bot: GameObject):
        bot_enemy_position = []
        for bots in board.bots:
            if bots.id != board_bot.id:
                bot_enemy_position.append((bots.position.x, bots.position.y))

        if (board_bot.position.x + 1, board_bot.position.y) in bot_enemy_position:
            # if board.height - 1 > board_bot.position.y > 0:
            # lakukan gerakan yang valid (tidak menabrak batas height dan widht matrix)
            if board_bot.position.x == 0:
                if board_bot.position.y == 0:
                    return 0, 1
                elif board_bot.position.y == board.height - 1:
                    return 0, -1
                else:
                    return 0, 1
            else:
                return -1, 0

        if (board_bot.position.x - 1, board_bot.position.y) in bot_enemy_position:
            if board_bot.position.x == board.width - 1:
                if board_bot.position.y == 0:
                    return 0, 1
                elif board_bot.position.y == board.height - 1:
                    return 0, -1
                else:
                    return 0, 1
            else:
                return 1, 0

        if (board_bot.position.x, board_bot.position.y + 1) in bot_enemy_position:
            if board_bot.position.y == 0:
                if board_bot.position.x == 0:
                    return 1, 0
                elif board_bot.position.x == board.width - 1:
                    return -1, 0
                else:
                    return 1, 0
            else:
                return 0, -1

        if (board_bot.position.x, board_bot.position.y - 1) in bot_enemy_position:
            if board_bot.position.y == board.height - 1:
                if board_bot.position.x == 0:
                    return 1, 0
                elif board_bot.position.x == board.width - 1:
                    return -1, 0
                else:
                    return 1, 0
            else:
                return 0, 1
        return None

    def tackle_enemy(self, board_bot: GameObject, board: Board):
        bot_enemy_position = []
        for bots in board.bots:
            if bots.id != board_bot.id:
                bot_enemy_position.append((bots.position.x, bots.position.y))

        if (board_bot.position.x + 1, board_bot.position.y) in bot_enemy_position:
            # lakukan gerakan yang menabrak lawan (tidak menabrak batas height dan widht matrix)

            return 1, 0

        if (board_bot.position.x - 1, board_bot.position.y) in bot_enemy_position:
            return -1, 0

        if (board_bot.position.x, board_bot.position.y + 1) in bot_enemy_position:
            return 0, 1

        if (board_bot.position.x, board_bot.position.y - 1) in bot_enemy_position:
            return 0, -1
        return None

    def get_direction_zigzag(self, current_x, current_y, dest_x, dest_y):
        delta_x = dest_x - current_x
        delta_y = dest_y - current_y
        if abs(delta_x) > abs(delta_y):
            if delta_x > 0:
                return (1, 0)
            return (-1, 0)
        else:
            if delta_y > 0:
                return (0, 1)
            return (0, -1)

    def next_move(self, board_bot: GameObject, board: Board):
        props = board_bot.properties
        base = board_bot.properties.base
        current_position = board_bot.position

        # Sequence gerakan menghindari teleport
        if self.sequenceMove:
            self.timer_to_base += 1
            return self.sequenceMove.pop(0)

        # Monitor jarak bot ke base
        distance_to_base = self.distance(
            base.x, board_bot.position.x, base.y, board_bot.position.y
        )

        # Pulang ketika inventory penuh
        if props.diamonds == 5:
            self.goal_position = base

        # Base timing management
        elif self.timer_to_base >= 45:
            if distance_to_base > 5:
                self.goal_position = base
            elif self.timer_to_base >= 52:
                self.goal_position = base
            else:
                self.goal_position = self.closest_diamond(board, board_bot)

        # Injak reset diamond button
        elif (
            self.distance(
                current_position.x,
                self.diamond_button_position(board).x,
                current_position.y,
                self.diamond_button_position(board).y,
            )
            <= 2
            and self.distance(
                current_position.x,
                self.goal_position.x,
                current_position.y,
                self.goal_position.y,
            )
            and not position_equals(self.goal_position, base)
        ):
            diamond_button = self.diamond_button_position(board)
            self.goal_position = diamond_button

        else:
            self.goal_position = self.closest_diamond(board, board_bot)

        # Hitung delta x, delta y
        if self.goal_position:
            delta_x, delta_y = self.get_direction_zigzag(
                current_position.x,
                current_position.y,
                self.goal_position.x,
                self.goal_position.y,
            )

            if delta_x == delta_y:
                step = random.randint(-1, 1)
                delta_x = step
                if delta_y == delta_x:
                    if delta_x == 0:
                        delta_y = 1
                    else:
                        delta_y = delta_x * -1

        # Sequence gerakan menghindari teleport
        teleporter_position = []
        for teleport in self.get_teleporter(board):
            teleporter_position.append((teleport.position.x, teleport.position.y))

        our_bot = (board_bot.position.x, board_bot.position.y)

        if (current_position.x + delta_x, current_position.y) in teleporter_position:
            # ukur jarak y dari current_position ke goal_position
            y_distance_to_goal = self.goal_position.y - current_position.y
            if (
                y_distance_to_goal > 0 or current_position.y == 0
            ):  # validasi agar tidak menabrak batas atas matrix
                delta_x = 0
                delta_y = 1
            else:
                delta_x = 0
                delta_y = -1

        if (current_position.x, current_position.y + delta_y) in teleporter_position:
            # ukur jarak x dari current_position ke goal_position
            if delta_y == 1:  # gerakan sedang turun
                if current_position.x == 0:
                    self.sequenceMove.append((1, 0))
                    self.sequenceMove.append((0, 1))
                    self.sequenceMove.append((0, 1))
                    self.sequenceMove.append((-1, 0))
                else:
                    self.sequenceMove.append((-1, 0))
                    self.sequenceMove.append((0, 1))
                    self.sequenceMove.append((0, 1))
                    self.sequenceMove.append((1, 0))
            else:  # gerakan sedang naik
                if current_position.x == 0:
                    self.sequenceMove.append((1, 0))
                    self.sequenceMove.append((0, -1))
                    self.sequenceMove.append((0, -1))
                    self.sequenceMove.append((-1, 0))
                else:
                    self.sequenceMove.append((-1, 0))
                    self.sequenceMove.append((0, -1))
                    self.sequenceMove.append((0, -1))
                    self.sequenceMove.append((1, 0))

        # Apakah terdapat gerakan di sequence
        if self.sequenceMove:
            delta_x, delta_y = self.sequenceMove.pop(0)
        self.timer_to_base += 1
        return delta_x, delta_y
