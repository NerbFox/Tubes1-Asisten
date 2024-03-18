import random
from typing import Optional, List

from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from ..util import clamp, position_equals

# Modified get direction function
def get_direction(current_x, current_y, dest_x, dest_y, h_priority):
    delta_x = clamp(dest_x - current_x, -1, 1)
    delta_y = clamp(dest_y - current_y, -1, 1)
    if h_priority:
        if delta_x != 0:
            delta_y = 0
    else:
        if delta_y != 0:
            delta_x = 0
    return (delta_x, delta_y)

# Distance counting functions
def distance(p1: Position, p2: Position):
    return abs(p1.x - p2.x) + abs(p1.y - p2.y)

def distance_tp(src: Position, dest: Position, close_tp: Position, far_tp: Position):
    return distance(src, close_tp) + distance(far_tp, dest)

def min_distance(src: Position, dest: Position, close_tp: Position, far_tp: Position):
    return min(distance(src, dest), distance_tp(src, dest, close_tp, far_tp))

# Teleporter functions
def teleporter_positions(board: Board):
    teleporters = []
    for game_object in board.game_objects:
        if (game_object.type == "TeleportGameObject"):
            teleporters.append(game_object.position)
    return teleporters

def blocked_by_teleporter(position: Position, board: Board):
    teleporters = teleporter_positions(board)
    return (position_equals(teleporters[0], position) or position_equals(teleporters[1], position))

# Red button finder
def red_button(board_bot: GameObject, board: Board, close_tp: Position, far_tp: Position):
    for game_object in board.game_objects:
        if (game_object.type == "DiamondButtonGameObject"):
            red_button = game_object.position
            break

    total_distance_normal = distance(board_bot.position, red_button)
    total_distance_tp = distance(board_bot.position, close_tp) + distance(far_tp, red_button)

    return red_button if ((total_distance_normal <= total_distance_tp) or position_equals(board_bot.position, close_tp)) else close_tp 

# Cluster functions
def within_cluster(p1: Position, p2: Position):
    return (abs(p1.x - p2.x) < 3 and abs(p1.y - p2.y) < 3)

def count_diamond_cluster(diamond: GameObject, diamonds: List[GameObject]):
    sum = diamond.properties.points
    for diamond2 in diamonds:
        if (within_cluster(diamond.position, diamond2.position) and not(position_equals(diamond.position, diamond2.position))):
            sum += diamond2.properties.points
    return sum

# Find best cluster
def best_cluster(board_bot: GameObject, board: Board, close_tp: Position, far_tp: Position):
    diamonds = board.diamonds
    props = board_bot.properties

    best_cluster = diamonds[0]
    min_distance_points_ratio = 10000
    through_tp = False

    for diamond in diamonds:
        if (props.diamonds == 4 and diamond.properties.points == 2):
            continue

        total_diamonds = count_diamond_cluster(diamond, diamonds)

        total_distance_normal = distance(board_bot.position, diamond.position)
        total_distance_tp = distance(board_bot.position, close_tp) + distance(far_tp, diamond.position)
        total_distance = min(total_distance_normal, total_distance_tp)

        if ((total_distance / min(total_diamonds, props.inventory_size - props.diamonds)) < min_distance_points_ratio):
            min_distance_points_ratio = (total_distance / min(total_diamonds, props.inventory_size - props.diamonds))
            best_cluster = diamond
            through_tp = True if (total_distance == total_distance_tp) else False

    return close_tp if (through_tp and not(position_equals(board_bot.position, close_tp))) else best_cluster.position

# Find best cluster while returning to base
def best_cluster_base(board_bot: GameObject, board: Board, close_tp: Position, far_tp: Position):
    diamonds = board.diamonds
    props = board_bot.properties

    best_cluster = diamonds[0]
    min_distance_points_ratio = 10000
    through_tp = False

    for diamond in diamonds:
        if (props.diamonds == 4 and diamond.properties.points == 2):
            continue

        total_diamonds = count_diamond_cluster(diamond, diamonds)

        d_current_diamond = min_distance(board_bot.position, diamond.position, close_tp, far_tp)
        d_diamond_base = min_distance(diamond.position, board_bot.properties.base, close_tp, far_tp)
        total_distance = d_current_diamond + d_diamond_base

        if ((total_distance / min(total_diamonds, props.inventory_size - props.diamonds)) < min_distance_points_ratio):
            min_distance_points_ratio = (total_distance / min(total_diamonds, props.inventory_size - props.diamonds))
            best_cluster = diamond
            through_tp = True if (d_current_diamond == distance_tp(board_bot.position, diamond.position, close_tp, far_tp)) else False

    return close_tp if (through_tp and not(position_equals(board_bot.position, close_tp))) else best_cluster.position

# Direct the bot to base
def to_base(board_bot: GameObject, board: Board, close_tp: Position, far_tp: Position):
    base = board_bot.properties.base

    return_distance_normal = distance(board_bot.position, base)
    return_distance_tp = distance(board_bot.position, close_tp) + distance(far_tp, base)
    
    return base if (return_distance_normal < return_distance_tp or position_equals(board_bot.position, close_tp)) else close_tp

class BestClusterLogic(BaseLogic):
    def __init__(self):
        self.directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        self.h_priority = True
        self.goal_position: Optional[Position] = None
        self.current_direction = 0

    def next_move(self, board_bot: GameObject, board: Board):
        props = board_bot.properties
        current_position = board_bot.position
        base = board_bot.properties.base
        
        teleporters = teleporter_positions(board)
        close_tp = teleporters[0] if (distance(board_bot.position, teleporters[0]) < distance(board_bot.position, teleporters[1])) else teleporters[1]
        far_tp = teleporters[1] if (position_equals(close_tp, teleporters[0])) else teleporters[0]

        distance_to_base = min(distance(current_position, base), distance_tp(current_position, base, close_tp, far_tp))
        d_red_button = distance(red_button(board_bot, board, close_tp, far_tp), current_position)

        if (props.diamonds == 5): # Go to base
            self.goal_position = to_base(board_bot, board, close_tp, far_tp)
        elif (props.diamonds >= 3): # Find best cluster while returning
            cluster = best_cluster_base(board_bot, board, close_tp, far_tp)
            red = red_button(board_bot, board, close_tp, far_tp)

            d_current_cluster = min_distance(current_position, cluster, close_tp, far_tp)
            d_cluster_base = min_distance(cluster, base, close_tp, far_tp)
            d_red_button_base = min_distance(red, base, close_tp, far_tp)

            if (d_red_button < d_current_cluster and (d_red_button + d_red_button_base) < (distance_to_base + 5) and not(position_equals(red, close_tp))):
                self.goal_position = red # If red button is nearest
            elif (d_current_cluster + d_cluster_base) < distance_to_base + 5 and not(position_equals(cluster, close_tp)):
                self.goal_position = cluster # If taking a detour to the cluster doesnt take too long
            else:
                # If everything else is too far
                self.goal_position = to_base(board_bot, board, close_tp, far_tp)
        else:
            # Search for best cluster or nearest red button
            d_best_cluster = distance(best_cluster(board_bot, board, close_tp, far_tp), current_position)

            if (d_red_button < d_best_cluster and not(position_equals(red_button(board_bot, board, close_tp, far_tp), close_tp))):
                self.goal_position = red_button(board_bot, board, close_tp, far_tp)
            else:
                self.goal_position = best_cluster(board_bot, board, close_tp, far_tp)

        if ((props.milliseconds_left / 1000) - 2 <= distance_to_base): # Return to base in time
            self.goal_position = to_base(board_bot, board, close_tp, far_tp)

        if self.goal_position:
            # We are aiming for a specific position, calculate delta
            delta_x, delta_y = get_direction(
                current_position.x,
                current_position.y,
                self.goal_position.x,
                self.goal_position.y,
                self.h_priority
            )
            
            new_position = Position(x=(current_position.x + delta_x), y=(current_position.y + delta_y))
            # Check if destination isnt a teleporter, but blocked by a teleporter
            if (blocked_by_teleporter(new_position, board) and not(position_equals(self.goal_position, close_tp))):
                if (delta_x != 0): # If initially going horizontally, move vertically
                    delta_x = 0
                    self.h_priority = True
                    if (board.is_valid_move(current_position, delta_x, 1)): 
                        delta_y = 1
                    else:
                        delta_y = -1 # Go down if unable to go up (at the top of the board)
                else:
                    delta_y = 0
                    self.h_priority = False
                    if (board.is_valid_move(current_position, 1, delta_y)):
                        delta_x = 1
                    else:
                        delta_x = -1 # Go left if unable to go right (at the right edge of the board)
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