from typing import Optional, List, Tuple

from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from ..util import *
import random


def findTeleportandRedButton(game_objects: List[GameObject]):
    teleport_pairs = {}
    redbutton = None
    for game_object in game_objects:
        if game_object.type == "TeleportGameObject":
            pair_id = game_object.properties.pair_id
            position = game_object.position
            if pair_id in teleport_pairs:
                teleport_pairs[pair_id].append(position)
            else:
                teleport_pairs[pair_id] = [position]
        elif game_object.type == "DiamondButtonGameObject":
            redbutton = game_object.position

    return [
        (pair[0], pair[1]) for pair in teleport_pairs.values() if len(pair) == 2
    ], redbutton


def findDistance(
    current: Position, teleport: List[Tuple[Position, Position]], target: Position
):
    tp_close_to_current = [None for _ in range(len(teleport))]
    distance_to_tp = [100 for _ in range(len(teleport))]
    otherside_tp = [None for _ in range(len(teleport))]
    otherside_tp_to_target = [100 for _ in range(len(teleport))]

    for i in range(len(teleport)):
        for j in range(2):
            total = abs(teleport[i][j].x - current.x) + abs(
                teleport[i][j].y - current.y
            )
            if total < distance_to_tp[i] and total != 0:
                distance_to_tp[i] = total
                tp_close_to_current[i] = teleport[i][j]
                for k in range(2):
                    if k != j:
                        otherside_tp[i] = teleport[i][k]
                        other = abs(teleport[i][k].x - target.x) + abs(
                            teleport[i][k].y - target.y
                        )
                        otherside_tp_to_target[i] = other

    tp_most_efficient = 100
    tp_entry = None
    for i in range(len(teleport)):
        if distance_to_tp[i] + otherside_tp_to_target[i] < tp_most_efficient:
            tp_most_efficient = distance_to_tp[i] + otherside_tp_to_target[i]
            tp_entry = tp_close_to_current[i]

    current_to_target = abs(current.x - target.x) + abs(current.y - target.y)

    if tp_most_efficient > current_to_target:
        distance = current_to_target
        return target, distance, False
    else:
        distance = tp_most_efficient
        return tp_entry, distance, True


def findCluster(
    current: GameObject, diamonds: List[GameObject], cluster_distance_threshold: int
):
    clusters = []
    for diamond in diamonds:
        added_to_cluster = False
        for cluster in clusters:
            if any(
                findDistance(diamond.position, [], other_diamond.position)[1]
                <= cluster_distance_threshold
                for other_diamond in cluster
            ):
                cluster.append(diamond)
                added_to_cluster = True
                break
        if not added_to_cluster:
            clusters.append([diamond])

    def cluster_efficiency(cluster):
        distance_to_cluster = min(
            findDistance(current.position, [], d.position)[1] for d in cluster
        )
        internal_cluster_distance = sum(
            findDistance(d1.position, [], d2.position)[1]
            for d1 in cluster
            for d2 in cluster
            if d1 != d2
        )
        distance_to_base = (
            min(
                findDistance(d.position, [], current.properties.base)[1]
                for d in cluster
            )
            + internal_cluster_distance
        )
        total_value = sum(d.properties.points for d in cluster)
        return total_value / (
            distance_to_cluster + internal_cluster_distance + distance_to_base
        )

    best_cluster = max(clusters, key=cluster_efficiency, default=[])
    if best_cluster:
        target_diamond = min(
            best_cluster,
            key=lambda d: findDistance(current.position, [], d.position)[1],
        )
        efficiency = cluster_efficiency(best_cluster)
        total_score = sum(d.properties.points for d in best_cluster)
        return target_diamond, efficiency, total_score
    else:
        return None, 0, 0


def findTarget(
    current: GameObject,
    teleport: List[Tuple[Position, Position]],
    diamonds: List[GameObject],
    redButton: Position,
    board: Board,
):
    remaining_diamonds = len(diamonds)
    remaining_inventory = (
        current.properties.inventory_size - current.properties.diamonds
    )

    if remaining_diamonds <= 3:
        red_button_target, distance_to_red_button, is_tp_red_button = findDistance(
            current.position, teleport, redButton
        )
        if distance_to_red_button < remaining_diamonds:
            return red_button_target, is_tp_red_button

    cluster_target, cluster_efficiency, expected = findCluster(current, diamonds, 3)
    distance_diamond_blue = 100
    distance_diamond_red = 100
    target_blue = None
    target_red = None
    is_tp_red = False
    is_tp_blue = False

    for diamond in diamonds:
        temp_target, temp_distance, temp_tp = findDistance(
            current.position, teleport, diamond.position
        )
        if diamond.properties.points == 1:
            if temp_distance < distance_diamond_blue:
                distance_diamond_blue = temp_distance
                target_blue = temp_target
                is_tp_blue = temp_tp
        else:
            if temp_distance < distance_diamond_red:
                distance_diamond_red = temp_distance
                target_red = temp_target
                is_tp_red = temp_tp

    base_target, _, is_back_tp = findDistance(
        current.position, teleport, current.properties.base
    )

    if target_red:
        base_target, distance_base_red, _ = findDistance(
            target_red, teleport, current.properties.base
        )
        value = 1
        calculated_distance = distance_base_red
    if target_blue:
        base_target, distance_base_blue, _ = findDistance(
            target_blue, teleport, current.properties.base
        )
        value = 2
        calculated_distance = distance_base_blue

    red_button_target, distance_to_red_button, is_tp_red_button = findDistance(
        current.position, teleport, redButton
    )
    should_press_red_button = False

    if min(distance_diamond_blue, distance_diamond_red) >= distance_to_red_button + 3:
        should_press_red_button = True
    if should_press_red_button:
        return red_button_target, is_tp_red_button

    if (
        cluster_target
        and cluster_efficiency > value / calculated_distance
        and expected <= remaining_inventory
    ):
        _, calculated_distance, temp = findDistance(
            current.position, teleport, cluster_target.position
        )
        return cluster_target.position, temp

    if distance_diamond_blue < distance_diamond_red - 2:
        if distance_base_blue + distance_diamond_blue > round(
            current.properties.milliseconds_left / 1000
        ):
            return base_target, is_back_tp
        else:
            return target_blue, is_tp_blue
    else:
        if distance_base_red + distance_diamond_red > round(
            current.properties.milliseconds_left / 1000
        ):
            return base_target, is_back_tp
        else:
            if current.properties.diamonds < current.properties.inventory_size - 1:
                return target_red, is_tp_red
            else:
                if distance_base_blue + distance_diamond_blue > round(
                    current.properties.milliseconds_left / 1000
                ):
                    return base_target, is_back_tp
                else:
                    return target_blue, is_tp_blue


def findQuadran(current: Position, target: Position):
    # 10 means vertically, -10 means horizontally
    direction_quadran = 10
    if current.x > target.x:
        if current.y > target.y:
            direction_quadran = 2
        elif current.y < target.y:
            direction_quadran = 3
        else:
            direction_quadran = -10
    elif current.x < target.x:
        if current.y > target.y:
            direction_quadran = 1
        elif current.y < target.y:
            direction_quadran = 4
        else:
            direction_quadran = -10

    return direction_quadran


def isTeleportInterupt(current: Position, teleport: Position, target: Position):
    quadran = findQuadran(current, target)

    if quadran == 10:
        if current.x == teleport.x and current.x == target.x:
            if current.y > target.y:
                if teleport.y < current.y and teleport.y > target.y:
                    return True, quadran
                else:
                    return False, quadran
            else:
                if teleport.y > current.y and teleport.y < target.y:
                    return True, quadran
                else:
                    return False, quadran
        else:
            return False, quadran

    elif quadran == -10:
        if current.y == teleport.y and current.y == target.y:
            if current.x > target.x:
                if teleport.x < current.x and teleport.x > target.x:
                    return True, quadran
                else:
                    return False, quadran
            else:
                if teleport.x > current.x and teleport.x < target.x:
                    return True, quadran
                else:
                    return False, quadran
        else:
            return False, quadran

    else:
        if current.y == teleport.y:
            if quadran == 1 or quadran == 4:
                if teleport.x > current.x and teleport.x < target.x:
                    return True, quadran
                else:
                    return False, quadran
            elif quadran == 2 or quadran == 3:
                if teleport.x > current.x and teleport.x < target.x:
                    return True, quadran
                else:
                    return False, quadran
        else:
            if teleport.x == target.x:
                if quadran == 1 or quadran == 2:
                    if teleport.y < current.y and teleport.y > target.y:
                        return True, quadran
                    else:
                        return False, quadran
                elif quadran == 3 or quadran == 4:
                    if teleport.y > current.y and teleport.y < target.y:
                        return True, quadran
                    else:
                        return False, quadran
            else:
                return False, quadran


def ignoreTeleport(
    current: Position,
    teleport: List[Tuple[Position, Position]],
    target: Position,
    board: Board,
):
    result: Position = target

    is_teleport_interupt, quadran = False, None
    teleport_crash = None

    for i in range(len(teleport)):
        for j in range(2):
            temp_will, temp_quadran = isTeleportInterupt(
                current, teleport[i][j], target
            )
            if temp_will:
                teleport_crash = teleport[i][j]
                is_teleport_interupt = temp_will
                quadran = temp_quadran
                break

    if is_teleport_interupt:
        if quadran == 10:
            if current.x == 0:
                result.x = current.x + 1
                result.y = current.y
            elif current.x == board.width - 1:
                result.x = current.x - 1
                result.y = current.y
            else:
                result.x = random.choice([current.x + 1, current.x - 1])
                result.y = current.y
        elif quadran == -10:
            if current.y == 0:
                result.x = current.x
                result.y = current.y + 1
            elif current.y == board.height - 1:
                result.x = current.x
                result.y = current.y - 1
            else:
                result.x = current.x
                result.y = random.choice([current.y + 1, current.y - 1])
        elif quadran == 1:
            if current.x == teleport_crash.x - 1:
                result.x = current.x
                result.y = current.y - 1
            elif current.x == teleport_crash.x:
                result.x = current.x
                result.y = current.y - 1
        elif quadran == 2:
            if current.x == teleport_crash.x + 1:
                result.x = current.x
                result.y = current.y - 1
            elif current.x == teleport_crash.x:
                result.x = current.x
                result.y = current.y - 1
        elif quadran == 3:
            if current.x == teleport_crash.x + 1:
                result.x = current.x
                result.y = current.y + 1
            elif current.x == teleport_crash.x:
                result.x = current.x
                result.y = current.y + 1
        elif quadran == 4:
            if current.x == teleport_crash.x - 1:
                result.x = current.x
                result.y = current.y + 1
            elif current.x == teleport_crash.x:
                result.x = current.x
                result.y = current.y + 1

    return result


class AkiongLogic(BaseLogic):
    def __init__(self):
        self.directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        self.goal_position: Optional[Position] = None
        self.current_direction = 0

    def next_move(self, board_bot: GameObject, board: Board):
        teleport, redbutton = findTeleportandRedButton(board.game_objects)

        target, is_teleport = findTarget(
            board_bot, teleport, board.diamonds, redbutton, board
        )

        if not is_teleport:
            target = ignoreTeleport(board_bot.position, teleport, target, board)

        if target is board_bot.position:
            target = board_bot.properties.base

        props = board_bot.properties
        if props.diamonds == props.inventory_size:
            base = board_bot.properties.base
            self.goal_position = base
        else:
            self.goal_position = None

        current_position = board_bot.position

        if self.goal_position:
            delta_x, delta_y = get_direction(
                current_position.x,
                current_position.y,
                self.goal_position.x,
                self.goal_position.y,
            )
        else:
            delta_x, delta_y = get_direction(
                current_position.x,
                current_position.y,
                target.x,
                target.y,
            )

        if delta_x == 0 and delta_y == 0:
            delta_x, delta_y = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])

        return delta_x, delta_y
