import random
from typing import Optional

from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from ..models import Position


# Gets Information
def am_i_in_danger(bot, enemies):
    for enemy in enemies:
        if (
            abs(enemy.position.x - bot.position.x)
            + abs(enemy.position.y - bot.position.y)
            <= 2
        ):
            return True
    return False


def is_in_between(point1, point2, point3):
    return point1 <= point2 <= point3  # Check if point2 is between point1 and point3


def get_direction(current_x, current_y, dest_x, dest_y, board):
    teleports = get_teleport_info(board.game_objects)
    diamondButton = get_diamond_button(board.game_objects)
    bots = board.bots
    horizontal = True
    isDestDiaButton = (
        dest_x == diamondButton.position.x and dest_y == diamondButton.position.y
    )
    # Edge case where the bot, the diamond button, and the destination are in the same line on the edge of the board
    if (
        (
            is_in_between(current_x, diamondButton.position.x, dest_x)
            or is_in_between(dest_x, diamondButton.position.x, current_x)
        )
        and current_y == dest_y
        and current_y == diamondButton.position.y
        and not isDestDiaButton
    ):
        print("masuk sini")
        if current_y != board.height - 1:
            return (0, 1)
        else:
            return (0, -1)
    elif (
        (
            is_in_between(current_y, diamondButton.position.y, dest_y)
            or is_in_between(dest_y, diamondButton.position.y, current_y)
        )
        and current_x == dest_x
        and current_x == diamondButton.position.x
        and not isDestDiaButton
    ):
        print("masuk nih")
        if current_x != board.width - 1:
            return (1, 0)
        else:
            return (-1, 0)

    # This will avoid any diamond button on the way to the destionation
    if (
        (
            is_in_between(current_y, diamondButton.position.y, dest_y)
            or is_in_between(dest_y, diamondButton.position.y, current_y)
        )
        and (
            dest_x == diamondButton.position.x or current_y == diamondButton.position.y
        )
        and not isDestDiaButton
    ):
        print("anjay gannnn")
        horizontal = False

    for teleport in teleports:
        # Edge case where the bot, the teleport, and the destination are in the same line on the edge of the board
        if (
            (
                is_in_between(current_x, teleport.position.x, dest_x)
                or is_in_between(dest_x, teleport.position.x, current_x)
            )
            and current_y == dest_y
            and current_y == teleport.position.y
        ):
            if current_y != board.height - 1:
                return (0, 1)
            else:
                return (0, -1)
        elif (
            (
                is_in_between(current_y, teleport.position.y, dest_y)
                or is_in_between(dest_y, teleport.position.y, current_y)
            )
            and current_x == dest_x
            and current_x == teleport.position.x
        ):
            if current_x != board.width - 1:
                return (1, 0)
            else:
                return (-1, 0)

        # This will avoid any teleport on the way to the destionation=
        if (
            is_in_between(current_y, teleport.position.y, dest_y)
            or is_in_between(dest_y, teleport.position.y, current_y)
        ) and (dest_x == teleport.position.x or current_y == teleport.position.y):
            print("test gan")

            horizontal = False

    delta_x = clamp(dest_x - current_x, -1, 1)
    delta_y = clamp(dest_y - current_y, -1, 1)

    if delta_x != 0 and horizontal:
        delta_y = 0
    elif delta_y != 0 and not horizontal:
        delta_x = 0
    return (delta_x, delta_y)


def get_diamonds_info(game_objects: list):
    return [obj for obj in game_objects if obj.type == "DiamondGameObject"]


def get_teleport_info(game_objects: list):
    return [obj for obj in game_objects if obj.type == "TeleportGameObject"]


def get_time_left(game_objects: list):
    for item in game_objects:
        if item.type == "BotGameObject":
            return item.properties.milliseconds_left


def get_closest_diamond(pos: Position, diamonds: list):
    return min(
        diamonds,
        key=lambda d: abs(d.position.x - pos.x) + abs(d.position.y - pos.y),
    )


def check_if_should_go_for_diamond_button(bot, game_objects, diamonds):
    return (
        get_time_to_location(
            bot.position, get_closest_diamond_position(bot.position, diamonds)
        )
        - get_time_to_location(bot.position, get_diamond_button(game_objects).position)
        > 5000
    )


# Gets Location
def get_diamond_button(game_objects: list):
    for item in game_objects:
        if item.type == "DiamondButtonGameObject":
            return item


def get_closest_diamond_position(pos: Position, diamonds: list):
    return get_closest_diamond(pos, diamonds).position


def get_closest_blue_diamond_position(pos: Position, diamonds: list):
    return min(
        [d for d in diamonds if d.properties.points == 1],
        key=lambda d: abs(d.position.x - pos.x) + abs(d.position.y - pos.y),
    ).position


def get_second_closest_diamond(pos: Position, diamonds: list):
    return min(
        [
            d
            for d in diamonds
            if not position_equals(
                d.position, get_closest_diamond_position(pos, diamonds)
            )
        ],
        key=lambda d: abs(d.position.x - pos.x) + abs(d.position.y - pos.y),
    ).position


def get_closest_bot(pos: Position, bots: list):
    return min(
        bots,
        key=lambda b: abs(b.position.x - pos.x) + abs(b.position.y - pos.y),
    )


def get_closest_bot_to_diamond(diamond_pos: Position, bots: list):
    return min(
        bots,
        key=lambda b: abs(b.position.x - diamond_pos.x)
        + abs(b.position.y - diamond_pos.y),
    )


def get_ranked_robots(bots: list):
    return sorted(bots, key=lambda b: b.properties.diamonds, reverse=True)


def get_rank(bots: list, bot_id: int):
    sorted_bots = sorted(bots, key=lambda b: b.properties.diamonds, reverse=True)
    for i, bot in enumerate(sorted_bots):
        if bot.id == bot_id:
            return i + 1


def get_time_to_location(current: Position, dest: Position):
    return 1000 * (abs(dest.x - current.x) + abs(dest.y - current.y))


# Comparisons
def position_equals(a: Position, b: Position):
    return a.x == b.x and a.y == b.y


def clamp(n, smallest, largest):
    return max(smallest, min(n, largest))


def killable(my_bot: any, enemies: any, diamonds: any) -> Position:
    qualified_diamonds = []
    # Check if other bot is killable which is in a position where the closest diamond is the same as my bot and the other bot is exactly 1 tile closer to the diamond than our bot
    for enemy in enemies:
        if enemy.position == my_bot.position:
            continue

        my_bot_closest_diamond = get_closest_diamond_position(my_bot.position, diamonds)
        enemy_closest_diamond = get_closest_diamond_position(enemy.position, diamonds)
        if not position_equals(my_bot_closest_diamond, enemy_closest_diamond):
            continue
        elif (
            get_time_to_location(my_bot.position, my_bot_closest_diamond)
            - get_time_to_location(enemy.position, enemy_closest_diamond)
            == 1000
        ):
            qualified_diamonds.append(my_bot_closest_diamond)
    if len(qualified_diamonds) == 0:
        return my_bot.position
    return get_closest_diamond_position(my_bot.position, qualified_diamonds)


def suicide(my_bot: any, enemies: any, diamonds: any, dest_diamond: Position) -> bool:
    print("musuh", enemies)
    # Check if my bot is in an unsafe position which is in a position where the closest diamond is the same as some bots and my bot is exactly 1 tile closer to the diamond than the other bot
    for enemy in enemies:
        if enemy.position == my_bot.position:
            continue
        enemy_closest_diamond = get_closest_diamond_position(enemy.position, diamonds)
        if not position_equals(dest_diamond, enemy_closest_diamond):
            continue
        elif (
            get_time_to_location(enemy.position, dest_diamond) == 1000
            and get_time_to_location(my_bot.position, dest_diamond) == 1000
        ):
            return True
    return False


# 5x5 section yang paling banyak poin bukan diamond karna red diamond lebih worth it
def find_diamond_mine(diamonds: list, bot_position: Position):
    max_tile_diamonds = 0
    section = []
    for y in range(11):
        for x in range(11):
            tile_diamonds = sum(
                diamond.properties.points
                for diamond in diamonds
                if y <= diamond.position.y < y + 5 and x <= diamond.position.x < x + 5
            )
            if tile_diamonds > max_tile_diamonds:
                section = []
                max_tile_diamonds = tile_diamonds
                for diamond in diamonds:
                    if (
                        y <= diamond.position.y < y + 5
                        and x <= diamond.position.x < x + 5
                    ):
                        section.append(diamond)

    return section


def get_closest_diamond_in_mine(diamonds: list, bot_position: Position):
    return get_closest_diamond_position(
        bot_position, find_diamond_mine(diamonds, bot_position)
    )


# jalan pulang ada teleport yang ngebuat dia muter disitu situ aja

# python main.py --logic Greedy --email=your_email@example.com --name=your_name --password=your_password --team etimo


class QUEENLogic(BaseLogic):
    def __init__(self):
        self.directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        # Optional[Position] is a way to say that the value can be None
        self.goal_position: Optional[Position] = None
        self.current_direction = 0

    def next_move(self, board_bot: GameObject, board: Board):
        # store all diamond objects
        diamonds = board.diamonds
        # store the properties of our bot
        props = board_bot.properties

        # Check if inventory is empty and if diamond button is closer than the closest diamond
        if props.diamonds == 0:
            print("diamond 0")
            killable_pos = killable(board_bot, board.bots, diamonds)
            print("killable_pos", killable_pos)
            if check_if_should_go_for_diamond_button(
                board_bot,
                board.game_objects,
                find_diamond_mine(diamonds, board_bot.position),
            ):
                print("ke dia button")

                # Go to diamond button if the closest diamond mine is much further than the diamond button
                self.goal_position = get_diamond_button(board.game_objects).position
            elif killable_pos is not board_bot.position and get_time_to_location(
                board_bot.position, killable_pos
            ) <= get_time_to_location(
                board_bot.position,
                get_closest_diamond_in_mine(diamonds, board_bot.position),
            ):
                print("ke kill bot")

                self.goal_position = killable_pos
            elif not (
                get_time_to_location(
                    board_bot.position,
                    get_closest_diamond_in_mine(diamonds, board_bot.position),
                )
                - get_time_to_location(
                    board_bot.position,
                    get_closest_diamond_position(board_bot.position, diamonds),
                )
                > 5000
            ):
                print("ke diamond mine")
                self.goal_position = get_closest_diamond_in_mine(
                    diamonds, board_bot.position
                )
            else:
                print("ke diamond biasa")
                self.goal_position = get_closest_diamond_position(
                    board_bot.position, diamonds
                )
        elif (
            # Check if the inventory is full or there is not enough time to get back to the base. We do this so that in the last seconds, if our bot carries some diamonds and still looking for the closest diamond but dont have enough time to take those diamonds back to the base, it will go straigth to the base
            props.diamonds >= 5
            or (
                props.diamonds > 0
                and (
                    abs(
                        get_time_to_location(
                            board_bot.position, board_bot.properties.base
                        )
                        - get_time_left(board.game_objects)
                    )
                    <= 2000
                )
            )
        ):
            print("ke base")
            # Move to base
            base = board_bot.properties.base
            self.goal_position = base
        elif (
            # Check if the closest diamond is red diamond and our bot carries 4 diamonds already
            get_closest_diamond(board_bot.position, diamonds).properties.points == 2
            and props.diamonds == 4
        ):
            print("ke blue dia terdekat")
            # It will go to the closest blue diamond to fill the inventory
            self.goal_position = get_closest_blue_diamond_position(
                board_bot.position, diamonds
            )

        else:
            if check_if_should_go_for_diamond_button(
                board_bot,
                board.game_objects,
                diamonds,
            ):
                print("ke dia button edisi 2")
                # Go to diamond button to reset board so that enemies who are close to their base will have to change direction because their base changed
                self.goal_position = get_diamond_button(board.game_objects).position
            else:
                # Go to the closest diamond
                closest_diamond = get_closest_diamond_position(
                    board_bot.position, diamonds
                )
                if suicide(board_bot, board.bots, diamonds, closest_diamond) == True:
                    print("bahaya brow")
                    self.goal_position = get_second_closest_diamond(
                        board_bot.position, diamonds
                    )
                else:
                    print("amang")
                    self.goal_position = get_closest_diamond_position(
                        board_bot.position, diamonds
                    )
        # store the current position of our robot
        current_position = board_bot.position

        # if goal position exists, calculate the direction to go to the goal position
        if self.goal_position:
            # We are aiming for a specific position, calculate delta
            delta_x, delta_y = get_direction(
                current_position.x,
                current_position.y,
                self.goal_position.x,
                self.goal_position.y,
                board,
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
        print(f"delta_x: {delta_x}, delta_y: {delta_y}")
        print("goal", self.goal_position)
        return delta_x, delta_y