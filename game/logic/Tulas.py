from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from ..util import get_direction
import random
from typing import List, Optional


# check if it's safe to go left, right, up , or down (used in avoiding bot case)
def safe(delta_x, delta_y, up, down, left, right):
    if ((delta_x == 1) and right) or ((delta_x == -1) and left) or ((delta_y == 1) and up) or (
            (delta_y == -1) and down):
        return True
    return False


def avoid_tele_base(current_position: Position, up, down, left, right, board: Board, delta_x, delta_y):
    if (safe(delta_x, delta_y, up, down, left, right) == False):
        if (delta_x == 1 and delta_y == 0) or (delta_x == -1 and delta_y == 0):  # bot ada di sumbu x
            if (current_position.y >= board.height / 2):
                return 0, 1  # up
            else:
                return 0, -1  # down
        else:
            if (current_position.x >= board.width / 2):
                return -1, 0  # left
            else:
                return 1, 0  # right
    else:
        return 0, 0


class TulasLogic(BaseLogic):
    def __init__(self):
        self.goal_position: Optional[Position] = None
        self.travel_method = 0

    # see teleport.js for details
    def get_teleport_objects(self, board: Board) -> List[GameObject]:
        return [d for d in board.game_objects if d.type == "TeleportGameObject"]

    # see diamond-button.js for details
    def get_red_button_objects(self, board: Board) -> List[GameObject]:
        return [d for d in board.game_objects if d.type == "DiamondButtonGameObject"]

    # offense to attack
    def get_bot_objects(self, board: Board) -> List[GameObject]:
        return [d for d in board.game_objects if d.type == "BotGameObject"]

    # return closest diamond, method to get to diamond (0: direct, 1: teleport 1, 2: teleport 2), and the distance
    def closest_diamond(self, board: Board, board_bot: GameObject, diamonds: List[GameObject]):
        current_position = board_bot.position
        min = 9999
        method = 0
        idx = -1
        teleporters = self.get_teleport_objects(board)

        for i in range(0, len(diamonds)):
            dist = abs(current_position.x - diamonds[i].position.x) + abs(current_position.y - diamonds[i].position.y)
            this_method = 0
            dist_teleporter_1 = abs(current_position.x - teleporters[0].position.x) + abs(
                current_position.y - teleporters[0].position.y) + abs(
                diamonds[i].position.x - teleporters[1].position.x) + abs(
                diamonds[i].position.y - teleporters[1].position.y)
            dist_teleporter_2 = abs(current_position.x - teleporters[1].position.x) + abs(
                current_position.y - teleporters[1].position.y) + abs(
                diamonds[i].position.x - teleporters[0].position.x) + abs(
                diamonds[i].position.y - teleporters[0].position.y)
            if (dist_teleporter_1 <= dist) and (dist_teleporter_1 <= dist_teleporter_2):
                dist = dist_teleporter_1
                this_method = 1
            elif (dist_teleporter_2 < dist) and (dist_teleporter_2 < dist_teleporter_1):
                dist = dist_teleporter_2
                this_method = 2

            if (dist < min):
                min = dist
                method = this_method
                idx = i

        return {"diamond": diamonds[idx], "method": method, "distance": min}

    # return method to get to position (0: direct, 1: teleport 1, 2: teleport 2) and the distance
    def closest_to_position(self, board: Board, board_bot: GameObject, goal: Position):
        current_position = board_bot.position

        teleporters = self.get_teleport_objects(board)
        method = 0
        dist = abs(current_position.x - goal.x) + abs(current_position.y - goal.y)
        dist_teleporter_1 = abs(current_position.x - teleporters[0].position.x) + abs(
            current_position.y - teleporters[0].position.y) + abs(goal.x - teleporters[1].position.x) + abs(
            goal.y - teleporters[1].position.y)
        dist_teleporter_2 = abs(current_position.x - teleporters[1].position.x) + abs(
            current_position.y - teleporters[1].position.y) + abs(goal.x - teleporters[0].position.x) + abs(
            goal.y - teleporters[0].position.y)
        if (dist_teleporter_1 <= dist) and (dist_teleporter_1 <= dist_teleporter_2):
            dist = dist_teleporter_1
            method = 1
        elif (dist_teleporter_2 < dist) and (dist_teleporter_2 < dist_teleporter_1):
            dist = dist_teleporter_2
            method = 2

        return {"method": method, "distance": dist}

    def next_move(self, board_bot: GameObject, board: Board):
        # Analyze state of board
        teleport_objects = self.get_teleport_objects(board)
        red_button_objects = self.get_red_button_objects(board)
        bot_objects = self.get_bot_objects(board)
        diamond_list = board.diamonds
        base = board_bot.properties.base
        to_base = self.closest_to_position(board, board_bot, base)
        time_left = board_bot.properties.milliseconds_left / 1000
        to_red_button = self.closest_to_position(board, board_bot, red_button_objects[0].position)

        # Analyze state of bot
        props = board_bot.properties
        current_position = board_bot.position
        my_bot_pocket = board_bot.properties.diamonds

        # base variables for tackle bot
        avoid = False
        left = True
        right = True
        up = True
        down = True

        # Move to base if bot's inventory is full or there is no timeleft
        if props.diamonds == 5 or (to_base["distance"] >= time_left - 2 and to_base["distance"] > 0):
            self.goal_position = base
            self.travel_method = to_base["method"]
        # There is still time to get diamonds
        else:
            bot_position = [i.position for i in bot_objects]
            bot_pockets = [j.properties.diamonds for j in bot_objects]

            # offense other bot if the distance to each other is 1
            distance_bot_list = [(abs(current_position.x - position.x) + abs(current_position.y - position.y)) for
                                 position in bot_position]
            for i in range(len(bot_objects)):
                if (current_position.x == bot_objects[i].position.x and current_position.y == bot_objects[
                    i].position.y):
                    idx_our_bot = i
            i = 0
            for bot in bot_position:
                if (current_position != bot and distance_bot_list[i] == 1 and bot_pockets[i] > my_bot_pocket):
                    self.goal_position = bot_position[i]
                    delta_x, delta_y = get_direction(
                        current_position.x,
                        current_position.y,
                        self.goal_position.x,
                        self.goal_position.y,
                    )
                    return delta_x, delta_y
                i += 1

            for i in range(len(bot_objects)):
                if (props.diamonds > bot_objects[i].properties.diamonds and bot_objects[
                    i].properties.diamonds != 5 and i != idx_our_bot and distance_bot_list[i] == 3):
                    # time to avoid bots
                    if (bot_objects[i].position.x > board_bot.position.x) and (
                            bot_objects[i].position.y > board_bot.position.y):
                        up, right = False, False
                    elif (bot_objects[i].position.x > board_bot.position.x) and (
                            bot_objects[i].position.y < board_bot.position.y):
                        down, right = False, False
                    elif (bot_objects[i].position.x < board_bot.position.x) and (
                            bot_objects[i].position.y < board_bot.position.y):
                        left, down = False, False
                    elif (bot_objects[i].position.x < board_bot.position.x) and (
                            bot_objects[i].position.y > board_bot.position.y):
                        left, up = False, False
                    elif (bot_objects[i].position.x == board_bot.position.x):
                        if (bot_objects[i].position.y > board_bot.position.y):
                            up = False
                        else:
                            down = False
                    elif (bot_objects[i].position.y == board_bot.position.y):
                        if (bot_objects[i].position.x > board_bot.position.x):
                            right = False
                        else:
                            left = False

                    avoid = True

            # get the closest diamond
            goal_diamond = self.closest_diamond(board, board_bot, diamond_list)
            self.goal_position = goal_diamond["diamond"].position
            self.travel_method = goal_diamond["method"]

            if (props.diamonds == 4 and goal_diamond["diamond"].properties.points == 2):
                # find the closest blue dias available also considering base distance to dias
                blue_diamond_list = list(filter(lambda diamond: diamond.properties.points == 1, diamond_list))
                if (len(blue_diamond_list) > 0):
                    goal_diamond = self.closest_diamond(board, board_bot, blue_diamond_list)

                    # decide to go back to base immediately or grab another blue dias
                    if (goal_diamond["distance"] < to_base["distance"]):
                        self.goal_position = goal_diamond["diamond"].position
                        self.travel_method = goal_diamond["method"]
                    else:
                        self.goal_position = base
                        self.travel_method = to_base["method"]
                else:  # go to base, wont try to find blue dias
                    self.goal_position = base
                    self.travel_method = to_base["method"]

            # go to red button if diamond is scarce
            if (to_red_button["distance"] < goal_diamond["distance"] and goal_diamond["distance"] > 7):
                self.goal_position = red_button_objects[0].position
                self.travel_method = to_red_button["method"]

        if self.goal_position:
            # change goal to teleporter
            if (self.travel_method == 1):
                self.goal_position = teleport_objects[0].position
            elif (self.travel_method == 2):
                self.goal_position = teleport_objects[1].position

            delta_x, delta_y = get_direction(
                current_position.x,
                current_position.y,
                self.goal_position.x,
                self.goal_position.y,
            )

            if avoid:
                delta_x, delta_y = avoid_tele_base(current_position, up, down, left, right, board, delta_x, delta_y)

            while not board.is_valid_move(current_position, delta_x, delta_y):
                # to avoid error delta = 0 in case of bot gets teleported and goal position is set on the teleporter, whereas the bot is on the teleporter
                random_direction = random.choice([(1, 0), (0, 1), (-1, 0), (0, -1)])
                delta_x = random_direction[0]
                delta_y = random_direction[1]

        return delta_x, delta_y

# run shortcut
# python main.py --logic Coba --email=your_email@example.com --name=your_name --password=your_password --team etimo