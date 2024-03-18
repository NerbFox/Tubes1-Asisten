from typing import Optional
from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from ..util import get_direction

class PCS(BaseLogic):
    def __init__(self):
        self.directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        self.goal_position: Optional[Position] = None
        self.current_direction = 0

    def next_move(self, board_bot: GameObject, board: Board):
        props = board_bot.properties
        current_pos_x = board_bot.position.x
        current_pos_y = board_bot.position.y
        base = board_bot.properties.base

        # Mencari semua Diamond berdasarkan jarak terhadap bot
        diamond_list = [d for d in board.game_objects if d.type == "DiamondGameObject"]
        distance_list = [0 for i in range (len(diamond_list))]
        for i in range (len(diamond_list)):
            distance_list[i] = abs(current_pos_x - diamond_list[i].position.x) + abs(diamond_list[i].position.y - current_pos_y)
            # Mengurangi jarak berdasarkan bobot diamond
            if diamond_list[i].properties.points == 2:
                distance_list[i]*=0.6
        # Memasangkan Diamond dan jarak serta mengurutkan
        distance_pos_list = list(zip(distance_list,diamond_list))
        distance_pos_list.sort(key=lambda x: x[0])



        # Mencari Teleporter
        teleporter_list = [t for t in board.game_objects if t.type == "TeleportGameObject"]
        tp_1 = teleporter_list[0]
        tp_2 = teleporter_list[1]
        dist_tp1 = abs(tp_1.position.x - current_pos_x) + abs(tp_1.position.y - current_pos_y)
        dist_tp2 = abs(tp_2.position.x - current_pos_x) + abs(tp_2.position.y - current_pos_y)

        # Mencari Teleporter terdekat
        close_tp = tp_1
        close_tp_dist = dist_tp1
        far_tp = tp_2
        if dist_tp1 > dist_tp2:
            close_tp = tp_2
            close_tp_dist = dist_tp2
            far_tp = tp_1
        
        # Mencari semua Diamond berdasarkan jarak terhadap Teleporter terjauh dari Bot
        distance_tp_list = [0 for i in range (len(diamond_list))]
        for i in range (len(diamond_list)):
            # Mengurangi jarak berdasarkan bobot diamond
            distance_tp_list[i] = abs(far_tp.position.x - diamond_list[i].position.x) + abs(far_tp.position.y - diamond_list[i].position.y) + close_tp_dist
            if diamond_list[i].properties.points == 2:
                distance_tp_list[i]*=0.6
        # Memasangkan Diamond dan jarak serta mengurutkan
        distance_pos_tp_list = list(zip(distance_tp_list,diamond_list))
        distance_pos_tp_list.sort(key=lambda x: x[0])


        # Mencari lokasi dan jarak Tombol
        buton_list = [b for b in board.game_objects if b.type == "DiamondButtonGameObject"]
        buton = buton_list[0]
        dist_but = (abs(buton.position.x - current_pos_x) + abs(buton.position.y - current_pos_y))*1.21 + 2

        dist_base = abs(current_pos_x - board_bot.properties.base.x) + abs(board_bot.properties.base.y - current_pos_y)
        dist_base_tp = abs(far_tp.position.x - board_bot.properties.base.x) + abs(board_bot.properties.base.y - far_tp.position.y) + close_tp_dist
       
        dist_base = abs(current_pos_x - board_bot.properties.base.x) + abs(board_bot.properties.base.y - current_pos_y)
        dist_base_tp = abs(far_tp.position.x - board_bot.properties.base.x) + abs(board_bot.properties.base.y - far_tp.position.y) + close_tp_dist
        min_dist = min(dist_base,dist_base_tp)+1
        # Balik ke Base apabila Inventory penuh atau waktu sudah mau habis
        if props.diamonds == 5 or min_dist>=(props.milliseconds_left / 1000):
            # Mendapatkan keperluan menggunakan teleporter untuk balik ke base
            if min_dist == (dist_base+1):
                self.goal_position = base
            else:
                #print("stuck111")
                self.goal_position = close_tp.position
            
        else:
            # Jika Diamond terdekat merah (untuk menghindari Bot 'stuck' pada diamond merah ketika tidak bisa mengambil)
            if props.diamonds == 4 and distance_pos_list[0][1].properties.points == 2:
                i=1
                while i<len(diamond_list)-1:
                    # Mencari Diamond bukan merah terdekat
                    closest = min(dist_but, distance_pos_tp_list[i][0], distance_pos_list[i][0])
                    if closest == distance_pos_list[i][0] and distance_pos_list[i][1].properties.points==1:
                        self.goal_position = distance_pos_list[i][1].position
                        break
                    elif closest == distance_pos_tp_list[i][0] and distance_pos_tp_list[i][1].properties.points==1:
                        #print("stuck222")
                        self.goal_position = close_tp.position
                        break
                    elif distance_pos_tp_list[i][0] > dist_but and distance_pos_list[i][0] > dist_but:
                        self.goal_position = buton.position
                        break
                    else:
                        i+=1
                # jika tidak ada balik ke Base
                if distance_pos_list[i][1].properties.points==2:
                    self.goal_position = base
                else:
                    self.goal_position = distance_pos_list[i][1].position
                    
            else:
                #Mencari Diamond terdekat. Apabila tidak ada mereset Board menggunakan Button
                closest = min(dist_but, distance_pos_tp_list[0][0], distance_pos_list[0][0])
                if closest == distance_pos_list[0][0]:
                    self.goal_position = distance_pos_list[0][1].position
                elif closest == distance_pos_tp_list[0][0]:
                    #print("stuck333")
                    self.goal_position = close_tp.position
                else:
                    self.goal_position = buton.position
        
        # Menghindari stuck di teleporter
        if current_pos_x == self.goal_position.x and current_pos_y == self.goal_position.y:
            self.goal_position = base
        current_position = board_bot.position
        #print("GOAL=" ,self.goal_position.x, self.goal_position.y)
        #print("TP CLOSE=",close_tp.position.x,close_tp.position.y)
        #print("TP FAR=",far_tp.position.x,far_tp.position.y)
        #print("DIAMOND=",distance_pos_list[i][1].position.x,distance_pos_list[i][1].position.y)
        #print("BASE=",base.x,base.y)

        if self.goal_position:
            # We are aiming for a specific position, calculate delta
            delta_x, delta_y = get_direction(
                current_position.x,
                current_position.y,
                self.goal_position.x,
                self.goal_position.y,
            )
        
        return delta_x, delta_y