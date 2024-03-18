import random
from typing import Optional

from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from game.util import clamp
from typing import List

class AlucardGreedy(BaseLogic):
    def __init__(self):
        self.directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        self.goal_position: Optional[Position] = None
        self.current_direction = 0

    def getDistanceBetween(self,curr_pos: Position, target_pos: Position) -> int:
        """Calculate the Manhattan distance between two positions."""
        return abs(curr_pos.x - target_pos.x) + abs(curr_pos.y - target_pos.y)

    def getDistanceBetweenTransition(self,curr_pos: Position, transition: Position, target_pos: Position) -> int:
        """Calculate the combined Manhattan distance when transitioning through an intermediate position."""
        return abs(curr_pos.x - transition.x) + abs(curr_pos.y - transition.y) + abs(transition.x - target_pos.x) + abs(transition.y - target_pos.y)

    def getNearestObjectPosition(self,curr_pos: Position, target_pos: List[Position]) -> Position:
        """Find the position of the nearest object from a list."""
        nearest = None
        nearest_distance = float('inf')
        for obj in target_pos:
            distance = self.getDistanceBetween(curr_pos, obj)
            if distance < nearest_distance:
                nearest = obj
                nearest_distance = distance
        return nearest

    def getObjectsInArea(self,bot_position: Position, target_pos: List[Position], area: int) -> List[Position]:
        """Get a list of objects within a specified distance from a given position."""
        objects = []
        for obj in target_pos:
            if self.getDistanceBetween(bot_position, obj) <= area:
                objects.append(obj)
        return objects

    def isObjectInArea(self,bot_position: Position, target_pos: List[Position], area: int) -> bool:
        """Check if any object is within a specified distance from a given position."""
        for obj in target_pos:
            if self.getDistanceBetween(bot_position, obj) <= area:
                return True
        return False

    def isSameDirection(self,curr_po: Position, target1_po: Position, target2_po: Position) -> bool:
        """Check if two targets are in the same direction from the current position."""
        if(target1_po.x > curr_po.x and target2_po.x > curr_po.x and target1_po.y > curr_po.y and target2_po.y > curr_po.y):
            return True
        elif(target1_po.x < curr_po.x and target2_po.x < curr_po.x and target1_po.y > curr_po.y and target2_po.y > curr_po.y):
            return True
        elif(target1_po.x < curr_po.x and target2_po.x < curr_po.x and target1_po.y < curr_po.y and target2_po.y < curr_po.y):
            return True
        elif(target1_po.x > curr_po.x and target2_po.x > curr_po.x and target1_po.y < curr_po.y and target2_po.y < curr_po.y):
            return True
        return False

    def get_direction_v2(self,current_x, current_y, dest_x, dest_y):
        """Get the direction (delta_x, delta_y) between two positions, clamping the values."""
        delta_x = clamp(dest_x - current_x, -1, 1)
        delta_y = clamp(dest_y - current_y, -1, 1)
        
        if(delta_x == 0 or delta_y == 0):
                return(delta_x, delta_y)
        else:
                if(current_x%2==1):
                    return(delta_x, 0)
                else:
                    return(0, delta_y)

    # Calculate the total distance from the bot's position to the goal position using portals and base.
    def getDistanceWithPortalRelBase(self,curr_po:Position, near_portal:Position, far_portal:Position,target_po: Position, base_pos:Position) -> int:
        return self.getDistanceBetween(curr_po, near_portal) + self.getDistanceBetween(far_portal, target_po) + min(self.getDistanceBetween(target_po, base_pos), self.getDistanceBetween(target_po, far_portal) + self.getDistanceBetween(near_portal,base_pos))
                
       # Function to dodge a teleport when moving towards a goal position.
   
    def dodge_tele(self,curr_po: Position, near_tele: Position, far_tele: Position, goal_po: Position) -> Position:
        # Calculate the delta_x and delta_y from the current position to the goal position.
        delta_x = goal_po.x - curr_po.x
        delta_y = goal_po.y - curr_po.y

        # Conditions for handling movement when the current position is in the same line as the goal position.
        if curr_po.y == goal_po.y:
            if curr_po.y + 1 == far_tele.y or curr_po.y - 1 == far_tele.y:
                return Position(x=curr_po.x, y=curr_po.y + 1 if curr_po.y + 1 == far_tele.y else curr_po.y - 1)
            elif near_tele.y + 1 == far_tele.y or near_tele.y - 1 == far_tele.y:
                return Position(x=near_tele.x, y=near_tele.y)
            return Position(x=curr_po.x, y=curr_po.y + 1 if curr_po.y + 1 < 15 else curr_po.y - 1)

        elif curr_po.x == goal_po.x:
            if curr_po.x + 1 == far_tele.x or curr_po.x - 1 == far_tele.x:
                return Position(x=curr_po.x + 1 if curr_po.x + 1 == far_tele.x else curr_po.x - 1, y=curr_po.y)
            elif near_tele.x + 1 == far_tele.x or near_tele.x - 1 == far_tele.x:
                return Position(x=near_tele.x, y=near_tele.y)
            return Position(x=curr_po.x + 1 if curr_po.x + 1 < 15 else curr_po.x - 1, y=curr_po.y)

        # Conditions for handling movement when the current position is not in the same line as the goal position.
        elif curr_po.y == near_tele.y:
            return Position(x=curr_po.x, y=curr_po.y + 1 if delta_y > 0 else curr_po.y - 1)

        elif curr_po.x == near_tele.x:
            return Position(x=curr_po.x + 1 if delta_x > 0 else curr_po.x - 1, y=curr_po.y)

        else:
            # If none of the conditions are met, return the goal position without modification.
            return goal_po
            
            
    def get_nearest_diamond(self,bot_position:Position, diamond_position_list:List[Position]) -> Position:
        # Get the nearest diamond position to the bot.
        return self.getNearestObjectPosition(bot_position, diamond_position_list)

    def get_nearest_diamond_base(self,diamonds:List[GameObject], diamond_position_list: List[Position], bot_position:Position, base_position:Position) -> Position:
        min_distance = float('inf')
        nearest_diamond = None

        # Loop through all diamonds to find the nearest one considering the base.
        for diamond in diamond_position_list:
            if len(diamond_position_list) >= 3:
                diamond_list = [d for d in diamond_position_list if d != diamond]
                nearest_diamonds = self.getNearestObjectPosition(diamond, diamond_list)

                # Find the corresponding GameObjects for the current and nearest diamonds.
                for d in diamonds:
                    if d.position == nearest_diamonds:
                        nearest_obj = d
                    if d.position == diamond:
                        curr_obj = d

                # Calculate the total distance considering points of the diamonds and their distance from the bot.
                distance = (
                    self.getDistanceBetween(bot_position, diamond) +
                    self.getDistanceBetween(diamond, base_position) +
                    self.getDistanceBetween(diamond, nearest_diamonds) - nearest_obj.properties.points - curr_obj.properties.points
                )
            else:
                # If there are less than 3 diamonds, calculate distance without considering points.
                distance = (
                    self.getDistanceBetween(bot_position, diamond) +
                    self.getDistanceBetween(diamond, base_position)
                )

            if distance < min_distance:
                min_distance = distance
                nearest_diamond = diamond

        return nearest_diamond

    def diamond_process(self,base_position:Position,diamonds:List[GameObject], diamond_position_list: List[Position], bot:GameObject, red_button_position:Position):
        bot_position = bot.position
        nearest_diamond_with_base = self.get_nearest_diamond_base(diamonds=diamonds,
                                                                  diamond_position_list=diamond_position_list,
                                                                  bot_position=bot_position, 
                                                                  base_position=base_position)

        # Determine the goal position based on distances and conditions.
        if (self.getDistanceBetween(bot_position, nearest_diamond_with_base) > self.getDistanceBetween(bot_position, red_button_position) and 
            self.getDistanceBetween(bot_position, nearest_diamond_with_base) > 2
        ):
            self.goal_position = red_button_position
        elif (
            self.getDistanceBetween(bot_position, nearest_diamond_with_base) > self.getDistanceBetween(bot_position, base_position) and
            self.isSameDirection(bot_position, nearest_diamond_with_base, base_position) and
            bot.properties.diamonds > 2
        ):
            self.goal_position = base_position
        else:
            nearest_diamond = self.get_nearest_diamond(bot_position, diamond_position_list)

            # If the bot is close to the nearest diamond, set the goal position to that diamond; otherwise, set it to the nearest diamond with base.
            if self.getDistanceBetween(bot_position, nearest_diamond) <= 2:
                self.goal_position = nearest_diamond
            else:
                self.goal_position = nearest_diamond_with_base
    

    def bot_process(self, bot: GameObject, enemies_position: List[Position], diamond_position_list: List[Position], diamonds: List[GameObject], base_position: Position) -> Position:
        curr_pos = bot.position
        dm_candidate = diamond_position_list.copy() 
        
        for enemy in enemies_position:
            # Get direction of enemy from bot
            delta_x_en, delta_y_en = self.get_direction_v2(curr_pos.x, curr_pos.y, enemy.x, enemy.y)
            
            while len(dm_candidate) > 0:
                # Get nearest diamond from bot and base
                nearest_dm = self.get_nearest_diamond_base(diamonds=diamonds, diamond_position_list=dm_candidate, bot_position=curr_pos, base_position=base_position)
                # Get direction of nearest diamond from bot
                delta_x_dm, delta_y_dm = self.get_direction_v2(curr_pos.x, curr_pos.y, nearest_dm.x, nearest_dm.y)
                
                # Back to looping to search for another diamond if the nearest diamond is in the same direction as the enemy
                if delta_x_en == delta_x_dm and delta_y_en == delta_y_dm:
                    dm_candidate.remove(nearest_dm)
                
                # Return the nearest diamond if it is not in the same direction as the enemy
                else:
                    return nearest_dm
    
    def next_move(self, board_bot: GameObject, board: Board):
        bot = board_bot
        teleports_position = []
        red_position = []
        enemy_position = []
        diamond_positions = []
        diamonds = []

        # Store the base position of the bot.
        base_position = bot.properties.base

        # Iterate through the game objects on the board and categorize them based on their type.
        for obj in board.game_objects:
            if obj.type == "DiamondGameObject":
                # Exclude certain diamonds based on conditions.
                if bot.properties.diamonds >= 4 and obj.properties.points == 2:
                    pass
                else:
                    diamonds.append(obj)
                    diamond_positions.append(obj.position)
            elif obj.type == "TeleportGameObject":
                teleports_position.append(obj.position)
            elif obj.type == "BotGameObject":
                # Store the positions of enemy bots.
                if bot.properties.name != obj.properties.name:
                    enemy_position.append(obj.position)
            elif obj.type == "DiamondButtonGameObject":
                # Store the positions of red diamond buttons.
                red_position.append(obj.position)
        
        if self.getDistanceBetween(bot.position, teleports_position[0]) >= self.getDistanceBetween(bot.position, teleports_position[1]):
            teleports_position[0], teleports_position[1] = teleports_position[1], teleports_position[0]

        # Set the goal position based on various conditions.
        if (bot.properties.milliseconds_left < 10000 and bot.properties.diamonds > 0) or bot.properties.diamonds == 5:
            self.goal_position = base_position
            
        # elif self.bot.properties.milliseconds_left <= 7000 and self.isObjectInArea(self.bot.position, self.red_position, self.red_threshold) and self.redProcessor.is_bot_score_lower_than_enemies:
        #     self.goal_position = self.red_position[0]
        elif self.isObjectInArea(bot.position, enemy_position, 2):
            self.goal_position =   self.bot_process(bot, enemy_position, diamond_positions, diamonds, base_position)
        else:
            # Process the diamond logic.
            self.diamond_process(base_position, diamonds, diamond_positions, bot, red_position[0])

        # Adjust goal position based on teleport locations.
        if self.goal_position !=None and self.getDistanceWithPortalRelBase(bot.position, teleports_position[0], teleports_position[1], self.goal_position, base_position) < self.getDistanceBetween(bot.position, self.goal_position) + self.getDistanceBetween(self.goal_position, base_position):
            self.goal_position = teleports_position[0]

        if self.goal_position:
            # Calculate the direction based on the current and goal positions.
            delta_x, delta_y = self.get_direction_v2(
                bot.position.x,
                bot.position.y,
                self.goal_position.x,
                self.goal_position.y
            )

            # Check for teleport dodging conditions and update the goal position if necessary.
            curplusportal = Position(x=bot.position.x + delta_x, y=bot.position.y + delta_y)
            if self.goal_position != teleports_position[0] and curplusportal == teleports_position[0]:
                self.goal_position = self.dodge_tele(bot.position, teleports_position[0], teleports_position[1], self.goal_position)
                delta_x, delta_y = self.get_direction_v2(bot.position.x, bot.position.y, self.goal_position.x, self.goal_position.y)
            
        else:
            # Roam around if no specific goal position is set.
            delta = self.directions[self.current_direction]
            delta_x = delta[0]
            delta_y = delta[1]
            if random.random() > 0.6:
                self.current_direction = (self.current_direction + 1) % len(self.directions)
           
        return delta_x, delta_y