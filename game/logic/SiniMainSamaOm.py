from typing import Optional, Tuple

from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from ..util import get_direction

import time

class OptBot:
    def __init__(self):
        self.init = False
        '''
        variable just to run once in game loop.
        '''
        self.current_position: Optional[Position] = None
        '''
        our bot current position `Position(x, y) - object`
        '''
        self.base_position: Optional[Position] = None
        '''
        our bot base position `Position(x, y) - object`
        '''
        self.enemy_bots: Tuple[list[GameObject], int] = []
        '''
        list of enemy bots metadata
        '''
        self.teleporter: list[Position] = []
        '''
        list of teleporter position `[[Position(x, y), time_left], ...] - object`
        '''
        self.teleporter_anchor: list[str] = []
        '''
        list of teleporter anchor id `[id, ...]`
        '''
        self.is_teleporter_move: bool = False
        '''
        triggered everytime teleporter move
        '''
        self.list_objective = []
        '''
        list of diamonds and reset buttons.
        
        structure `[[Position(x, y), points, priority], ...]`
        '''
        self.target_position: Optional[Position] = None
        '''
        target position. object `Position(x, y)`
        '''
        self.start_time = None
        '''
        the time anchor for counting teleporter
        '''
        self.teleporter_time_remaining = None
        '''
        time left in second till teleporter moved randomly
        '''
        self.teleporter_time_config = 30
        '''
        time configuration for teleporter random moved in seconds
        '''

    def set_current_position(self, board_bot: GameObject) -> None:
        """
        set current position every iteration.
        """
        self.current_position = board_bot.position
    
    def set_info_once(self, board_bot: GameObject) -> None:
        """
        set information only once such as:
        - base position
        """
        if not self.init:
            self.base_position = board_bot.properties.base
            self.start_time = time.time() // 1
            self.init = True

    def set_teleporter(self, board: Board) -> None:
        """
        set teleporter locations
        """
        self.teleporter.clear()
        print("teleporter time remaining:", self.teleporter_time_remaining)
        
        self.teleporter = [[x.position, self.teleporter_time_remaining] for x in board.game_objects if x.type == "TeleportGameObject"]

        # set anchor and check if teleporter moved
        temp = [x.position for x in board.game_objects if x.type == "TeleportGameObject"]
        for x in temp:
            if x not in self.teleporter_anchor:
                self.is_teleporter_move = True
                print("=== TELEPORTER MOVED")
        
        if(self.is_teleporter_move):
            self.teleporter_anchor.clear()
            for x in temp:
                self.teleporter_anchor.append(x)

        def func(x):
            """sort teleporter by closest distance to current_position"""
            return self.get_distance(self.current_position, x[0])
        self.teleporter.sort(key=func)
    
    def get_distance(self, a: Position, b: Position) -> int:
        """
        get distance between 2 position

        return:
        - distance: `int`
        """
        dist_x = abs(a.x - b.x)
        dist_y = abs(a.y - b.y)
        dist = dist_x + dist_y
        return dist
    
    def get_distance_teleporter(self, a: Position, b: Position) -> int:
        """
        get distance between 2 position account teleporter to SELF
        """
        return self.get_distance(a, self.teleporter[0][0]) + self.get_distance(self.teleporter[1][0], b)

    def set_priority(self, obj) -> None:
        """
        set priorities for objectives.

        obj structure `[Position(x, y), points, priority]`
        """
        distance = min(
            self.get_distance(self.current_position, obj[0]),
            self.get_distance_teleporter(self.current_position, obj[0])
        )

        obj[2] = distance / obj[1]

        return obj

    def set_list_objective(self, board: Board) -> None:
        """
        set list objectives location and points. such as:
        - diamonds
        - reset button
        """
        # add all diamonds
        temp_objective = [[x.position, x.properties.points, 0]for x in board.diamonds]
        # add all reset buttons
        reset_button = [[x.position, 0.75, 0] for x in board.game_objects if x.type == "DiamondButtonGameObject"]
        temp_objective.append(reset_button[0])

        self.list_objective = list(map(self.set_priority, temp_objective))
    
        # sort by priority
        def func(e):
            """sort list_objective by 2nd key - priority"""
            return e[2]
        self.list_objective.sort(key=func)

    def go_to_destination(self, board_bot: GameObject) -> None:
        """
        go to destination
        """
        dist_normal = self.get_distance(self.current_position, self.target_position)
        dist_teleporter = self.get_distance_teleporter(self.current_position, self.target_position)

        print("dist normal : ", dist_normal)
        print("dist teleporter : ", dist_teleporter)

        if(dist_teleporter < dist_normal):
            if(dist_teleporter+2 >= board_bot.properties.milliseconds_left // 1000):
                if (self.teleporter[0][1]+2 >= self.get_distance(self.current_position, self.teleporter[0][0])):
                    # get closest teleporter
                    self.target_position = self.teleporter[0][0]
                    return
            
        # self.target_position = self.base_position
        
    def initialize(self, board_bot : GameObject, board: Board) :
        # init once on run time
        self.set_info_once(board_bot)

        # set time
        self.teleporter_time_remaining = self.teleporter_time_config - (time.time() // 1 - self.start_time)

        # info setup
        self.set_current_position(board_bot)
        self.set_teleporter(board)
        self.set_list_objective(board)
        

    def time_to_go_home(self, board_bot: GameObject):
        """
        function to set bot to go home.
        based on distance from base and time left
        """
        dist_normal = self.get_distance(self.current_position, self.base_position)
        dist_teleporter = self.get_distance_teleporter(self.current_position, self.base_position)

        # ditambah 2 untuk buffer
        buffer = 2
        
        if (dist_teleporter < dist_normal):    
            if(dist_teleporter+buffer >= board_bot.properties.milliseconds_left // 1000):
                if (self.teleporter[0][1]+buffer >= self.get_distance(self.current_position, self.teleporter[0][0])):
                    return True
            return False
        else:
            if(dist_normal+buffer >= board_bot.properties.milliseconds_left // 1000):
                return True
            return False

    def next_move(self, board_bot: GameObject, board: Board) -> Tuple[int, int]:
        '''
        default function *main game loop*!
        '''
        time_start = time.time()

        self.initialize(board_bot, board)

        # teleporter check
        if(self.is_teleporter_move):
            self.start_time = time.time() // 1
            self.is_teleporter_move = False

        print("bot time remaining:", board_bot.properties.milliseconds_left // 1000)
        print("current position = ", end='')
        print(self.current_position)

        print("inventory: ", board_bot.properties.diamonds)

        # set destination
        if(self.time_to_go_home(board_bot)):
            print("=== TIME TO GO HOME")
            self.target_position = self.base_position
        elif (board_bot.properties.diamonds == 5):
            print("=== INVENTORY PENUH")
            self.target_position = self.base_position
        else:
            if (board_bot.properties.diamonds == 4):
                # hapus seluruh diamond merah
                print("=== DIAMOND MERAH DIHAPUS")
                self.list_objective = list(filter(lambda x: x[1] != 2, self.list_objective))

            self.target_position = self.list_objective[0][0]


        # get position
        print("Teleporter position : ", end="")
        print(self.teleporter[0])
        self.go_to_destination(board_bot)

        print("Possible Targets: ", end='')
        print(self.list_objective[0:5])

        print("Target position : ", end='')
        print(self.target_position)

        # get direction
        direction = get_direction(
            self.current_position.x,
            self.current_position.y,
            self.target_position.x,
            self.target_position.y
        )

        time_end = time.time()
        print("Elapsed Time:", time_end - time_start)

        return direction[0], direction[1]
