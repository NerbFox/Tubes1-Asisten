import random
from typing import Optional

from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from ..util import get_direction


class DevilTears(BaseLogic):
    def __init__(self):
        self.goal_position: Optional[Position] = None
        self.current_direction = 0

    def getDistance(self, game: GameObject, board_bot: GameObject):
        # Calculate the distance between two game objects
        return abs(board_bot.position.x - game.position.x) + abs(
            board_bot.position.y - game.position.y
        )

    def getNearestDiamonds(self, board_bot: GameObject, board: Board):
        # Retrieve the nearest diamond coordinate
        if board_bot.properties.diamonds == 4:
            # Case diamonds == 4
            array_diamond = [
                diamonds
                for diamonds in board.diamonds
                if diamonds.properties.points == 1
            ]
            nearestDiamond = array_diamond[0]
            nearestDistance = self.getDistance(array_diamond[0], board_bot)
            for i in range(1, len(array_diamond)):
                if self.getDistance(array_diamond[i], board_bot) < nearestDistance:
                    nearestDistance = self.getDistance(array_diamond[i], board_bot)
                    nearestDiamond = array_diamond[i]
                if (
                    self.getDistance(array_diamond[i], board_bot) == nearestDistance
                    and array_diamond[i].properties.points
                    > nearestDiamond.properties.points
                ):
                    nearestDiamond = array_diamond[i]
        else:
            array_diamond = [diamonds for diamonds in board.diamonds]
            nearestDiamond = array_diamond[0]
            nearestDistance = self.getDistance(array_diamond[0], board_bot)
            for i in range(1, len(array_diamond)):
                if self.getDistance(array_diamond[i], board_bot) < nearestDistance:
                    nearestDistance = self.getDistance(array_diamond[i], board_bot)
                    nearestDiamond = array_diamond[i]
                if (
                    self.getDistance(array_diamond[i], board_bot) == nearestDistance
                    and array_diamond[i].properties.points
                    > nearestDiamond.properties.points
                ):
                    nearestDiamond = array_diamond[i]
        return nearestDiamond

    def getTeleporter(self, board: Board):
        # Retrieve teleporters data
        teleporter = []
        for i in board.game_objects:
            if i.type == "TeleportGameObject":
                teleporter.append(i)
        return teleporter

    def getResetButton(self, board: Board):
        # Retrieve reset button data
        for i in board.game_objects:
            if i.type == "DiamondButtonGameObject":
                return i

    def next_move(self, board_bot: GameObject, board: Board):
        # Input next move
        props = board_bot.properties
        current_position = board_bot.position
        # Finding each distance
        reset_coor = self.getResetButton(board)
        reset_distance = self.getDistance(reset_coor, board_bot)

        diamond_coor = self.getNearestDiamonds(board_bot, board)
        diamond_distance = self.getDistance(diamond_coor, board_bot)

        base = board_bot.properties.base
        base_distance = abs(base.x - board_bot.position.x) + abs(
            base.y - board_bot.position.y
        )

        # logic
        if board_bot.properties.milliseconds_left // 1000 - 1 > base_distance:
            if props.diamonds == 5:
                # Move to base
                self.goal_position = base
            elif props.diamonds >= 3:
                if diamond_distance > base_distance and reset_distance > base_distance:
                    self.goal_position = base
                elif diamond_distance > reset_distance:
                    self.goal_position = reset_coor.position
                else:
                    self.goal_position = diamond_coor.position
            else:
                if reset_distance < diamond_distance:
                    self.goal_position = reset_coor.position
                else:
                    self.goal_position = diamond_coor.position
        else:
            self.goal_position = base

        delta_x, delta_y = get_direction(
            current_position.x,
            current_position.y,
            self.goal_position.x,
            self.goal_position.y,
        )

        teleporter = self.getTeleporter(board)
        # Teleporter position handling
        if teleporter[0].position.y == self.goal_position.y and (
            current_position.y <= teleporter[0].position.y <= self.goal_position.y
            or current_position.y >= teleporter[0].position.y >= self.goal_position.y
        ):
            if current_position.x == teleporter[0].position.x:
                if current_position.x == 0:
                    return 1, 0
                else:
                    return -1, 0
            if current_position.y > teleporter[0].position.y:
                return 0, -1
            elif current_position.y < teleporter[0].position.y:
                return 0, 1
        if teleporter[1].position.y == self.goal_position.y and (
            current_position.y <= teleporter[0].position.y <= self.goal_position.y
            or current_position.y >= teleporter[0].position.y >= self.goal_position.y
        ):
            if current_position.x == teleporter[1].position.x:
                if current_position.x == 0:
                    return 1, 0
                else:
                    return -1, 0
            if current_position.y > teleporter[1].position.y:
                return 0, -1
            elif current_position.y < teleporter[1].position.y:
                return 0, 1

        return delta_x, delta_y
