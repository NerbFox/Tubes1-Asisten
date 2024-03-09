import random
from typing import Optional

from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from ..util import get_direction

RETURN_TO_BASE_VALUE = 9999
TACKLE_VALUE = 10000
MAX_VALUE = 5000
MIN_VALUE = -1000

class AsistenLogic(BaseLogic):
    def __init__(self):
        self.directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        self.goal_position: Optional[Position] = None
        self.current_direction = 0

    def manhattan_distance(self, position1: Position, position2: Position) -> int:
        return abs(position1.x - position2.x) + abs(position1.y - position2.y)
    
    def positions_value(self, board_bot: GameObject, board: Board) -> dict:
        current_position = board_bot.position
        base_position = board_bot.properties.base
        props = board_bot.properties
        otherbots = board.bots
        otherbots_position = [bots.position for bots in otherbots]
        positions = {}
        
        # Must go to base if we have 5 diamonds
        if props.diamonds == 5:
            # Move to base
            positions[(base_position.x, base_position.y)] = RETURN_TO_BASE_VALUE
            
        # Diamonds
        diamonds = board.diamonds
        diamonds1 = [d.position for d in diamonds if d.properties.points == 1]
        diamonds2 = [d.position for d in diamonds if d.properties.points == 2]
        # calculate manhattan distance for each diamond
        for d in diamonds1:
            distance = self.manhattan_distance(current_position, d)
            positions[(d.x, d.y)] = MAX_VALUE - (distance)**2
        for d in diamonds2:
            distance = self.manhattan_distance(current_position, d)
            positions[(d.x, d.y)] = MAX_VALUE - (distance*0.8)**2
            
        # Teleport 
        
        # Base
        
        # Red Button
        # Enemy to be tackled if can_tackle
        # for directions in self.directions:
        #     for other in otherbots_position:
        #         if other.x == current_position + directions[0] and other.y == current_position + directions[1] :
        #             positions[(other.x,other.y)] = TACKLE_VALUE
    
        if len(positions) == 0:
            # random move
            random_direction = random.choice(self.directions)
            positions[(random_direction[0], random_direction[1])] = MIN_VALUE
            
        return positions

    def best_position(self, board_bot: GameObject, board: Board) -> Position:
        positions_dict = self.positions_value(board_bot, board)
        best_position = max(positions_dict, key=positions_dict.get)
        return Position(best_position[0], best_position[1])

    def movable_positions_value(self, board_bot: GameObject, board: Board) -> dict:
        best_position = self.best_position(board_bot, board)
        current_position = board_bot.position
        movable_positions = {}
        for direction in self.directions:
            new_position = Position(
                current_position.x + direction[0],
                current_position.y + direction[1],
            )
            if board.is_valid_move(current_position, direction[0], direction[1]):
                distance = self.manhattan_distance(best_position, new_position)
                movable_positions[(new_position.x, new_position.y)] = MAX_VALUE - distance
        return movable_positions

    def goal_position(self, movable_positions: dict) -> Position:
        p = max(movable_positions, key=movable_positions.get)
        return Position(p[0], p[1])
        
    
    def next_move(self, board_bot: GameObject, board: Board):
        current_position = board_bot.position   
        movable_positions = self.movable_positions_value(board_bot, board)
        position = AsistenLogic.goal_position(self, movable_positions)
        
        delta_x, delta_y = get_direction(
            current_position.x,
            current_position.y,
            position.x,
            position.y,
        )
        return delta_x, delta_y
