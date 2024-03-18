from typing import Optional, Literal
from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from ..util import clamp

class HighestBlockPerDistanceBotLogic(BaseLogic):
    def __init__(self):
        self.directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        self.goal_position: Optional[Position] = None
        self.current_direction = 0
        self.attack_other_bots = False
        self.time_based_retreat = True

    # get total point in block (3x3)
    def get_surroundings_points(self, diamond: tuple[Position, int], list_of_diamonds: list[tuple[Position, int]]) -> int:
        list_to_check = [(-1, 1), (0, 1), (1, 1), (-1, 0), (1, 0), (-1, -1), (0, -1), (1, -1)]
        points = diamond[1]
        for delta in list_to_check :
            coordinate_x = delta[0] + (diamond[0]).x
            coordinate_y = delta[1] + (diamond[0]).y
            for position, point in list_of_diamonds:
                if position.x == coordinate_x and position.y == coordinate_y:
                    points += point
        return points

    # check distance from to obj
    def get_distance(self, current_position: Position, target_position: Position) -> int:
        return abs(current_position.x - target_position.x) + abs(current_position.y - target_position.y)

    # calculate value of point and distance
    def calculate_benefit(self, point: int, distance: int) -> float :
        if distance == 0:
            return 0
        else :
            return (point / distance) * 100000
        
    # check for use teleport or not to reach target
    def is_teleporting_closer(self, bot_position: Position, target_position: Position, teleporter_pairs: list[tuple[Position, Position]]) -> tuple[bool, Optional[Position]]:
        direct_distance = self.get_distance(bot_position, target_position)

        for teleporter_pair in teleporter_pairs:
            teleporter1, teleporter2 = teleporter_pair
            distance_via_teleporter_1 = self.get_distance(bot_position, teleporter1) + self.get_distance(teleporter2, target_position)
            distance_via_teleporter_2 = self.get_distance(bot_position, teleporter2) + self.get_distance(teleporter1, target_position)

            if distance_via_teleporter_1 < direct_distance:
                return True, teleporter1
            elif distance_via_teleporter_2 < direct_distance:
                return True, teleporter2

        return False, None
    
    # prioritize y movement
    def get_direction_yfirst(self, current_x: int, current_y: int, dest_x: int, dest_y: int) -> tuple[int | Literal[0], int | Literal[0]]:
        delta_x = clamp(dest_x - current_x, -1, 1)
        delta_y = clamp(dest_y - current_y, -1, 1)
        if delta_y != 0:
            delta_x = 0
        return (delta_x, delta_y)
    
    # handling in case not moving
    def handle_not_moving(self, current_position: Position, board_width: int, board_height: int) -> tuple[int, int]:
        if current_position.x == 0:
            if current_position.y == 0:
                return 1, 0
            elif current_position.y == board_height - 1:
                return 0, -1
            else:
                return 0, -1 
        elif current_position.x == board_width - 1:
            if current_position.y == 0:
                return 0, 1
            elif current_position.y == board_height - 1:
                return -1, 0
            else:
                return 0, 1
        elif current_position.y == 0:
            return 1, 0
        elif current_position.y == board_height - 1:
            return -1, 0
        else:
            return 1, 0

    def next_move(self, board_bot: GameObject, board: Board):
        game_objects = [x for x in board.game_objects]
        diamonds = [(x.position, x.properties.points) for x in game_objects if x.type == "DiamondGameObject"]

        teleporter = [x for x in game_objects if x.type == "TeleportGameObject"]
        teleporter_pairs = []
        paired_ids = []
        for teleport in teleporter:
            if teleport.properties.pair_id not in paired_ids:
                pair = next((x for x in teleporter if x.properties.pair_id == teleport.properties.pair_id and x != teleport), None)
                if pair:
                    teleporter_pairs.append((teleport.position, pair.position))
                    paired_ids.append(teleport.properties.pair_id)

        temp = []
        for diamond in diamonds:
            surrounding_points = self.get_surroundings_points(diamond, diamonds)
            distance = self.get_distance(board_bot.position, diamond[0])
            benefit = self.calculate_benefit(surrounding_points, distance)
            temp.append((diamond[0], benefit, diamond[1], distance, surrounding_points))
        sorted_temp = sorted(temp, key=lambda x: x[1], reverse=True)

        props = board_bot.properties
        base = board_bot.properties.base
        distance_to_base = self.get_distance(board_bot.position, base)
        current_position = board_bot.position

        if props.diamonds == 5:
            self.goal_position = base
        else:
            if (props.diamonds == 4 and sorted_temp[0][2] == 2) or (props.diamonds >= 3 and distance_to_base < sorted_temp[0][3]):
                self.goal_position = base
            else:
                self.goal_position = sorted_temp[0][0]

        refresh_buttons = [x.position for x in game_objects if x.type == "DiamondButtonGameObject"]
        if self.goal_position != base:
            for button in refresh_buttons:
                distance_to_button = self.get_distance(current_position, button)

                if distance_to_button < self.get_distance(current_position, self.goal_position):
                    self.goal_position = button

        if self.time_based_retreat:
            if (board_bot.properties.milliseconds_left < (distance_to_base + 1.3) * (1000)) and (props.diamonds >= 1):
                self.goal_position = base

        is_closer, teleporter_to_use = self.is_teleporting_closer(board_bot.position, self.goal_position, teleporter_pairs)
        if is_closer:
            self.goal_position = teleporter_to_use
            
        #Attack to nearby enemy
        if self.attack_other_bots:
            bots = [x.position for x in game_objects if x.type == "BotGameObject" and x.id != board_bot.id]
            for bot in bots:
                for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    print(bot.x, bot.y)
                    if bot.x == current_position.x + dx and bot.y == current_position.y + dy:
                        return dx, dy

        if self.goal_position:
            delta_x, delta_y = self.get_direction_yfirst(
                current_position.x,
                current_position.y,
                self.goal_position.x,
                self.goal_position.y,
            )
        
        if delta_x == 0 and delta_y == 0:
            delta_x, delta_y = self.handle_not_moving(current_position, board.width, board.height)
        
        print(self.goal_position)
        return delta_x, delta_y
