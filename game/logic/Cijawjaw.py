import heapq
from typing import Optional, List, Tuple

from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from ..util import get_direction

class CijawjawLogic(BaseLogic):
    def __init__(self):
        self.directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        self.goal_position: Optional[Position] = None
        self.current_direction = 0
    
    def next_move(self, board_bot: GameObject, board: Board):
        props = board_bot.properties
        current_position = board_bot.position

        temp: List[GameObject] = [
            d for d in board.game_objects if d.type == "DiamondButtonGameObject"
        ]
        button: GameObject = temp[0]
        button_distance = abs(button.position.x - current_position.x) + abs(button.position.y - current_position.y)

        tele: List[GameObject] = [
            d for d in board.game_objects if d.type == "TeleportGameObject"
        ]
        teleport1: GameObject = tele[0]
        teleport2: GameObject = tele[1]

        if props.diamonds == 5:
            # Move to base
            base = board_bot.properties.base
            self.goal_position = base
        else:
            self.goal_position = None
        
        current_position = board_bot.position
        if self.goal_position:
            # We are aiming for a specific position, calculate delta
            delta_x, delta_y = get_direction(
                current_position.x,
                current_position.y,
                self.goal_position.x,
                self.goal_position.y,
            )
        else:
            # Create a list to use as a priority queue
            diamonds_queue = []
            for index, diamond in enumerate(board.diamonds):
                distance = abs(diamond.position.x - current_position.x) + abs(diamond.position.y - current_position.y)
                # Use the distance as the priority
                heapq.heappush(diamonds_queue, (distance, index))

            # Get the diamond with the smallest distance
            if props.diamonds == 4:
                min_distance, nearest_diamond_index = heapq.heappop(diamonds_queue)
                # if the distance to the base is nearer than the nearest diamond, move to the base
                if (abs(props.base.x - current_position.x) + abs(props.base.y - current_position.y)) < min_distance and props.diamonds != 0:
                    self.goal_position = props.base
                else:
                    # Check if the nearest diamond has 1 point
                    if board.diamonds[nearest_diamond_index].properties.points == 1:
                        self.goal_position = board.diamonds[nearest_diamond_index].position
                    else:
                        # If the nearest diamond does not have 1 point, find the next nearest diamond
                        while board.diamonds[nearest_diamond_index].properties.points != 1 and diamonds_queue:
                            min_distance, nearest_diamond_index = heapq.heappop(diamonds_queue)
                        self.goal_position = board.diamonds[nearest_diamond_index].position
            else:          
                min_distance, nearest_diamond_index = heapq.heappop(diamonds_queue)
                if (abs(props.base.x - current_position.x) + abs(props.base.y - current_position.y)) < min_distance and props.diamonds != 0:
                        self.goal_position = props.base
                elif button_distance < min_distance:
                        self.goal_position = button.position
                else:
                    self.goal_position = board.diamonds[nearest_diamond_index].position

            # if the distance to the base is the same with the time left, move to the base
            if (props.milliseconds_left / 1000) <= (abs(props.base.x - current_position.x) + abs(props.base.y - current_position.y) + 2) and props.diamonds != 0:
                self.goal_position = props.base
            
            if (props.milliseconds_left / 1000) < 2 and current_position == props.base:
                delta_x, delta_y = 0, 1
            
            if self.goal_position == props.base:
                teleport_in_path = self.is_teleport_in_path(current_position, props.base, teleport1, teleport2)
                if teleport_in_path:
                    # Choose a new goal position on the opposite side of the teleport
                    self.goal_position = self.get_opposite_position(current_position, teleport_in_path)

            delta_x, delta_y = get_direction(
                current_position.x,
                current_position.y,
                self.goal_position.x,
                self.goal_position.y,
            )

        return delta_x, delta_y

    def is_teleport_in_path(self, start_position: Position, end_position: Position, teleport1: GameObject, teleport2: GameObject) -> Optional[GameObject]:
        """
        Check if a teleport is in the path between two positions.
        Returns the teleport GameObject if it is, otherwise returns None.
        """
        path_direction = get_direction(start_position.x, start_position.y, end_position.x, end_position.y)
        
        if self.is_between(start_position, teleport1.position, end_position, path_direction):
            return teleport1
        elif self.is_between(start_position, teleport2.position, end_position, path_direction):
            return teleport2
        else:
            return None

    def is_between(self, start_position: Position, middle_position: Position, end_position: Position, path_direction: Tuple[int, int]) -> bool:
        """
        Check if a position is between two other positions in a given direction.
        """
        return (
            start_position.x <= middle_position.x <= end_position.x or start_position.x >= middle_position.x >= end_position.x
        ) and (
            start_position.y <= middle_position.y <= end_position.y or start_position.y >= middle_position.y >= end_position.y
        )

    def get_opposite_position(self, current_position: Position, teleport_in_path: GameObject) -> Position:
        """
        Get a new goal position on the opposite side of the teleport.
        """
        teleport_position = teleport_in_path.position
        delta_x, delta_y = get_direction(current_position.x, current_position.y, teleport_position.x, teleport_position.y)
        new_goal_position = Position(teleport_position.x + delta_x, teleport_position.y + delta_y)
        return new_goal_position