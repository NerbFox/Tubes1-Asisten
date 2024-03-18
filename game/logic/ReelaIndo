# Nama / NIM : Rayhan Ridhar Rahman / 13522160

from typing import Optional

from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position, List
from ..util import get_direction

# yes I have been so afraid
class TomerryLogic(BaseLogic):
    def __init__(self):
        self.goal_position: Optional[Position] = None
        self.goal: Optional[GameObject] = None
        self.portals: List[Position] = []
        self.wrath: bool = True

    def next_move(self, board_bot: GameObject, board: Board):
        props = board_bot.properties
        current_position = board_bot.position
        base = board_bot.properties.base

        self.update_portals(board, current_position)
            
        if props.diamonds == 5 or (board_bot.properties.milliseconds_left < (board.minimum_delay_between_moves + 500) * self.distance(current_position, base) and  props.diamonds > 0):
            self.goal_position = base
        elif not self.goal in board.game_objects or props.diamonds == 4 or (self.goal_position.x == current_position.x and self.goal_position.y == current_position.y) or current_position in self.portals:
            if len(self.objects_near_coords(base, board, "DiamondGameObject")) < 1:
                self.goal = self.square(board, current_position)
                self.goal_position = self.goal.position
            else:
                self.goal = self.nearest_diamond(board, current_position, 5 - props.diamonds)
                self.goal_position = self.goal.position
            if not (base.x == current_position.x and base.y == current_position.y) and props.diamonds > 0:
                self.triangle(board_bot)

        if self.warp_train(current_position):
            delta_x, delta_y = get_bot_direction(
                current_position.x,
                current_position.y,
                self.portals[0].x,
                self.portals[0].y,
            )
        else:
            delta_x, delta_y = self.lets_play(current_position, board)
            
        return delta_x, delta_y
    
    def update_portals(self, board: Board, current_position: Position) -> None:
        self.portals = [p.position for p in board.game_objects if p.type == "TeleportGameObject"]
        if self.distance(current_position, self.portals[0]) > self.distance(current_position, self.portals[1]):
            self.portals[0], self.portals[1] = self.portals[1], self.portals[0]

    def lets_play(self,current_position: Position, board: Board) -> List[int]:
        adjacent = [obj for obj in board.game_objects if self.distance(current_position, obj.position) == 1 and not (obj.type=="DiamondGameObject" or obj.type=="DiamondButtonGameObject" or obj.type=="BaseGameObject")]

        for i in adjacent:
            if i.properties.can_tackle and self.wrath:
                self.wrath = False
                return get_bot_direction(
                    current_position.x, 
                    current_position.y, 
                    i.position.x, 
                    i.position.y,
                )
        self.wrath = True
        return get_bot_direction(
            current_position.x,
            current_position.y,
            self.goal_position.x,
            self.goal_position.y,
        )

    def warp_train(self, current_position: Position) -> bool:
        return self.distance(current_position, self.goal_position) > self.distance(current_position, self.portals[0]) + self.distance(self.goal_position, self.portals[1]) and not current_position in self.portals
    
    def objects_near_coords(self, coords: Position, board: Board, object_type: str) -> List[GameObject]:
        return [d for d in board.game_objects if d.type == object_type and abs(d.position.x - coords.x) + abs(d.position.y - coords.y) < 7]

    def distance(self, object: Position, target: Position) -> int:
        return abs(target.x - object.x) + abs(target.y - object.y)
    
    def nearest_diamond(self, board: Board, current_position: Position, point_cap: int):
        distance = 10000
        temp = None
        tpoints = 0

        for d in board.diamonds:
            if d.properties.points <= point_cap:
                compared_distance = min(self.distance(d.position, current_position), self.distance(self.portals[0], current_position) + self.distance(self.portals[1], d.position))

                if compared_distance < distance or (compared_distance <= distance and d.properties.points > tpoints) :
                    distance = compared_distance
                    tpoints = d.properties.points
                    temp = d

        return temp
    
    def triangle(self, board_bot: GameObject) -> None:
        current_position = board_bot.position
        base = board_bot.properties.base
        
        min_distance = min(self.distance(self.goal_position, current_position), self.distance(self.portals[0], current_position) + self.distance(self.portals[1], self.goal_position))
        if min_distance * 2 > self.distance(self.goal_position, base) + self.distance(base, current_position):
            self.goal = base
            self.goal_position = base

    def square(self, board: Board, current_position: Position) -> Optional[GameObject]:
        for p in board.game_objects:
            if p.type == "DiamondButtonGameObject":
                button = p
                break
        for d in board.diamonds:
            if in_between(d.position, button.position, current_position):
                return d
        return button
    


def in_between(checked: Position, onep: Position, twop: Position) -> bool:
    return checked.x >= min(onep.x, twop.x) and checked.x <= max(onep.x, twop.x) and checked.y >= min(onep.y, twop.y) and checked.y <= max(onep.y, twop.y)

def get_bot_direction(current_x: int, current_y: int, dest_x: int, dest_y: int) -> List[int]:
    # Modifikasi get_direction dari file util.py
    delta_x = dest_x - current_x
    delta_y = dest_y - current_y
    if abs(delta_x) > abs(delta_y):
        delta_x = max(-1, min(delta_x, 1))
        delta_y = 0
    else:
        delta_y = max(-1, min(delta_y, 1))
        delta_x = 0
    return (delta_x, delta_y)