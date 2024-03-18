from typing import Optional
import math
import random
from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from ..util import get_direction, position_equals


class TheYudsLogic(BaseLogic):
    # Fungsi Konstruktor
    def __init__(self):
        self.directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        self.goal_position: Optional[Position] = None
        self.current_direction = 0
        self.is_portal_entry = False
    
    # Fungsi untuk menghitung jarak dua titik
    def displacement(self, current_position: Position, goal_position: Position):
        return math.sqrt((current_position.x - goal_position.x) ** 2 + (current_position.y - goal_position.y) ** 2)
    
    # Fungsi untuk menentukan apakah sebuah titik mengandung teleporter atau tidak
    def is_teleporter_position (self, current_position : Position, board: Board):
        list_portal = [x for x in board.game_objects if x.type == "TeleportGameObject"]
        for portal in list_portal:
            if (position_equals(current_position, portal.position)):
                return True
        return False
    
    # Fungsi untuk menentukan apakah sebuah titik mengandung diamond atau tidak
    def is_diamond_position (self, current_position : Position, board: Board):
        list_diamond = [x for x in board.game_objects if x.type == "DiamondGameObject"]
        for diamond in list_diamond:
            if (position_equals(current_position, diamond.position)):
                return True
        return False
    
    # Fungsi untuk menentukan arah yang dilalui oleh robot
    def possible_direction(self, current_position: Position, board: Board):
        direction_available = []
        
        if current_position.x > 0:
            direction_available.append((-1, 0))
        if current_position.x < board.width - 1:
            direction_available.append((1, 0))

        if current_position.y > 0:
            direction_available.append((0, -1))
        if current_position.y < board.height - 1:
            direction_available.append((0, 1))
        
        return direction_available
    
    # Fungsi untuk memanfaatkan portal
    def portal_utility_displacement(self, target:str, current_position: Position, portal_one_position: Position, portal_two_position: Position, board: Board, board_bot: GameObject):
        displacement_bot_to_portal_one = self.displacement(current_position, portal_one_position)
        displacement_bot_to_portal_two = self.displacement(current_position, portal_two_position)

        if displacement_bot_to_portal_one <= displacement_bot_to_portal_two:
            initial_to_portal_displacement = displacement_bot_to_portal_one
            portal_to_finish_displacement = portal_two_position
            initial_portal = portal_one_position
        else:
            initial_to_portal_displacement = displacement_bot_to_portal_two
            portal_to_finish_displacement = portal_one_position
            initial_portal = portal_two_position

        if target == "DiamondGameObject":
            displacement_to_diamond = []
            for diamond in board.diamonds:
                displacement_to_diamond.append((diamond.position, self.displacement(portal_to_finish_displacement, diamond.position)))
            shortest_displacement = min(displacement_to_diamond, key=lambda x: x[1])
            shortest_displacement_to_diamond = shortest_displacement[1]

            total_displacement = shortest_displacement_to_diamond + initial_to_portal_displacement
        elif target == "Base":
            base_position = board_bot.properties.base
            displacement_to_base = self.displacement(portal_to_finish_displacement, base_position)
            total_displacement = displacement_to_base + initial_to_portal_displacement
        
        
        return initial_portal, total_displacement

    # Fungsi untuk mencari posisi portal yang terdapat pada papan
    def find_portal_position(self, board: Board):
        list_portal = [x for x in board.game_objects if x.type == "TeleportGameObject"]
        return list_portal[0].position, list_portal[1].position
    

    # Fungsi untuk menentukan langkah selanjutnya yang akan dilalui robot
    def next_move(self, board_bot: GameObject, board: Board):

        # Inisialisasi
        props = board_bot.properties
        current_position = board_bot.position
        first_portal_position, second_portal_position = self.find_portal_position(board)
        base = board_bot.properties.base
        time_rem = props.milliseconds_left
        direction_available  = self.possible_direction(current_position, board)
        enemy_bot = [x for x in board.bots if not position_equals(current_position, x.position)]

        # Collision strategy
        for enemy in enemy_bot:
            if (enemy.properties.diamonds > board_bot.properties.diamonds and board_bot.properties.diamonds < 3 and (board_bot.properties.milliseconds_left%1000 < enemy.properties.milliseconds_left%1000)):
                if (abs(current_position.x - enemy.position.x) == 1 and current_position.y == enemy.position.y):
                    return [enemy.position.x - current_position.x, 0]
                elif (abs(current_position.y  - enemy.position.y) == 1 and current_position.x == enemy.position.x):
                    return [0, enemy.position.y - current_position.y]
                
        if props.diamonds == 5:
            initial_portal_position, effective_portal_base_displacement = self.portal_utility_displacement("Base", current_position,first_portal_position, second_portal_position, board, board_bot)
            if (self.displacement(current_position,base) > effective_portal_base_displacement):
                self.goal_position = initial_portal_position
            else:
                self.goal_position = base
            # Kasus ketika robot baru masuk ke dalam teleporter dan inventory == 5
            if (self.is_teleporter_position(current_position, board)):
                
                for direction in direction_available:
                    expected_position = Position(current_position.y+direction[1], current_position.x+direction[0])
                    if (not self.is_teleporter_position(expected_position, board)):        
                        self.goal_position = base

        else:
            listRatio = []
            for diamond in board.diamonds:
                if props.diamonds == 4:
                    if diamond.properties.points != 2:
                        listRatio.append((diamond.position, diamond.properties.points/self.displacement(board_bot.position,diamond.position), self.displacement(board_bot.position,diamond.position))) 
                else:
                    listRatio.append((diamond.position, diamond.properties.points/self.displacement(board_bot.position,diamond.position), self.displacement(board_bot.position,diamond.position)))
            try:
                maxDiamond = max(listRatio, key = lambda x: x[1])
                initial_portal_position, effective_portal_diamond_displacement = self.portal_utility_displacement("DiamondGameObject",current_position, first_portal_position, second_portal_position, board, board_bot)

                if (maxDiamond[2] > effective_portal_diamond_displacement):
                    self.goal_position = initial_portal_position
                else:
                    self.goal_position = maxDiamond[0]
                
                # Kasus ketika robot baru masuk ke dalam teleporter dan inventory < 5 dan target robot adalah diamond
                if (self.is_teleporter_position(current_position, board)):
                    for direction in direction_available:
                        expected_position = Position(current_position.y+direction[1], current_position.x+direction[0])
                        if (not self.is_teleporter_position(expected_position, board)):
                            if (self.is_diamond_position(expected_position, board)):
                                return direction
                            else:
                                maxDiamond = max(listRatio, key = lambda x: x[1])
                                self.goal_position = maxDiamond[0]
            except:
                initial_portal_position, effective_portal_base_displacement = self.portal_utility_displacement("Base", current_position,first_portal_position, second_portal_position, board, board_bot)
                if (self.displacement(current_position,base) > effective_portal_base_displacement):
                    self.goal_position = initial_portal_position
                else:
                    self.goal_position = base
            
                # Kasus ketika robot baru masuk ke dalam teleporter dan inventory < 5 dan target robot adalah base 
                if (self.is_teleporter_position(current_position, board)):
                    
                    for direction in direction_available:
                        expected_position = Position(current_position.y+direction[1], current_position.x+direction[0])
                        if (not self.is_teleporter_position(expected_position, board)):        
                            self.goal_position = base

            # Kasus ketika waktu yang tersisa dalam permainan dibawah 10 detik
            if time_rem <= 10000:
                if(props.diamonds > 1):
                    initial_portal_position, effective_portal_base_displacement = self.portal_utility_displacement("Base", current_position,first_portal_position, second_portal_position, board, board_bot)
                    if (self.displacement(current_position,base) > effective_portal_base_displacement):
                        self.goal_position = initial_portal_position
                    else:
                        self.goal_position = base

        # Pengembalian nilai fungsi
        delta_x, delta_y = get_direction(
            current_position.x,
            current_position.y,
            self.goal_position.x,
            self.goal_position.y,
        )

        if (delta_x == 0 and delta_y == 0):
            delta_x, delta_y = direction_available[random.randrange(0,len(direction_available))]
        return delta_x, delta_y