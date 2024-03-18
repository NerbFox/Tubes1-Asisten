from typing import Optional
from game.logic.base import BaseLogic
from game.models import Board, GameObject, Position
from game.util import get_direction


# LIST OF IMPROVEMENTS
# TODO: Implement AVOID TELEPORT ON THE WAY
# TODO: Implement back to base if already have 2 diamonds and time is near to end <TESTING>
# TODO: Implement back to base if base is near and have 3 diamonds <TESTING>
# TODO: Implement AVOID ENEMY ON THE WAY TO DIAMOND
# TODO: Implement back to base if enemy is near (distance 2) and have 3 diamonds

# TODO: Implement Simple Diamond Greedy Algorithm
class GreedyDiamondLogic(BaseLogic):
    static_goals : list[Position] = []
    static_goal_teleport : GameObject = None
    static_temp_goals : Position = None
    static_direct_to_base_via_teleporter : bool = False

    def __init__(self) -> None:
        self.directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        self.goal_position: Optional[Position] = None
        self.current_direction = 0
        self.distance = 0

    def next_move(self, board_bot: GameObject, board: Board):
        props = board_bot.properties
        self.board = board
        self.board_bot = board_bot
        self.diamonds = board.diamonds
        self.bots = board.bots
        self.teleporter = [d for d in self.board.game_objects if d.type == "TeleportGameObject"]
        self.redButton = [d for d in self.board.game_objects if d.type == "DiamondButtonGameObject"]
        self.enemy = [d for d in self.bots if d.id != self.board_bot.id]
        self.enemyDiamond = [d.properties.diamonds for d in self.enemy]

        # REMOVE ALL STATIC WHEN IN BASE
        if (self.board_bot.position == self.board_bot.properties.base):
            self.static_goals = []
            self.static_goal_teleport = None
            self.static_temp_goals = None
            self.static_direct_to_base_via_teleporter = False

        # REMOVE STATIC GOALS IN TELEPORT
        if (self.static_goal_teleport and self.board_bot.position == self.find_other_teleport(self.static_goal_teleport)):
            self.static_goals.remove(self.static_goal_teleport.position)
            self.static_goal_teleport = None
        if (not self.static_goal_teleport and self.board_bot.position in self.static_goals):
            self.static_goals.remove(self.board_bot.position)
        
        # Remove temp goal if already reached
        if (self.board_bot.position == self.static_temp_goals):
            self.static_temp_goals = None

        # Analyze new state
        if props.diamonds == 5 or (props.milliseconds_left < 5000 and props.diamonds > 1):
            # Move to base
            self.goal_position = self.find_best_way_to_base()
            if not self.static_direct_to_base_via_teleporter:
                self.static_goals = []
                self.static_goal_teleport = None
        else:
            if (len(self.static_goals) == 0):
                self.find_nearest_diamond()
            self.goal_position = self.static_goals[0]
    

        if (self.calculate_near_base() and props.diamonds > 2):
            self.goal_position = self.find_best_way_to_base()
            if not self.static_direct_to_base_via_teleporter:
                self.static_goals = []
                self.static_goal_teleport = None

        if self.static_temp_goals: # If there is a temp goal, use it
            self.goal_position = self.static_temp_goals

        # Attack bot lain
        current_position = board_bot.position
        if self.enemy and props.diamonds < 3:
            self.enemy = sorted(self.enemy, key=lambda bot: abs(bot.position.x - current_position.x) + abs(bot.position.y - current_position.y), reverse=True)
            goal_distance = abs(self.goal_position.x - current_position.x) + abs(self.goal_position.y - current_position.y)
            bot_distance = abs(self.enemy[0].position.x - current_position.x) + abs(self.enemy[0].position.y - current_position.y)
            nearest_enemy = self.enemy[0]
            if nearest_enemy.properties.diamonds > 2 and bot_distance < goal_distance:
                self.goal_position = nearest_enemy.position

        # Calculate next move
        if self.goal_position:
            # Check if there is a teleporter on the path
            if (not self.static_temp_goals):
                self.obstacle_on_path(
                    'teleporter',
                    current_position.x,
                    current_position.y,
                    self.goal_position.x,
                    self.goal_position.y,
                )


            # Check if there is a red diamond on the path
            if (props.diamonds == 4):
                self.obstacle_on_path(
                    'redDiamond',
                    current_position.x,
                    current_position.y,
                    self.goal_position.x,
                    self.goal_position.y,
                )
            
            # We are aiming for a specific position, calculate delta
            delta_x, delta_y = get_direction(
                current_position.x,
                current_position.y,
                self.goal_position.x,
                self.goal_position.y,
            )
        else:
            # Roam around
            delta = self.directions[self.current_direction]
            delta_x = delta[0]
            delta_y = delta[1]
            self.current_direction = (self.current_direction + 1) % len(
                self.directions
            )

        if (delta_x == 0 and delta_y == 0):
            # Reset goal
            self.static_goals = []
            self.static_direct_to_base_via_teleporter = False
            self.static_goal_teleport = None
            self.static_temp_goals = None
            self.goal_position = None
            tempMove = self.next_move(board_bot, board)
            delta_x, delta_y = tempMove[0], tempMove[1]

        return delta_x, delta_y
    
    #Calculate the best way to base
    def find_best_way_to_base(self):
        current_position = self.board_bot.position
        base = self.board_bot.properties.base
        base_position = Position(base.y, base.x)

        # Calculate distance to base with direct and teleporter
        base_distance_direct = abs(base.x - current_position.x) + abs(base.y - current_position.y)
        nearest_teleport_position, far_teleport_position, nearest_tp = self.find_nearest_teleport()

        if (nearest_teleport_position == None and far_teleport_position == None):
            return base_position

        # Find the best way to base
        base_distance_teleporter = abs(base.x - far_teleport_position.x) + abs(base.y - far_teleport_position.y) + abs(nearest_teleport_position.x - current_position.x) + abs(nearest_teleport_position.y - current_position.y)
        if (base_distance_direct < base_distance_teleporter):
            return base_position
        else:
            self.static_direct_to_base_via_teleporter = True
            self.static_goal_teleport = nearest_tp
            self.static_goals = [nearest_teleport_position, base]
            return nearest_teleport_position
    
    def calculate_near_base(self):
        current_position = self.board_bot.position
        base = self.board_bot.properties.base

        # Calculate distance to base with direct and teleporter
        base_distance = abs(base.x - current_position.x) + abs(base.y - current_position.y)
        base_distance_teleporter = self.find_base_distance_teleporter()
        distance = base_distance_teleporter if base_distance_teleporter < base_distance else base_distance

        if (distance == 0):
            return False
        
        return distance < self.distance

    def find_base_distance_teleporter(self):
        current_position = self.board_bot.position

        # Calculate distance to base with teleporter
        nearest_teleport_position, far_teleport_position, nearest_teleport = self.find_nearest_teleport()

        if (nearest_teleport_position == None and far_teleport_position == None and nearest_teleport == None):
            return float("inf")

        base = self.board_bot.properties.base
        base_distance_teleporter = abs(base.x - far_teleport_position.x) + abs(base.y - far_teleport_position.y) + abs(nearest_teleport_position.x - current_position.x) + abs(nearest_teleport_position.y - current_position.y)
        return base_distance_teleporter    

    def find_nearest_diamond(self) -> Optional[Position]:
        direct = self.find_nearest_diamond_direct() # distance, position
        teleport = self.find_nearest_diamond_teleport() # distance, [teleportPosition, diamondPosition]
        redButton = self.find_nearest_red_button() # distance, position
        if (direct[0] < teleport[0] and direct[0] < redButton[0]):
            self.static_goals = [direct[1]]
            self.distance = direct[0]
        elif (teleport[0] < direct[0] and teleport[0] < redButton[0]):
            self.static_goals = teleport[1]
            self.static_goal_teleport = teleport[2]
            self.distance = teleport[0]
        else:
            self.static_goals = [redButton[1]]
            self.distance = redButton[0]
    
    # Find the nearest red button
    def find_nearest_red_button(self):
        current_position = self.board_bot.position
        distance = abs(self.redButton[0].position.x - current_position.x) + abs(self.redButton[0].position.y - current_position.y)
        return distance, self.redButton[0].position

    # Find the nearest teleport
    def find_nearest_teleport(self):
        nearest_teleport_position, far_teleport_position, nearest_tp = None, None, None
        min_distance = float("inf")
        for teleport in self.teleporter:
            distance = abs(teleport.position.x - self.board_bot.position.x) + abs(teleport.position.y - self.board_bot.position.y)
            if distance == 0:
                return None, None, None
            if distance < min_distance:
                min_distance = distance
                nearest_teleport_position,far_teleport_position = teleport.position, self.find_other_teleport(teleport)
                nearest_tp = teleport
        return nearest_teleport_position,far_teleport_position, nearest_tp
    
    # Find the other teleport
    def find_other_teleport(self, teleport: GameObject):
        for t in self.teleporter:
            if t.id != teleport.id:
                return t.position
            
    # Find the nearest diamond with teleport
    def find_nearest_diamond_teleport(self) -> Optional[Position]:
        current_position = self.board_bot.position
        nearest_teleport_position, far_teleport_position, nearest_teleport = self.find_nearest_teleport()

        if (nearest_teleport_position == None and far_teleport_position == None and nearest_teleport == None):
            return float("inf")
    
        min_distance = float("inf")
        nearest_diamond = None

        # Calculate distance to diamond with teleport
        for diamond in self.diamonds:
            distance = abs(diamond.position.x - far_teleport_position.x) + abs(diamond.position.y - far_teleport_position.y) + abs(nearest_teleport_position.x - current_position.x) + abs(nearest_teleport_position.y - current_position.y)
            distance /= diamond.properties.points
            if distance < min_distance and ((diamond.properties.points == 2 and self.board_bot.properties.diamonds != 4) or (diamond.properties.points == 1)):
                min_distance = distance
                nearest_diamond = [nearest_teleport_position, diamond.position]
        return min_distance, nearest_diamond, nearest_teleport
    
    # Find the nearest diamond with direct
    def find_nearest_diamond_direct(self) -> Optional[Position]:
        current_position = self.board_bot.position
        min_distance = float("inf")
        nearest_diamond = None
        for diamond in self.diamonds:
            distance = abs(diamond.position.x - current_position.x) + abs(diamond.position.y - current_position.y)
            distance /= diamond.properties.points
            if distance < min_distance and ((diamond.properties.points == 2 and self.board_bot.properties.diamonds != 4) or (diamond.properties.points == 1)):
                min_distance = distance
                nearest_diamond = diamond.position
        return min_distance, nearest_diamond
    
    def obstacle_on_path(self, type, current_x, current_y, dest_x, dest_y):
        if type == 'teleporter':
            object = self.teleporter
        elif type == 'redDiamond':
            object = [d for d in self.diamonds if d.properties.points == 2]
        elif type == 'redButton':
            object = self.redButton
        
        for t in object:
            if current_x == t.position.x and  current_y == t.position.y:
                continue
            # Kondisi saat redDiamond sejajar dengan destinasi dalam sumbu y dan berada pada jalur current->dest
            if t.position.x == dest_x and (dest_y < t.position.y <= current_y or current_y <= t.position.y < dest_y):

                # Kondisi saat current tidak sejajar dengan destinasi pada sumbu y
                if (dest_x != current_x):
                    self.goal_position = Position(dest_y,dest_x-1) if dest_x > current_x else Position(dest_y,dest_x+1)

                # Kondisi saat current sejajar dengan destinasi pada sumbu y
                else:
                    # Handle kalo dipinggir kiri/kanan
                    if (dest_x <= 1):
                        self.goal_position = Position(dest_y,dest_x+1)
                    else:
                        self.goal_position = Position(dest_y,dest_x-1)
                self.static_temp_goals = self.goal_position

            # Kondisi saat redDiamond sejajar dengan destinasi dalam sumbu x dan berada pada jalur current->dest (Tidak akan pernah terjadi)
            elif t.position.y == dest_y and (dest_x < t.position.x <= current_x or current_x <= t.position.x < dest_x):

                # Kondisi saat current tidak sejajar dengan destinasi pada sumbu x
                if (dest_y != current_y):
                    self.goal_position = Position(dest_y-1,dest_x) if dest_y > current_y else Position(dest_y+1,dest_x)

                # Kondisi saat current sejajar dengan destinasi pada sumbu x
                else:
                    # Handle kalo dipinggir atas/bawah
                    if (dest_y <= 1):
                        self.goal_position = Position(dest_y+1,dest_x)
                    else:
                        self.goal_position = Position(dest_y-1,dest_x)

                self.static_temp_goals = self.goal_position
                        
            # Kondisi saat redDiamond sejajar dengan current dalam sumbu x dan berada pada jalur current->dest
            elif t.position.y == current_y and (dest_x < t.position.x <= current_x or current_x <= t.position.x < dest_x): 

                # Kondisi saat current tidak sejajar dengan destinasi pada sumbu x
                if (dest_y != current_y):
                    self.goal_position = Position(dest_y,current_x)

                # Kondisi saat current sejajar dengan destinasi pada sumbu y
                else:
                    # Handle kalo dipinggir kiri/kanan
                    if (current_y <= 1):
                        self.goal_position = Position(current_y+1,current_x)
                    else:
                        self.goal_position = Position(current_y-1,current_x)
                        
                self.static_temp_goals = self.goal_position
        
    