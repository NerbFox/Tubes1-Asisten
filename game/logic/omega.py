from typing import Optional

from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from ..util import get_direction

class omega(BaseLogic):
    def __init__(self): # Inisialisasi
        self.goal_position: Optional[Position] = None
        self.portal: tuple[Position, Position]
        self.red_diamonds: list[Position]
        self.blue_diamonds: list[Position]
        self.distance_to_Base: int
        self.distance_to_redButton: int
        self.redButton_position: list[Position]
    

    def getDistance(self, A: Position, B: Position) : # Menghitung jarak antara dua posisi
        return (abs(B.x - A.x) + abs(B.y - A.y))
    

    def isInDomain(self, X : Position, Y: Position, A: Position):  # Mengecek apakah A berada di dalam domain X dan Y
        return (X.x >= A.x >= Y.x or X.x <= A.x <= Y.x) and (X.y >= A.y >= Y.y or X.y <= A.y <= Y.y) and (X.x != A.x and X.y != A.y) and (Y.x != A.x and Y.y != A.y)


    def getPortal(self, board_bot: GameObject, board : Board) : # Mendapatkan posisi portal awal yang terdekat dari bot dan posisi portal kedua yang terjauh dari bot
        portal_position = [d.position for d in board.game_objects if d.type == 'TeleportGameObject']
        bot_position = board_bot.position
        if (self.getDistance(portal_position[0], bot_position) < self.getDistance(portal_position[1], bot_position)):
            nearest_portal = portal_position[0]
            second_portal = portal_position[1]
        else :
            nearest_portal = portal_position[1]
            second_portal = portal_position[0]
        return nearest_portal, second_portal
    

    def logicPortal(self, diamonds_position : list[Position], board_bot: GameObject) : # Menentukan jarak dari bot ke diamond terdekat melalui/tidak melalui portal
        distance_from_bot = self.getDistance(diamonds_position[-1], board_bot.position)
        distance_with_portal = self.getDistance(self.portal[0], board_bot.position) + self.getDistance(self.portal[1], diamonds_position[-1])
        if distance_with_portal < distance_from_bot :
            result = True
            temp_final_distance = distance_with_portal
        else :
            result = False
            temp_final_distance = distance_from_bot
        return temp_final_distance, result
    

    def logicDiamond(self, diamonds_position : list[Position], board_bot: GameObject) : # Mencari jarak bot ke diamond
        distance_from_bot = self.getDistance(diamonds_position[-1], board_bot.position)
        return distance_from_bot


    # Mencari jarak terdekat dari bot ke diamond
    def greedyNearestDiamond(self, blue_diamonds_position : list[Position], red_diamonds_position : list[Position], board_bot: GameObject, board: Board) : 
        goal_blue : Optional[Position] = None
        goal_red : Optional[Position] = None
        leng_blue = len(blue_diamonds_position)
        leng_red = len(red_diamonds_position)
        
        if (leng_blue != 0) :
            final_distance_blue = self.getDistance(blue_diamonds_position[-1], board_bot.position)
            goal_blue = blue_diamonds_position[-1]
        
        if (leng_red != 0) :
            final_distance_red = self.getDistance(red_diamonds_position[-1], board_bot.position)
            goal_red = red_diamonds_position[-1]
        
        while leng_blue != 0 or leng_red != 0:
            if (leng_blue != 0) :
                temp_blue = self.logicDiamond(blue_diamonds_position, board_bot)
                if temp_blue < final_distance_blue :
                    final_distance_blue = temp_blue
                    goal_blue = blue_diamonds_position[-1]
                blue_diamonds_position.pop()
                leng_blue -= 1
            
            if (leng_red != 0) :
                temp_red = self.logicDiamond(red_diamonds_position, board_bot)
                if temp_red < final_distance_red :
                    final_distance_red = temp_red 
                    goal_red = red_diamonds_position[-1]
                red_diamonds_position.pop()
                leng_red -= 1
        
        if (goal_blue != None and goal_red != None) :
            if final_distance_red <= final_distance_blue and board_bot.properties.diamonds != 4:
                final_distance_diamond = final_distance_red
                self.goal_position = goal_red
            else:
                final_distance_diamond = final_distance_blue
                self.goal_position = goal_blue
        
        elif goal_blue == None :
            final_distance_diamond = final_distance_red
            self.goal_position = goal_red
        
        else :
            final_distance_diamond = final_distance_blue
            self.goal_position = goal_blue
        
        if self.distance_to_base <= final_distance_diamond and board_bot.position != board_bot.properties.base and board_bot.properties.diamonds >= 3:
            if (board_bot.position in self.portal) :
                self.goal_position = board_bot.properties.base
            else :
                self.logicBasePortal(board_bot, board)
        
        elif self.distance_to_redButton <= final_distance_diamond:
            if (board_bot.position in self.portal) :
                self.goal_position = self.redButton_position[0]
            else :
                self.logicRedButtonPortal(board_bot, board)
        

    # Memilih jarak terdekat dari bot ke base melalui/tidak melalui portal
    def logicBasePortal (self, board_bot : GameObject, board : Board) :
        bot_position = board_bot.position
        base = board_bot.properties.base
        if (self.getDistance(bot_position, self.portal[0]) + self.getDistance(self.portal[1], base) <= self.getDistance(bot_position, base)):
            self.goal_position = self.portal[0]
        else :
            self.goal_position = base
        

    # Memilih jarak terdekat dari bot ke redButton melalui portal/tidak    
    def logicRedButtonPortal (self, board_bot : GameObject, board : Board) :
        bot_position = board_bot.position
        redButton = self.redButton_position[0]
        if (self.getDistance(bot_position, self.portal[0]) + self.getDistance(self.portal[1], redButton) <= self.getDistance(bot_position, redButton)):
            self.goal_position = self.portal[0]
        else :
            self.goal_position = redButton


    # Mencari jarak terdekat dari bot ke diamond melalui portal/tidak dengan menggunakan algoritma greedy
    def greedyDiamondPortal(self, blue_diamonds_position : list[Position], red_diamonds_position : list[Position], board_bot: GameObject, board: Board) :
        goal_position_blue : Optional[Position] = None
        goal_position_red : Optional[Position] = None
        leng_blue = len(blue_diamonds_position)
        leng_red = len(red_diamonds_position)
        
        if (leng_blue != 0) :
            goal_position_blue = blue_diamonds_position[-1]
            final_distance_blue = self.getDistance(blue_diamonds_position[-1], board_bot.position)
        
        if (leng_red != 0) :
            goal_position_red = red_diamonds_position[-1]
            final_distance_red = self.getDistance(red_diamonds_position[-1], board_bot.position)
       
        while leng_blue != 0 or leng_red != 0:
            if (leng_blue != 0) :
                temp_position_blue = self.logicPortal(blue_diamonds_position, board_bot)
                temp_final_distance_blue = temp_position_blue[0]
                if temp_final_distance_blue < final_distance_blue :
                    final_distance_blue = temp_final_distance_blue
                    if temp_position_blue[1]:
                        goal_position_blue = self.portal[0]
                    else :
                        goal_position_blue = blue_diamonds_position[-1]
                blue_diamonds_position.pop()
                leng_blue -= 1
            
            if (leng_red != 0) :
                temp_position_red = self.logicPortal(red_diamonds_position, board_bot)
                temp_final_distance_red = temp_position_red[0]
                if temp_final_distance_red < final_distance_red :
                    final_distance_red = temp_final_distance_red
                    if temp_position_red[1]:
                        goal_position_red = self.portal[0]
                    else :
                        goal_position_red = red_diamonds_position[-1]
                red_diamonds_position.pop()
                leng_red -= 1

        if (goal_position_blue != None and goal_position_red != None) :
            if final_distance_red <= final_distance_blue and board_bot.properties.diamonds != 4:
                final_distance_diamond = final_distance_red
                self.goal_position = goal_position_red
            else:
                final_distance_diamond = final_distance_blue
                self.goal_position = goal_position_blue
        
        elif goal_position_blue == None :
            final_distance_diamond = final_distance_red
            self.goal_position = goal_position_red
        
        else :
            final_distance_diamond = final_distance_blue
            self.goal_position = goal_position_blue
        
        if self.distance_to_base <= final_distance_diamond and board_bot.position != board_bot.properties.base and board_bot.properties.diamonds >= 3:
            if (board_bot.position in self.portal) :
                self.goal_position = board_bot.properties.base
            else :
                self.logicBasePortal(board_bot, board)
        
        elif self.distance_to_redButton <= final_distance_diamond:
            if (board_bot.position in self.portal) :
                self.goal_position = self.redButton_position[0]
            else :
                self.logicRedButtonPortal(board_bot, board)
    

    # Mencari jumlah diamond di area tertentu
    def diamondInArea(self, position : Position, radius : int):
        blue = [b for b in self.blue_diamonds if ((position.x - radius) <= b.x <= (position.x + radius)) and ((position.y - radius) <= b.y <= (position.y + radius)) ]
        red = [r for r in self.red_diamonds if (position.x - radius) <= r.x <= (position.x + radius) and (position.y - radius) <= r.y <= (position.y + radius) ]
        return len(blue) + len(red)


    # Menentukan langkah selanjutnya dari bot dengan mengimplementasikan fungsi-fungsi di atas
    def next_move(self, board_bot: GameObject, board: Board):
        props = board_bot.properties
        base = board_bot.properties.base
        self.blue_diamonds = [diamond.position for diamond in board.game_objects if diamond.type == 'DiamondGameObject' if diamond.properties.points == 1]
        self.red_diamonds = [diamond.position for diamond in board.game_objects if diamond.type == 'DiamondGameObject' if diamond.properties.points == 2]
        self.portal = self.getPortal(board_bot,board)
        
        self.distance_to_base = self.getDistance(board_bot.position, board_bot.properties.base)
        distance_to_base_portal = self.getDistance(board_bot.position, self.portal[0]) + self.getDistance(self.portal[1], base)
        if distance_to_base_portal <= self.distance_to_base:
            self.distance_to_base = distance_to_base_portal
            self.isBasePortal = True

        self.redButton_position = [x.position for x in board.game_objects if x.type == "DiamondButtonGameObject"]
        self.distance_to_redButton = self.getDistance(self.redButton_position[0], board_bot.position)
        distance_to_redButton_portal = self.getDistance(board_bot.position, self.portal[0]) + self.getDistance(self.portal[1], self.redButton_position[0])
        
        if distance_to_redButton_portal <= self.distance_to_redButton:
            self.distance_to_redButton = distance_to_redButton_portal
            self.isRedButtonPortal = True

        if props.diamonds == 5 or (board_bot.properties.milliseconds_left/1000 - 1 <= self.distance_to_base) or (props.diamonds == 4 and len(self.blue_diamonds) == 0):
            if (board_bot.position in self.portal) :
                self.goal_position = base
            else :
                self.logicBasePortal(board_bot, board)
        
        else:
            if (board_bot.position in self.portal) :
                self.greedyNearestDiamond(self.blue_diamonds, self.red_diamonds, board_bot, board)
            else :
                self.greedyDiamondPortal(self.blue_diamonds, self.red_diamonds, board_bot, board)

        current_position = board_bot.position

        delta_x, delta_y = get_direction(
            current_position.x,
            current_position.y,
            self.goal_position.x,
            self.goal_position.y,
        )
        return delta_x, delta_y