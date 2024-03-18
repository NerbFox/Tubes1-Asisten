import random
from typing import Optional, List
from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from ..util import get_direction


class SarikatJava(BaseLogic):
    def __init__(self):
        self.directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        self.goal_position: Optional[Position] = None
        self.current_direction = 0

    def needed_steps(self, starting_pos: Position, diamond_pos: Position) -> int:
        """Calculate the number of steps needed to reach the diamond position."""
        return abs(starting_pos.x - diamond_pos.x) + abs(starting_pos.y - diamond_pos.y)

    def get_density(self, diamond: GameObject, bot_pos: Position) -> float:
        """Calculate the density of a diamond based on its points and distance from the bot."""
        return diamond.properties.points / self.needed_steps(bot_pos, diamond.position)

    def generate_best_density(self, diamonds: List[GameObject], board_bot: GameObject, start_teleporter_position: Position, end_teleporter_position: Position, distance_to_targetTeleporter : int) -> None:
        """Find the diamond with the highest density and set it as the goal position."""
        curr_density_max = 0
        curr_density_max_pos = diamonds[0].position
        bot_position = board_bot.position

        ##calculate density of each diamond and compare it with the current max density
        for diamond in diamonds:
            density = self.get_density(diamond, bot_position)
            #Calculate density based on the distance to the teleporter
            teleportdensity = diamond.properties.points / (distance_to_targetTeleporter + self.needed_steps(diamond.position, end_teleporter_position) )
            if density > curr_density_max or teleportdensity > curr_density_max :
                if (teleportdensity > density):
                    curr_density_max = teleportdensity
                    curr_density_max_pos = start_teleporter_position
                else:
                    curr_density_max = density
                    curr_density_max_pos = diamond.position
        ##Langsung set as goal
        self.goal_position = curr_density_max_pos

    ##Mencari blue diamond terdekat. Digunakan ketika kasus diamond saat ini 4, namun best densitynya adalah red diamond
    def generate_shortest_blue(self, diamonds: List[GameObject], board_bot: GameObject, diamond_button : GameObject) -> None:
        diamonds.sort(key=lambda x: self.needed_steps(board_bot.position, x.position))
        for diamond in diamonds:
            if diamond.properties.points == 1:
                self.goal_position = diamond.position
                break
            else:
                self.goal_position = diamonds[0].position
    
    def next_move(self, board_bot: GameObject, board: Board) -> tuple:
        ##initialize props
        props = board_bot.properties
        base = board_bot.properties.base
        list_diamonds = board.diamonds
        current_position = board_bot.position
        
        ##initialize teleporters
        list_teleporters = [d for d in board.game_objects if d.type == "TeleportGameObject"]
        marco = list_teleporters[0]
        polo = list_teleporters[1]
        targetTeleporter = marco
        exitTeleporter = polo
        dm = self.needed_steps(marco.position,current_position)
        dp = self.needed_steps(polo.position,current_position)
        
        diamond_button = [d for d in board.game_objects if d.type == "DiamondButtonGameObject"]
        print(diamond_button[0])
        ##Cari teleporter terdekat
        if dp < dm:
            targetTeleporter = polo
            exitTeleporter=marco

        ##Cari jarak ke teleporter terdekat
        distance_to_targetTeleporter = self.needed_steps(targetTeleporter.position,current_position)
        ##Kalau Sudah 4, pastikan cari biru terdekat

        if props.diamonds == 4 :
            self.generate_shortest_blue(list_diamonds, board_bot, diamond_button[0].position)
        # If there are 5 diamonds in the inventory, move towards the base
        elif props.diamonds == 5 or (props.milliseconds_left < (1000* self.needed_steps(base, board_bot.position)+2000) and props.milliseconds_left < 8000): 
            teleporter_base_distance = self.needed_steps(exitTeleporter.position,base)
            td = teleporter_base_distance + distance_to_targetTeleporter
            distanceBotBase = self.needed_steps(base,current_position)
            if(td < distanceBotBase) and distance_to_targetTeleporter != 0:
                delta_x, delta_y = get_direction(
                    current_position.x,
                    current_position.y,
                    targetTeleporter.position.x,
                    targetTeleporter.position.y,
                )  
                return delta_x,delta_y
            else :
                self.goal_position = base
        # If there is only some diamonds left and the distance of our target is less than the distance to the diamond button, move towards the diamond trigger button
        elif len(list_diamonds) < 3 and self.goal_position!=None and self.needed_steps(board_bot.position, self.goal_position) > self.needed_steps(diamond_button[0].position, board_bot.position):
            self.goal_position = diamond_button[0].position
        # If the goal position is not among the diamonds or it's not set yet, generate the best density
        # If targetTeleporter is not among the teleporters or it's not set yet, generate the best density
        elif all(self.goal_position != diamond.position for diamond in list_diamonds) or all (targetTeleporter.position != teleporter.position for teleporter in list_teleporters) or self.goal_position is None:
            self.generate_best_density(list_diamonds, board_bot, targetTeleporter.position, exitTeleporter.position, distance_to_targetTeleporter)
        current_position = board_bot.position
        delta_x, delta_y = get_direction(current_position.x, current_position.y, self.goal_position.x, self.goal_position.y)
        

        return delta_x, delta_y