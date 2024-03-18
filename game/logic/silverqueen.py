### FINAL BOT ###

import random
from typing import Optional, List

from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from ..util import get_direction

def calculate_distance(position1, position2):
    return ((position1.x - position2.x) ** 2 + (position1.y - position2.y) ** 2) ** 0.5

@property
def teleport(self) -> List[GameObject]:
    return [d for d in self.game_objects if d.type == "TeleportGameObject"]

class SuperSilverqueen(BaseLogic):
    def __init__(self):
        self.directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        self.goal_position: Optional[Position] = None
        self.current_direction = 0
        self.move_count = 0 

    def find_teleport_gameobject(self, board: Board) -> Optional[Position]:
        teleport_objects = [obj for obj in board.game_objects if obj.type == "TeleportGameObject"]
        if teleport_objects:
            return teleport_objects[0].position, teleport_objects[1].position
        else:
            return None

    def find_nearest_diamond(self, board_bot: GameObject, board: Board):
        diamonds = board.diamonds
        if diamonds:
            if board_bot.properties.diamonds == 4:
                # Kalau diamonds sudah 4, cari diamond biru
                blue_diamonds = [diamond for diamond in diamonds if diamond.properties.points != 2]
                if blue_diamonds:
                    nearest_diamond = min(blue_diamonds, key=lambda diamond: abs(diamond.position.x - board_bot.position.x) + abs(diamond.position.y - board_bot.position.y))
                else:
                    nearest_diamond = min(diamonds, key=lambda diamond: abs(diamond.position.x - board_bot.position.x) + abs(diamond.position.y - board_bot.position.y))
            else:
                nearest_diamond = min(diamonds, key=lambda diamond: abs(diamond.position.x - board_bot.position.x) + abs(diamond.position.y - board_bot.position.y))
            self.goal_position = nearest_diamond.position
        else:
            # No diamonds found, roam around
            self.goal_position = None

    def next_move(self, board_bot: GameObject, board: Board):
        props = board_bot.properties
        bots = board.bots
        # Check other bots position
        for bot in bots:
            if bot != board_bot:
                temp_distance = calculate_distance(bot.position, board_bot.position)
                if temp_distance <= 1:
                    temp_delta_x = bot.position.x - board_bot.position.x
                    temp_delta_y = bot.position.y - board_bot.position.y
                    # If adjacent, move away
                    if temp_delta_x == 0 and abs(temp_delta_y) == 1:
                        # jika ada bot lawan di sebelah kanan atau kiri, arahkan untuk bergerak ke atas atau bawah
                        if 0 <= board_bot.position.y - temp_delta_y <= board.width:
                            return 0, -temp_delta_y
                        elif 0 <= board_bot.position.y + temp_delta_y <= board.width:
                            return 0, temp_delta_y
                    elif temp_delta_y == 0 and abs(temp_delta_x) == 1:
                        # jika ada bot lawan di atas atau bawah, arahkan untuk bergerak ke kanan atau kiri (atur invalid move juga)
                        if 0 <= board_bot.position.x - temp_delta_x <= board.width:
                            return -temp_delta_x, 0
                        elif 0 <= board_bot.position.x + temp_delta_x <= board.width:
                            return temp_delta_x, 0
                        
        # lokasi teleport game object
        teleport_position, teleport_position1 = self.find_teleport_gameobject(board)
        if teleport_position:
            print("teleporter location:", teleport_position)
            teleport_x = teleport_position.x
            teleport_y = teleport_position.y
            print("teleporter location - x:", teleport_x, "y:", teleport_y)
        
        if teleport_position1:
            print("teleporter location:", teleport_position1)
            teleport_x1 = teleport_position1.x
            teleport_y1 = teleport_position1.y
            print("teleporter location - x:", teleport_x1, "y:", teleport_y1)

        # Analyze new state
        if props.diamonds == 5:
            # Move to base
            base = board_bot.properties.base
            self.goal_position = base
        else:
            # Find the nearest diamond
            self.find_nearest_diamond(board_bot, board)
            if calculate_distance(self.goal_position, board_bot.position) > calculate_distance(board_bot.properties.base, board_bot.position) and props.diamonds >= 3:
                self.goal_position = board_bot.properties.base

        current_position = board_bot.position
        if self.goal_position:
            # We are aiming for a specific position, calculate delta
            delta_x, delta_y = get_direction(
                current_position.x,
                current_position.y,
                self.goal_position.x,
                self.goal_position.y,
            )
            board_x, board_y = board_bot.position.x, board_bot.position.y
            if (board_x + delta_x == teleport_x and board_y + delta_y == teleport_y) or \
            (board_x + delta_x == teleport_x1 and board_y + delta_y == teleport_y1):
                distance = calculate_distance(self.goal_position, board_bot.position)
                if distance < 8 and (0 <= board_x + delta_x <= 14) and (0 <=  board_y + delta_y <= 14):
                    return -delta_x, -delta_y
            print("current x:", current_position.x)
            print("current y:", current_position.y)
            print("goal x:", self.goal_position.x)
            print("goal y:", self.goal_position.y)
        else:
            # Roam around
            delta = self.directions[self.current_direction]
            delta_x = delta[0]
            delta_y = delta[1]
            if random.random() > 0.6:
                self.current_direction = (self.current_direction + 1) % len(
                    self.directions
                )

        self.move_count += 1
        print("Move count:", self.move_count)

        if (0 <= board_bot.position.x + delta_x <= board.width) and (0 <= board_bot.position.y + delta_y <= board.width):
            return delta_x, delta_y
        else:
            # adjust movement biar tetap didalam board
            while (delta_x + board_bot.position.x > board.width) or (delta_x + board_bot.position.x < 0) or (delta_y + board_bot.position.y > board.width) or (delta_y + board_bot.position.y < 0):
                delta_x = random.randint(-1, 1)
                if delta_x != 0:
                    delta_y = 0
                else:
                    delta_y = random.choice([-1, 1])
            return delta_x, delta_y