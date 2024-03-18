from typing import Optional
from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from ..util import get_direction

class SuperBot(BaseLogic):
    def __init__(self):
        self.directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        self.goal_position: Optional[Position] = None
        self.current_direction = 0

    def next_move(self, board_bot: GameObject, board: Board):
        def clamp(n, smallest, largest):
            return max(smallest, min(n, largest))


        def position_equals(a: Position, b: Position):
             return a.x == b.x and a.y == b.y
        
        def get_direction_Adv(current_x: int, current_y: int, dest_x: int, dest_y: int, avoidList):
            listBaru = [(a.x, a.y) for a in avoidList]
            delta_x = clamp(dest_x - current_x, -1, 1)
            delta_y = clamp(dest_y - current_y, -1, 1)
            if delta_x != 0:

                isBlocked = False
                if (delta_y != 0 and dest_x-delta_x == current_x):
                    for i in range(current_y, dest_y+delta_y, delta_y):
                        if ((current_x + delta_x, i) in listBaru):
                            isBlocked = True

                if (isBlocked or (current_x + delta_x, current_y) in listBaru):
                    delta_x = 0
                    if delta_y == 0:
                        if (current_y != 0 and not((current_x, current_y-1) in listBaru)):
                            delta_x, delta_y = 0, -1
                        else:
                            delta_x, delta_y = 0, 1
                else:
                    delta_y = 0
            if delta_x == 0:
                if ((current_x, current_y+delta_y) in listBaru):
                    if (current_x != 0 and not((current_x-1, current_y) in listBaru)):
                        delta_x, delta_y = -1, 0
                    else:
                        delta_x, delta_y = 1, 0

            return delta_x, delta_y

        props = board_bot.properties
        tombol_merah = [d for d in board.game_objects if d.type == "DiamondButtonGameObject"]   
        teleportasi = [d for d in board.game_objects if d.type == "TeleportGameObject"]    
        current_position = board_bot.position

        #INI BUAT TESTING
        arr_bot = board.bots
        list_diamonds = board.diamonds

        arr_1 = []
        arr_1_teleport = []
        filtered_bots = [bot for bot in arr_bot if not(bot.position.x == current_position.x and bot.position.y == current_position.y)]
        
        for diamond in list_diamonds:
            list_robot_terdekat = sorted(filtered_bots, key=lambda bots: abs(bots.position.x - diamond.position.x) + abs(bots.position.y - diamond.position.y))

            if filtered_bots:
                arr_1.append((diamond, list_robot_terdekat[0]))
                
            teleport_terdekat = sorted(teleportasi, key=lambda teleport: abs(teleport.position.x - diamond.position.x) + abs(teleport.position.y - diamond.position.y))
            list_robot_terdekat_teleportasi = sorted(filtered_bots, key=lambda bots: (abs(bots.position.x - teleport_terdekat[1].position.x) + abs(bots.position.y - teleport_terdekat[1].position.y)))

            if filtered_bots:
                arr_1_teleport.append((diamond, list_robot_terdekat_teleportasi[0]))
        
        arr_2 = []
        arr_2_teleportasi = []

        for elemen in arr_1:
              #ini buat jarak biasa
              distance_to_us = abs(elemen[0].position.x - current_position.x) + abs(elemen[0].position.y - current_position.y)
              selisih = distance_to_us -  (abs(elemen[1].position.x - elemen[0].position.x) + abs(elemen[1].position.y - elemen[0].position.y))
              arr_2.append((elemen[0], selisih, distance_to_us, 1))

 
        for elemen in arr_1_teleport:
              #ini buat jarak teleportasi
              teleport_terdekat = sorted(teleportasi, key=lambda teleport: (abs(teleport.position.x - elemen[0].position.x) + abs(teleport.position.y - elemen[0].position.y)))
              distance_to_us_teleportasi =  ((abs(elemen[0].position.x - teleport_terdekat[0].position.x) + abs(elemen[0].position.y - teleport_terdekat[0].position.y)) + (abs(teleport_terdekat[1].position.x - current_position.x) + abs(teleport_terdekat[1].position.y - current_position.y)))      
              selisih_teleportasi = distance_to_us_teleportasi - ((abs(elemen[0].position.x - teleport_terdekat[0].position.x) + abs(elemen[0].position.y - teleport_terdekat[0].position.y)) + (abs(teleport_terdekat[1].position.x - elemen[1].position.x) + abs(teleport_terdekat[1].position.y - elemen[1].position.y)))     
              arr_2_teleportasi.append((elemen[0], selisih_teleportasi, distance_to_us_teleportasi, 2))        

        arr_2_teleportasi = sorted(arr_2_teleportasi, key=lambda elem: elem[2])
        arr_2 = sorted(arr_2, key=lambda elem: elem[2])
        arr_2 = arr_2_teleportasi + arr_2                                                                           

        filtered_arr_2 = []
        filtered_arr_2 = [elem for elem in arr_2 if (elem[1] < 0 and elem[2] != 0)] 

        #print("selisih", filtered_arr_2[0][1])
        print("lokasi TM", tombol_merah[0].position.x, tombol_merah[0].position.y)

        selected_goal = tombol_merah[0]

        print("panjang", len(filtered_arr_2))

        if len(filtered_arr_2) > 0 and filtered_arr_2 != []:
            min_distance_elem = max(filtered_arr_2, key=lambda elem: elem[0].properties.points / elem[2]) 

            if min_distance_elem[3] == 1:
                selected_goal = min_distance_elem[0]
                if not(position_equals(selected_goal.position, current_position)):
                    selected_goal = min_distance_elem[0]
                else:
                    selected_goal = tombol_merah[0]
            else:
                 print("dia masuk sini teleport")
                 
                 lokasi_teleport_cik = sorted(teleportasi, key=lambda teleport: (abs(teleport.position.x - min_distance_elem[0].position.x) + abs(teleport.position.y - min_distance_elem[0].position.y)))

                 selected_goal = lokasi_teleport_cik[1]
                 if not(position_equals(selected_goal.position, current_position)):
                    selected_goal = lokasi_teleport_cik[1]
                 else:
                    selected_goal = tombol_merah[0]
            
        else:
             print("dia masuk tombol merah")
             selected_goal = tombol_merah[0]
    
        steps_to_base = abs(current_position.x - props.base.x) + abs(current_position.y - props.base.y)
        time_left = int(board_bot.properties.milliseconds_left / 1000)

        if (props.diamonds == props.inventory_size) or (steps_to_base == time_left) or (selected_goal.type == "DiamondGameObject" and selected_goal.properties.points == 2 and props.diamonds == props.inventory_size-1):

            base = board_bot.properties.base

            sort_base_to_teleport = sorted(teleportasi, key=lambda teleport: (abs(teleport.position.x - base.x) + abs(teleport.position.y - base.y)))
            
            jarak_base_biasa = abs(base.x - current_position.x) + abs(base.y - current_position.y)

            jarak_base_teleportasi = ((abs(base.x - sort_base_to_teleport[0].position.x) + abs(base.y - sort_base_to_teleport[0].position.y)) + (abs(current_position.x - sort_base_to_teleport[1].position.x) + abs(current_position.y - sort_base_to_teleport[1].position.y)))

            if jarak_base_biasa < jarak_base_teleportasi:
                  
                self.goal_position = base
            
            else:

                if not(position_equals(sort_base_to_teleport[1].position, current_position)):
                    self.goal_position = sort_base_to_teleport[1].position
                else:
                    self.goal_position = base

        else:

             self.goal_position = None

        dihindari = []

        if self.goal_position:
             
             penggabungan = teleportasi
            
             for unsur in penggabungan:
            
                if not(position_equals(unsur.position, self.goal_position)):

                    dihindari.append(unsur.position)

            
             delta_x, delta_y = get_direction_Adv(current_position.x, current_position.y, self.goal_position.x, self.goal_position.y, dihindari)
            

        else:
             penggabungan = teleportasi
            
             for unsur in penggabungan:
            
                if not(position_equals(unsur.position, selected_goal.position)):

                    dihindari.append(unsur.position)

             delta_x, delta_y = get_direction_Adv(current_position.x, current_position.y, selected_goal.position.x, selected_goal.position.y, dihindari)

        filtered_arr_2 = []
        
        dihindari = []
        
        return delta_x, delta_y