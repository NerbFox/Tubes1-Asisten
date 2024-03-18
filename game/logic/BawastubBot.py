from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
import random

class BawastubBot(BaseLogic):
    def __init__(self):
        self.directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        self.justTackle = False

    def direction(self, currx, curry, targetx, targety, bw, bh):
        delta_x = 0; delta_y = 0

        # If current position is our target
        # Recall-recall abangkuh        
        if currx == targetx and curry == targety:
            rand = [direction
                    for direction in self.directions
                    if 0 <= currx + direction[0] < bw 
                    and 0 <= curry + direction[1] < bh
                    ]
    
            # random move
            return rand[random.randint(0, len(rand) - 1)]


        # jika posisi x sudah sama dengan target
        elif currx == targetx:
            # jika posisi target berada di bawah = turun
            if curry < targety:
                delta_y = 1
            else: # jika posisi target berada di atas = naik
                delta_y = -1
        
        # jika posisi y sudah sama dengan target
        elif curry == targety:
            # jika posisi target berada di kanan = ke kanan
            if currx < targetx:
                delta_x = 1
            else: # jika posisi target berada di kiri = ke kiri
                delta_x = -1
        
        # jika posisi x dan y belum sama dengan target
        else:
            # jika posisi target berada di kanan dan bawah
            if currx < targetx and curry < targety:
                #pilih random antara ke kanan atau ke bawah
                temp = random.randint(0, 1)
                delta_x = self.directions[temp][0]
                delta_y = self.directions[temp][1]
            
            # jika posisi target berada di kanan dan atas
            elif currx < targetx and curry > targety:
                #pilih random antara ke kanan atau ke atas
                temp = random.choice([0, 3])
                delta_x = self.directions[temp][0]
                delta_y = self.directions[temp][1]
            
            # jika posisi target berada di kiri dan bawah
            elif currx > targetx and curry < targety:
                #pilih random antara ke kiri atau ke bawah
                temp = random.randint(1,2)
                delta_x = self.directions[temp][0]
                delta_y = self.directions[temp][1]
            
            # jika posisi target berada di kiri dan atas
            else:
                #pilih random antara ke kiri atau ke atas
                temp = random.randint(2,3)
                delta_x = self.directions[temp][0]
                delta_y = self.directions[temp][1]
        

        return delta_x, delta_y
        
    
    def point_per_distance(self, currx, curry, game_object):
        # Calculate the point divide by distance
        return game_object.properties.points/(abs(currx - game_object.position.x) + abs(curry - game_object.position.y))

    def next_move(self, board_bot: GameObject, board: Board):
        current_post = board_bot.position
        base = board_bot.properties.base
        props = board_bot.properties
        diamond = [] ; button = None
        goal = None
        delta_x = 0 ; delta_y = 0


        """"
        Tackle First if one move (next) there is a bot
        """
        # If just tackle in the previous, maybe failed tackle
        # dont catch the enemy again
        if self.justTackle:
            self.justTackle = False
        # tackle first
        else:
            bot_positions = [obj.position for obj in board.game_objects if obj.type == 'BotGameObject']

            for direct in self.directions:
                new_x = current_post.x + direct[0]
                new_y = current_post.y + direct[1]
                # if the next position still on the board
                if 0 <= new_y < board.height and 0 <= new_x < board.width:
                    if Position(x=new_x, y=new_y) in bot_positions:
                        self.justTackle = True
                        return direct
        

        # GO HOME        
        if props.diamonds == 5:
            delta_x, delta_y = self.direction(current_post.x, current_post.y, base.x, base.y, board.width, board.height)

            return delta_x, delta_y


        for obj in board.game_objects:
            if obj.type == "DiamondGameObject":
                diamond.append(obj)
            elif obj.type == "DiamondButtonGameObject":
                button = obj
            

        if (props.milliseconds_left < ((abs(current_post.x - base.x) + abs(current_post.y - base.y))*1000)+1750):
            delta_x, delta_y = self.direction(current_post.x, current_post.y, base.x, base.y, board.width, board.height)

            return delta_x, delta_y
        else:
            if abs(current_post.x - button.position.x) + abs(current_post.y - button.position.y) <= 1:
                delta_x, delta_y = self.direction(current_post.x, current_post.y, button.position.x, button.position.y, board.width, board.height)
                
            else:
                for gem in diamond:
                    if props.diamonds == 4 and gem.properties.points == 2:
                        continue
                    if goal is None:
                        goal = gem
                    else:
                        if self.point_per_distance(current_post.x, current_post.y, gem) > self.point_per_distance(current_post.x, current_post.y, goal):
                            goal = gem
                delta_x, delta_y = self.direction(current_post.x, current_post.y, goal.position.x, goal.position.y, board.width, board.height)

            return delta_x, delta_y