from typing import Tuple, Optional, List
from math import dist, inf
from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from ..util import *


# Defensive clamp + most profitable + attack capability
class Snoopy(BaseLogic):
    def __init__(self):
        self.goal_position: Optional[Position] = None
        self.aim_for_teleporter = False
        self.diamondtargetpoint: Optional[int] = None

    # Calculate next move based on mixed greedy strategy
    def next_move(self, board_bot: GameObject, board: Board) -> Tuple[int, int]:
        props = board_bot.properties
        current_position = board_bot.position

        direction = [(1, 0), (0, 1), (-1, 0), (0, -1)]  # East, South, West, North
        # handling edge positions
        if current_position.x == 0:
            direction.remove((-1, 0))
        elif current_position.x == board.width - 1:
            direction.remove((1, 0))
        if current_position.y == 0:
            direction.remove((0, -1))
        elif current_position.y == board.height - 1:
            direction.remove((0, 1))

        # Detect all diamonds and teleporters in board
        diamonds = []
        teleporters = {}
        for object in board.game_objects:
            if object.type == "DiamondGameObject":
                diamonds.append(object)
            elif object.type == "TeleportGameObject":
                if object.properties.pair_id not in teleporters:
                    teleporters[object.properties.pair_id] = []
                teleporters[object.properties.pair_id].append(object)

        # find the nearest teleporter to the bot and its pair
        nearestTeleporter = None
        minDist = inf
        for key in teleporters:
            for teleporter in teleporters[key]:
                distTeleporterToBot = self.calculateDistance(
                    board_bot.position, teleporter.position
                )
                if distTeleporterToBot < minDist:
                    nearestTeleporter = teleporter
                    minDist = distTeleporterToBot
        nearestTeleporterIdx = teleporters[nearestTeleporter.properties.pair_id].index(
            nearestTeleporter
        )

        base = board_bot.properties.base
        if (
            props.diamonds == 5
            or (
                props.diamonds == 4
                and (
                    self.diamondtargetpoint == 2
                    or dist([base.x, base.y], [current_position.x, current_position.y])
                    < 2.9
                )
            )
        ) and current_position != board_bot.properties.base:
            # Setting base as the goal position if conditions are met
            self.goal_position = base

        else:
            # Finding the nearest teleporter from bot and its pair
            if nearestTeleporterIdx == 0:
                nearestTeleporterPair = teleporters[
                    nearestTeleporter.properties.pair_id
                ][1]
            else:
                nearestTeleporterPair = teleporters[
                    nearestTeleporter.properties.pair_id
                ][0]

            # Aim for the most profitable diamond
            target = self.getMostProfitable(
                board_bot, diamonds, nearestTeleporter, nearestTeleporterPair
            )
            # Setting the goal position based on the aim for teleporter condition and target diamond position
            self.goal_position = (
                target.position
                if not self.aim_for_teleporter
                else nearestTeleporter.position
            )

        # Detect other bots in board
        enemies = [
            bot
            for bot in board.bots
            if bot.properties.name != board_bot.properties.name
        ]

        # Filtering the direction if avoiding teleporter needed
        if not self.aim_for_teleporter:
            if (
                current_position.x + 1 == nearestTeleporter.position.x
                and current_position.y == nearestTeleporter.position.y
            ):
                direction.remove((1, 0))
            elif (
                current_position.x - 1 == nearestTeleporter.position.x
                and current_position.y == nearestTeleporter.position.y
            ):
                direction.remove((-1, 0))
            if (
                current_position.y + 1 == nearestTeleporter.position.y
                and current_position.x == nearestTeleporter.position.x
            ):
                direction.remove((0, 1))
            elif (
                current_position.y - 1 == nearestTeleporter.position.y
                and current_position.x == nearestTeleporter.position.x
            ):
                direction.remove((0, -1))

        # Calculating move direction to goal position
        x_clamp = clamp(self.goal_position.x - current_position.x, -1, 1)
        y_clamp = clamp(self.goal_position.y - current_position.y, -1, 1)

        # Checking enemy position
        for enemy in enemies:
            # Checking if enemy's position is within 1.5 distance (8 cells around bot), if so proceed to next step
            if (
                dist(
                    [enemy.position.x, enemy.position.y],
                    [current_position.x, current_position.y],
                )
                <= 1.5
            ):  # sqrt(2) = 1.414
                # Calculating the direction to enemy
                enemy_x = clamp(enemy.position.x - current_position.x, -1, 1)
                enemy_y = clamp(enemy.position.y - current_position.y, -1, 1)

                # If bot has more diamonds than enemy, then attack the enemy
                if props.diamonds > enemy.properties.diamonds:
                    if enemy.position.x == current_position.x and enemy_y == y_clamp:
                        return 0, y_clamp
                    elif enemy.position.y == current_position.y and enemy_x == x_clamp:
                        return x_clamp, 0
                # Else, avoid the enemy
                else:
                    if enemy_x != 0 and (enemy_x, 0) in direction:
                        direction.remove((enemy_x, 0))
                    if enemy_y != 0 and (0, enemy_y) in direction:
                        direction.remove((0, enemy_y))

        # If bot is stuck, calculate the direction to goal position immediately
        if len(direction) == 0:
            if x_clamp != 0:
                y_clamp = 0
            return x_clamp, y_clamp

        # If bot is not stuck, calculate the direction to goal position based on the available direction
        else:
            if (x_clamp, 0) in direction:
                return x_clamp, 0
            elif (0, y_clamp) in direction:
                return 0, y_clamp
            # If there's no overlapping direction with goal direction, then use the first available direction
            else:
                return direction[0]

    def calculateDistance(self, position1: Position, position2: Position):
        # Calculate distance between 2 Position
        return dist([position2.x, position2.y], [position1.x, position1.y])

    def getMostProfitable(
        self,
        bot: GameObject,
        diamonds: List[GameObject],
        nearestTeleporter: GameObject,
        nearestTeleporterPair: GameObject,
    ) -> GameObject:
        # Find the nearest diamond with most profit
        maxProfit = 0

        for diamond in diamonds:
            realdistToBot = self.calculateDistance(bot.position, diamond.position)
            altDistToBot = self.calculateDistance(
                nearestTeleporter.position, bot.position
            ) + self.calculateDistance(nearestTeleporterPair.position, diamond.position)

            # Compare the distance to diamond from bot through teleporter and directly
            if realdistToBot > 1.6 * altDistToBot:
                self.aim_for_teleporter = True
                distToBot = altDistToBot
            else:
                self.aim_for_teleporter = False
                distToBot = realdistToBot

            # Calculate the distance to base from diamond
            distToBase = self.calculateDistance(bot.properties.base, diamond.position)
            # Calculate the profit of the diamond
            profit = (diamond.properties.points) / (distToBot + distToBase)

            # Select the most profitable diamond
            if profit >= maxProfit:
                selectedDiamond = diamond
                maxProfit = profit
                self.diamondtargetpoint = diamond.properties.points

        return selectedDiamond
