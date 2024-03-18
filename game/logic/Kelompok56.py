import random
from typing import Optional

from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from ..util import get_direction


class Kelompok56(BaseLogic):
    def __init__(self):
        self.directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        self.goal_position: Optional[Position] = None
        self.current_direction = 0

    def calc_distance(self, Position1: Position, Position2: Position) -> int: # no teleporters
        x, y = Position1.x - Position2.x, Position1.y - Position2.y
        if (x < 0): x *= -1
        if (y < 0): y *= -1
        return (x + y)

    def next_move(self, board_bot: GameObject, board: Board):
        props = board_bot.properties
        current_position = board_bot.position
        base = board_bot.properties.base
        # Analyze new state
        if ((props.diamonds == 5) or ((1000 * (self.calc_distance(current_position, base) + 3)) > board_bot.properties.milliseconds_left)):
            # Move to base
            self.goal_position = base
        else:
            self.goal_position = None
            diamond_list = board.diamonds

            # cari diamonds di jarak <= 5
            diamond_list_focus = [d for d in diamond_list if (self.calc_distance(current_position, d.position) <= 5)]
            # kalau tidak ada radiusnya dibesarkan
            if (len(diamond_list_focus) == 0): diamond_list_focus = [d for d in diamond_list if (self.calc_distance(current_position, d.position) <= 10)]

            # target diamond yang poinnya paling banyak dan jarak terpendek (tidak mempertimbangkan teleporter)
            target = None
            for i in range (len(diamond_list_focus)):
                if i == 0:
                    target = diamond_list_focus[0]
                elif (diamond_list_focus[i].properties.points > target.properties.points):
                    target = diamond_list_focus[i]
                elif ((self.calc_distance(current_position, diamond_list_focus[i].position) < self.calc_distance(current_position, target.position)) and (diamond_list_focus[i].properties.points == target.properties.points)):
                    target = diamond_list_focus[i]

            if target:
                self.goal_position = target.position

        if self.goal_position:
            # We are aiming for a specific position, calculate delta
            delta_x, delta_y = get_direction(
                current_position.x,
                current_position.y,
                self.goal_position.x,
                self.goal_position.y,
            )
            if ((delta_x == 0) and (delta_y == 0)): self.goal_position = None
        if not self.goal_position:
            # kode dari yang bot starter pack random lollll
            # kadang masih bisa ke sini kalau waktunya hampir habis (jalan-jalan disekitar base)
            # Roam around
            delta = self.directions[self.current_direction]
            delta_x = delta[0]
            delta_y = delta[1]
            if random.random() > 0.6:
                self.current_direction = (self.current_direction + 1) % len(
                    self.directions
                )
        return delta_x, delta_y