from typing import Optional, List, Tuple

from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from time import sleep


class MrNaginskiLogic(BaseLogic):
    """
    Only calculate area of certain radius from base,
    every turn move to tile with the minimum average distance from diamonds within constrained area,
    will go to diamond if within 2 tiles away,
    will go to base if within 2 tiles away and have 3 or more diamonds
    will go to base if diamond in inventory is 4 or greater
    """

    def __init__(self):
        self.limit = 9

    def next_move(self, board_bot: GameObject, board: Board):

        self.board = board
        self.my_bot = board_bot

        if (self.my_bot.properties.milliseconds_left // 1000 < 2):
            print("Goodbye world, my journey ends here")

        if (self.my_bot.properties.milliseconds_left // 1000 <= self.distance_with_teleporter(self.my_bot.position,
                                                                                              self.my_bot.properties.base) + 2):
            print("The sun is setting, i better get back to base, otherwise i might not see my family again")
            return self.move_towards_base()

        constrained_diamonds = self.get_all_diamonds_within_limit(self.limit)
        if len(constrained_diamonds) == 0:
            print("The diamond around our tunnel is too sparse, let's explore further")
            constrained_diamonds = self.get_all_diamonds_within_limit(self.limit + 2)

        if len(constrained_diamonds) == 0:
            print("Our home is devoid of resources, i will make my way to the center, pray that i make it back")
            return self.move_towards_center()

        if len(constrained_diamonds) == 2:
            print("Of these two choices i'll take the closer one")
            return self.move_towards_with_teleporter(min(constrained_diamonds,
                                                         key=lambda diamond: self.distance_with_teleporter(
                                                             self.my_bot.position, diamond.position)).position)

        all_diamonds = self.board.diamonds
        diamonds_within_one = self.diamonds_within_n(1, all_diamonds)
        diamonds_within_two = self.diamonds_within_n(2, all_diamonds)
        diamonds_within_one = list(filter(lambda
                                              diamond: self.my_bot.properties.diamonds + diamond.properties.points < self.my_bot.properties.inventory_size,
                                          diamonds_within_one))
        diamonds_within_two = list(filter(lambda
                                              diamond: self.my_bot.properties.diamonds + diamond.properties.points < self.my_bot.properties.inventory_size,
                                          diamonds_within_two))

        if len(diamonds_within_one) > 0:

            for diamond in diamonds_within_one:
                if (diamond.properties.points == 2):
                    print("I'll go for the diamond worth two that is next to me")
                    return self.move_towards_with_teleporter(diamond.position)

            best_one_tile_away_diamond = min(diamonds_within_one,
                                             key=lambda diamond: self.calculate_tile_avg_diamond_distance(
                                                 diamond.position, constrained_diamonds))
            print("I'll go for this diamond next to me")
            return self.move_towards_with_teleporter(best_one_tile_away_diamond.position)

        elif len(diamonds_within_two) > 0:

            for diamond in diamonds_within_two:
                if (diamond.properties.points == 2):
                    print("I'll go for the diamond worth two close to me")
                    return self.move_towards_with_teleporter(diamond.position)

            best_two_tile_away_diamond = min(diamonds_within_two,
                                             key=lambda diamond: self.calculate_tile_avg_diamond_distance(
                                                 diamond.position, constrained_diamonds))
            print("I'll go for this diamond close to me")
            return self.move_towards_with_teleporter(best_two_tile_away_diamond.position)

        if (self.my_bot.properties.diamonds >= self.my_bot.properties.inventory_size - 1):
            print("My inventory is full, i better store the spoils of war")
            return self.move_towards_base()
        elif (self.distance_with_teleporter(self.my_bot.position,
                                            self.my_bot.properties.base) <= 2 and self.my_bot.properties.diamonds >= 3):
            print("I'm close to base and i have some diamonds to help my family buy food")
            return self.move_towards_base()
        elif (self.distance_with_teleporter(self.my_bot.position,
                                            self.my_bot.properties.base) <= 1 and self.my_bot.properties.diamonds >= 1):
            print("It's not much but i guess i'll store this diamond to my base")
            return self.move_towards_base()

        best_avg_tile = self.calculate_tile_with_minimum_avg_diamond_distance_around_tile(self.my_bot.position,
                                                                                          constrained_diamonds)
        print(f"According to my analysis i should head to {best_avg_tile}")
        return self.move_towards_with_teleporter(best_avg_tile)

    # Get telebroter
    def get_both_teleporter(self) -> Tuple[GameObject, GameObject]:
        teleporters = [d for d in self.board.game_objects if d.type == "TeleportGameObject"]
        if len(teleporters) != 2:
            return None, None
        return teleporters[0], teleporters[1]

    def get_closer_tele(self):

        my_pos = self.my_bot.position

        tele1, tele2 = self.get_both_teleporter()
        closer_tele = tele1 if (
                    self.distance(my_pos, tele1.position) > self.distance(my_pos, tele2.position)) else tele2
        return closer_tele

    # Calculate distance
    def distance(self, a: Position, b: Position) -> int:
        x = abs(a.x - b.x)
        y = abs(a.y - b.y)
        return x + y

    # Calculate closest distance between two points considering teleporter
    def distance_with_teleporter(self, a: Position, b: Position) -> int:
        tele1, tele2 = self.get_both_teleporter()

        closer_tele = tele1 if (self.distance(a, tele1.position) < self.distance(a, tele2.position)) else tele2
        other_tele = tele1 if (self.distance(a, tele1.position) > self.distance(a, tele2.position)) else tele2

        a_to_tele = self.distance(a, closer_tele.position)
        tele_to_b = self.distance(other_tele.position, b)

        classic_distance = self.distance(a, b)

        return min(classic_distance, a_to_tele + tele_to_b)

    # Movement Commands

    # Move Toward not considering teleporter
    def move_towards(self, dest: Position) -> Tuple[int, int]:
        delta_x = dest.x - self.my_bot.position.x
        delta_y = dest.y - self.my_bot.position.y

        direction = (0, 0)

        if abs(delta_x) > abs(delta_y):
            direction = (1 if delta_x > 0 else -1, 0)
        else:
            direction = (0, 1 if delta_y > 0 else -1)

        my_pos = self.my_bot.position

        out_of_bound_check = (my_pos.x + direction[0] >= 0 and my_pos.y + direction[1] >= 0 and my_pos.x + direction[
            0] < self.board.width + 1 and my_pos.y + direction[1] < self.board.height + 1)

        if (out_of_bound_check):
            return direction
        else:
            return (direction[0] * (-1), direction[1] * (-1))

    # Move Toward considering teleporter
    def move_towards_with_teleporter(self, dest: Position) -> Tuple[int, int]:

        my_pos = self.my_bot.position

        if (self.distance_with_teleporter(my_pos, dest) == self.distance(my_pos, dest)):
            print("Straight forward is the shortest way")
            return self.move_towards(dest)
        elif ((self.distance_with_teleporter(my_pos, dest) < self.distance(my_pos, dest))):
            print("Let's move to the closer teleporter")
            closer_tele = self.get_closer_tele()
            return self.move_towards(closer_tele.position)

    # Move to base
    def move_towards_base(self) -> Tuple[int, int]:
        return self.move_towards_with_teleporter(self.my_bot.properties.base)

    def move_towards_center(self) -> Tuple[int, int]:
        return self.move_towards_with_teleporter(Position(self.board.height // 2, self.board.width // 2))

    # Enemy Methods

    # Return a list of enemies
    def get_all_enemy(self) -> list[GameObject]:
        enemy_bot_list = self.board.bots
        enemy_bot_list.remove(self.my_bot)
        return enemy_bot_list

    def closest_enemy(self) -> GameObject:
        curr_closest = None
        curr_closest_distance = 30

        enemies = self.get_all_enemy()
        for enemy in enemies:
            if (self.distance_with_teleporter(self.my_bot.position, enemy.position) < curr_closest_distance):
                curr_closest_distance = self.distance_with_teleporter(self.my_bot.position, enemy.position)
                curr_closest = enemy
        return curr_closest

    def get_bot_index(self, target_bot: GameObject) -> int:

        bots = self.board.bots
        for i in range(len(bots)):
            if bots[i] == target_bot:
                return i

    # Constrained Board Bot
    def get_all_diamonds_within_limit(self, limit):
        diamonds = self.board.diamonds

        return list(
            filter(lambda x: self.distance_with_teleporter(x.position, self.my_bot.properties.base) <= limit, diamonds))

    # Calculate avg diamond distance to tile from list of diamonds
    def calculate_tile_avg_diamond_distance(self, tile: Position, diamonds: list[GameObject]):
        total_distance = 0

        for diamond in diamonds:
            total_distance += (self.distance_with_teleporter(diamond.position,
                                                             tile) * diamond.properties.points * diamond.properties.points) ** (
                                  0.25)

        return total_distance / len(diamonds)

    def calculate_tile_with_minimum_avg_diamond_distance_around_tile(self, tile: Position, diamonds: list[GameObject]):
        tiles = []
        tiles.append(Position(tile.y + 1, tile.x))
        tiles.append(Position(tile.y - 1, tile.x))
        tiles.append(Position(tile.y, tile.x + 1))
        tiles.append(Position(tile.y, tile.x - 1))

        return min(tiles, key=lambda x: self.calculate_tile_avg_diamond_distance(x, diamonds))

    # Diamonds within n distance from the player
    def diamonds_within_n(self, n: int, diamonds: list[GameObject]):
        return list(filter(lambda diamond: self.distance_with_teleporter(self.my_bot.position, diamond.position) <= n,
                           diamonds))