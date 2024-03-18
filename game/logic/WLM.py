from typing import Optional, List

from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from ..util import get_direction

class MinerLovers(BaseLogic):
    def __init__(self):
        # Position attributes
        self.goal_position: Optional[Position] = None   # Current goal position
        self.buttonPos: Optional[Position] = None       # Button position
        
        # Boolean attributes
        self.useTel = False                             # Decide if bot needs to use teleporter
        
        # Time attributes
        self.lastUseButton: Optional[int] = None        # Last time the button is used
        
        # Miscelanneous attributes
        self.telA: Optional[GameObject] = None          # Shortest teleporter to bot
        self.telB: Optional[GameObject] = None          # Farthest teleporter to bot
        self.diamondDensity = 1                         # Density of diamonds near base (0 <= diamondDensity <= 1)
    
    # Get absolute distance between two positions (horizontal dist + vertical dist)
    def block_distance(self, a: Position, b: Position):
        return abs(a.x - b.x) + abs(a.y - b.y)
    
    # Get teleporters on board as (telA, telB) where telA is the nearest teleporter to the bot
    def get_teleporters(self, bot: GameObject, board: Board):
        pos = bot.position
        
        # Get teleporters on board
        tel: List[GameObject] = []
        for obj in board.game_objects:
            if obj.type == "TeleportGameObject":
                tel.append(obj)
        
        # Get distances of both teleporters
        distA = self.block_distance(pos, tel[0].position)
        distB = self.block_distance(pos, tel[1].position)
        
        # Decide telA, telB
        if distA <= distB:
            return (tel[0], tel[1])
        else:
            return (tel[1], tel[0])
    
    # Calculate priority points of an object
    def priorityPoints(self, bot: GameObject, obj: GameObject) -> float: 
        props = bot.properties
        
        # Get important distance values
        # dist              = Distance from bot to object
        # dist_to_base      = Distance from object to base
        # dist_with_tel     = Distance from bot to object (with teleporters)
        dist = self.block_distance(bot.position, obj.position)
        dist_to_base = self.block_distance(bot.properties.base, obj.position)
        dist_with_tel = self.block_distance(bot.position, self.telA.position) + self.block_distance(self.telB.position, obj.position)
        
        # Decide if distance using teleporter is shorter
        if dist_with_tel < dist and bot.position != self.telA.position:
            self.useTel = True
            dist = dist_with_tel
        else:
            self.useTel = False
        
        # Get priority points
        if dist == 0:       # divisionByZero error handler
            return 0
        else:
            if obj.type == "DiamondGameObject":
                if ((props.diamonds + obj.properties.points) > props.inventory_size):       # If inventory is full, return 0
                    return 0
                elif obj.properties.points == 2:                        # If red diamond, multiplier is 1.5 
                    return 1.5 / (dist + (dist_to_base * 0.5))
                else:                                                   # If blue diamond, multiplier is 1
                    return 1 / (dist + (dist_to_base * 0.5))
            elif obj.type == "DiamondButtonGameObject":
                # If button is still in cooldown, return 0
                if self.lastUseButton:
                    return 0
                
                # Get priority point of button
                points = (1.2 / dist) * self.diamondDensity
                
                # If button position has moved, change button position attribute
                if obj.position != self.buttonPos:
                    self.buttonPos = obj.position
                    self.lastUseButton = bot.properties.milliseconds_left
                
                return points
    
    # Decide the highest priority object as next goal  
    def nextGoal(self, bot: GameObject, board: Board):
        # Helper variables
        useTel = False                                              # Decide if bot should use teleporter
        max_points = self.priorityPoints(bot, board.diamonds[0])    # Current max points
        goal_pos = board.diamonds[0].position                       # Current goal position
        
        # Variables for calculating diamond density
        diam_dist_total = 0                                         # Total distance between all diamonds and base
        diam_dist_max = 0                                           # Max distance between all diamonds and base
        diam_count = 0                                              # Total amount of diamonds in the board
        
        # Iterate through all game objects to get the object with max priority points
        for obj in board.game_objects:
            if obj.type == "DiamondGameObject" or obj.type == "DiamondButtonGameObject":
                # Get priority point of object
                points = self.priorityPoints(bot, obj)
                
                # If object point is greater, max_points = point
                if points > max_points:
                    max_points = points
                    goal_pos = self.telA.position if self.useTel else obj.position
                
                # If object is a diamond, update diamond density variables
                if obj.type == "DiamondGameObject":
                    diam_count += 1 
                    diam_dist = self.block_distance(bot.properties.base, obj.position)
                    diam_dist_total += diam_dist
                    if diam_dist > diam_dist_max:
                        diam_dist_max = diam_dist
        
        # Calculate diamond density        
        self.diamondDensity = (diam_dist_total * 2 / diam_count) / diam_dist_max
        
        # Calculate points for returning to home
        # home_dist         = Distance from bot to home
        # home_dist_tel     = Distance from bot to home (with teleporters)
        home_dist = self.block_distance(bot.position, bot.properties.base)
        home_dist_tel = self.block_distance(bot.position, self.telA.position) + self.block_distance(self.telB.position, bot.properties.base)
        
        # Decide if bot should use teleporter
        if home_dist_tel < home_dist and bot.position != self.telA.position:
            home_dist = home_dist_tel
            useTel = True
        else:
            useTel = False
            
        # Calculate priority points for going back to base
        if home_dist > 0 and bot.properties.diamonds > 0:
            home_points = (0.12 * bot.properties.diamonds) / home_dist      # Home priority point
            seconds_left = bot.properties.milliseconds_left / 1000          # Time remaining for bot
            
            # Decide if bot should go back to base
            if (home_points > max_points or bot.properties.diamonds == bot.properties.inventory_size or seconds_left < 8):
                goal_pos = self.telA.position if useTel else bot.properties.base
        
        return goal_pos
    
    def next_move(self, bot: GameObject, board: Board):
        # Reset button press cooldown
        if self.lastUseButton and (self.lastUseButton - bot.properties.milliseconds_left) > 7000:
            self.lastUseButton = None
            
        # Get teleporter position
        tel = self.get_teleporters(bot, board)
        self.telA = tel[0]
        self.telB = tel[1]
        
        # Find next goal position
        self.goal_position = self.nextGoal(bot, board)
            
        # Set movement
        if self.goal_position:
            # We are aiming for a specific position, calculate delta
            delta_x, delta_y = get_direction(
                bot.position.x,
                bot.position.y,
                self.goal_position.x,
                self.goal_position.y,
            )
            
        return delta_x, delta_y