from typing import Optional, List, Tuple
from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position, Properties
from ..util import *

## ********** Helper Function ********** ##
def get_direction_alt(current_x, current_y, dest_x, dest_y):
    delta_x = clamp(dest_x - current_x, -1, 1)
    delta_y = clamp(dest_y - current_y, -1, 1)
    if delta_y != 0:
        delta_x = 0
    return delta_x, delta_y

def count_steps(a: Position, b: Position):
    return abs(a.x - b.x) + abs(a.y - b.y)

def coordinate_equals(x1: int, y1: int, x2: int, y2: int):
    return x1 == x2 and y1 == y2

def same_direction(pivot: Position, a: Position, b: Position):
    if a.x >= pivot.x and a.y >= pivot.y:
        return b.x >= pivot.x and b.y >= pivot.y
    elif a.x >= pivot.x and a.y <= pivot.y:
        return b.x >= pivot.x and b.y <= pivot.y
    elif a.x <= pivot.x and a.y >= pivot.y:
        return b.x <= pivot.x and b.y >= pivot.y
    elif a.x <= pivot.x and a.y <= pivot.y:
        return b.x <= pivot.x and b.y <= pivot.y

## ********** Classes ********** ##
class Portals:
    closest_portal: GameObject
    farthest_portal: GameObject

    def __init__(self, portal_list: List[GameObject], current_position: Position):
        if count_steps(current_position, portal_list[0].position) < count_steps(current_position, portal_list[1].position):
            self.closest_portal = portal_list[0]
            self.farthest_portal = portal_list[1]
        else:
            self.closest_portal = portal_list[1]
            self.farthest_portal = portal_list[0]

    def count_steps_by_portal(self, current_position: Position, target_position: Position) -> int:
        return count_steps(current_position, self.closest_portal.position) + count_steps(self.farthest_portal.position, target_position)

    def is_closer_by_portal(self, current_position: Position, target_position: Position) -> bool:
        return self.count_steps_by_portal(current_position, target_position) < count_steps(current_position, target_position)
    
class Player:
    current_position: Position
    target_position: Optional[Position]
    base_position: Position
    next_move: Tuple[int, int]
    current_target: Optional[GameObject]
    inventory_size: int
    diamonds_being_held: int
    is_inside_portal: bool
    is_avoiding_portal: bool
    milliseconds_left: int
    
    def __init__(self, current_position: Position, props: Properties):
        self.current_position = current_position
        self.base_position = props.base
        self.inventory_size = props.inventory_size
        self.diamonds_being_held = props.diamonds
        self.milliseconds_left = props.milliseconds_left
        self.is_inside_portal = False
        self.is_avoiding_portal = False
        self.current_target = None
        self.next_move = None
    
    def is_inventory_full(self) -> bool:
        return self.diamonds_being_held == self.inventory_size
    
    def set_target(self, object: GameObject):
        self.current_target = object
        self.target_position = object.position

    def set_target_position(self, target_position: Position):
        self.target_position = target_position
    
    def is_invalid_move(self, delta_x: int, delta_y: int, board: Board) -> bool:
        return (self.current_position.x + delta_x < 0 or self.current_position.x + delta_x == board.width or
                self.current_position.y + delta_y < 0 or self.current_position.y + delta_y == board.height)
        
    def avoid_obstacles(self, portals: Portals, is_avoiding_portal: bool, board: Board):
        delta_x, delta_y = get_direction(self.current_position.x, self.current_position.y, self.target_position.x, self.target_position.y)
        next_x, next_y = self.current_position.x + delta_x, self.current_position.y + delta_y
        
        if (is_avoiding_portal or ((not self.current_target or self.current_target.type != "TeleportGameObject") and 
           (coordinate_equals(next_x, next_y, portals.closest_portal.position.x, portals.closest_portal.position.y) or
            coordinate_equals(next_x, next_y, portals.farthest_portal.position.x, portals.farthest_portal.position.y)))):
            
            delta_x_alt, delta_y_alt = get_direction_alt(self.current_position.x, self.current_position.y, self.target_position.x, self.target_position.y)
            if delta_x == delta_x_alt and delta_y == delta_y_alt:
                delta_x, delta_y = delta_y, delta_x
                if self.is_invalid_move(delta_x, delta_y, board):
                    delta_x, delta_y = -delta_x, -delta_y
                if delta_y == 0:
                    self.is_avoiding_portal = True
            else:
                delta_x, delta_y = delta_x_alt, delta_y_alt                    
        
        self.next_move = delta_x, delta_y
        

class Diamonds:
    diamonds_list: List[GameObject]
    chosen_diamond: GameObject
    chosen_diamond_distance: int
    chosen_target: GameObject
    red_button: GameObject
    
    def __init__(self, diamonds_list: List[GameObject], red_button: GameObject, diamonds_being_held: int):
        self.diamonds_list = [d for d in diamonds_list if d.properties.points == 1 or diamonds_being_held < 4]
        self.chosen_diamond = diamonds_list[0]
        self.chosen_diamond_distance = float('inf')
        self.red_button = red_button
        self.chosen_target = None
    
    def filter_diamond(self, current_position: Position, enemy_position: Position):
        if current_position.x != enemy_position.x and current_position.y != enemy_position.y:
            self.diamond_list = [d for d in self.diamonds_list if d and not same_direction(current_position, enemy_position, d.position)]
    
    def choose_diamond(self, player: Player, portals: Portals):
        max_step_diff = 2
        for diamond in self.diamonds_list:
            diamond_distance = count_steps(player.current_position, diamond.position)
            if player.diamonds_being_held == 4:
                diamond_to_base = count_steps(diamond.position, player.base_position)
                diamond_to_portal1 = count_steps(diamond.position, portals.closest_portal.position) + count_steps(portals.farthest_portal.position, player.base_position)
                diamond_to_portal2 = count_steps(diamond.position, portals.farthest_portal.position) + count_steps(portals.closest_portal.position, player.base_position)
                diamond_distance += min(diamond_to_base, diamond_to_portal1, diamond_to_portal2)
            
            point_diff = diamond.properties.points - self.chosen_diamond.properties.points
            if self.chosen_diamond_distance > diamond_distance - (point_diff * max_step_diff):
                self.chosen_diamond = diamond
                self.chosen_diamond_distance = diamond_distance
                self.chosen_target = diamond
        
        if not player.is_inside_portal and count_steps(player.current_position, portals.closest_portal.position) < self.chosen_diamond_distance:
            for diamond in self.diamonds_list:
                diamond_distance = portals.count_steps_by_portal(player.current_position, diamond.position)
                if player.diamonds_being_held == 4:
                    diamond_to_base = count_steps(diamond.position, player.base_position)
                    diamond_to_portal1 = count_steps(diamond.position, portals.closest_portal.position) + count_steps(portals.farthest_portal.position, player.base_position)
                    diamond_to_portal2 = count_steps(diamond.position, portals.farthest_portal.position) + count_steps(portals.closest_portal.position, player.base_position)
                    diamond_distance += min(diamond_to_base, diamond_to_portal1, diamond_to_portal2)
                
                point_diff = diamond.properties.points - self.chosen_diamond.properties.points
                if self.chosen_diamond_distance > diamond_distance - (point_diff * max_step_diff):
                    self.chosen_diamond = diamond
                    self.chosen_diamond_distance = diamond_distance
                    self.chosen_target = portals.closest_portal
    
    def check_red_button(self, player: Player, portals: Portals):
        if not player.is_inside_portal:
            red_button_distance = min(count_steps(player.current_position, self.red_button.position), portals.count_steps_by_portal(player.current_position, self.red_button.position))
        else:
            red_button_distance = count_steps(player.current_position, self.red_button.position)
        
        if player.diamonds_being_held == 4:
            red_button_to_base = count_steps(self.red_button.position, player.base_position)
            red_button_to_portal1 = count_steps(self.red_button.position, portals.closest_portal.position) + count_steps(portals.farthest_portal.position, player.base_position)
            red_button_to_portal2 = count_steps(self.red_button.position, portals.farthest_portal.position) + count_steps(portals.closest_portal.position, player.base_position)
            red_button_distance += min(red_button_to_base, red_button_to_portal1, red_button_to_portal2)

        max_step_diff = 4
        if red_button_distance + max_step_diff <= self.chosen_diamond_distance:
            if portals.is_closer_by_portal(player.current_position, self.red_button.position):
                self.chosen_target = portals.closest_portal
            else:
                self.chosen_target = self.red_button

class Enemies:
    enemies_list: List[GameObject]
    target_enemy: GameObject
    target_enemy_distance: int
    enemy_target_position: Position
    try_tackle: bool
    wait_move: bool
    
    def __init__(self, bots_list: List[GameObject], player_bot: GameObject):
        self.enemies_list = [bot for bot in bots_list if bot.id != player_bot.id]
        self.target_enemy_distance = float('inf')
        self.try_tackle = False
    
    def check_nearby_enemy(self, diamonds: Diamonds, player: Player, portals: Portals, has_tried_tackle: bool):
        for enemy in self.enemies_list:
            enemy_distance = count_steps(player.current_position, enemy.position)
            if enemy_distance < self.target_enemy_distance:
                self.target_enemy = enemy
                self.target_enemy_distance = enemy_distance
        
        if (self.target_enemy_distance == 2 and not has_tried_tackle and
           (player.current_position.x != self.target_enemy.position.x and player.current_position.y != self.target_enemy.position.y)):
            player.next_move = get_direction_alt(player.current_position.x, player.current_position.y,
                                                 self.target_enemy.position.x, self.target_enemy.position.y)
            self.try_tackle = True
        elif self.target_enemy_distance == 3:
            self.avoid_enemy(player, diamonds, portals)
    
    def avoid_enemy(self, player: Player, diamonds: Diamonds, portals: Portals):
        diamonds.filter_diamond(player.current_position, self.target_enemy.position)
        diamonds.choose_diamond(player, portals)
        if not same_direction(player.current_position, self.target_enemy.position, diamonds.red_button.position):
            diamonds.check_red_button(player, portals)
        

class GameState:
    board: Board
    player_bot: GameObject
    
    def __init__(self, board_bot: GameObject, board: Board):
        self.board = board
        self.player_bot = board_bot
    
    def initialize(self):
        list_of_diamonds = []
        list_of_portals = []
        list_of_bots = []
        red_button = None
        
        for object in self.board.game_objects:
            if object.type == "DiamondGameObject":
                list_of_diamonds.append(object)
            elif object.type == "DiamondButtonGameObject":
                red_button = object 
            elif object.type == "TeleportGameObject":
                list_of_portals.append(object)
            elif object.type == "BotGameObject":
                list_of_bots.append(object)
        
        return (Player(self.player_bot.position, self.player_bot.properties),
                Diamonds(list_of_diamonds, red_button, self.player_bot.properties.diamonds),
                Portals(list_of_portals, self.player_bot.position),
                Enemies(list_of_bots, self.player_bot))
    
    def no_time_left(self, current_position: Position, base_position: Position) -> bool:
        return (not position_equals(current_position, base_position) and
                self.player_bot.properties.milliseconds_left / count_steps(current_position, base_position) <= 1300)


## ********** Main Logic ********** ##
class MyBot(BaseLogic):
    def __init__(self):
        self.back_to_base: bool = False
        self.is_avoiding_portal: bool = False
        self.tackle: bool = False
    
    def next_move(self, board_bot: GameObject, board: Board) -> Tuple[int, int]:
        game_state = GameState(board_bot, board)
        player, diamonds, portals, enemies = game_state.initialize()
        
        if position_equals(player.current_position, player.base_position):
            self.back_to_base = False
        elif position_equals(player.current_position, portals.closest_portal.position):
            player.is_inside_portal = True
        
        if self.back_to_base or player.is_inventory_full() or game_state.no_time_left(player.current_position, player.base_position):
            player.set_target_position(player.base_position)
            self.back_to_base = True

            if (not player.is_inside_portal and
                (not game_state.no_time_left(player.current_position, player.base_position) or count_steps(player.current_position, portals.closest_portal.position) == 1)
                and portals.is_closer_by_portal(player.current_position, player.base_position)):
                player.set_target(portals.closest_portal)

        else:            
            diamonds.choose_diamond(player, portals)
            if diamonds.chosen_target:
                diamonds.check_red_button(player, portals)
                player.set_target(diamonds.chosen_target)
            else:
                player.set_target_position(player.base_position)
                self.back_to_base = True
        
        if not game_state.no_time_left(player.current_position, player.base_position):
            enemies.check_nearby_enemy(diamonds, player, portals, self.tackle)
            self.tackle = enemies.try_tackle
        
        if not enemies.try_tackle:
            player.avoid_obstacles(portals, self.is_avoiding_portal, board)
            self.is_avoiding_portal = player.is_avoiding_portal

        return player.next_move

