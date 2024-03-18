import random
from typing import Optional

from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from ..util import get_direction
from collections import deque
from dataclasses import dataclass

MAX_GLOBAL_VALUE = 28

@dataclass
class Item:
    id: Optional[int] = None
    position: Optional[Position] = None
    item_type: Optional[str] = None
    name: Optional[str] = None
    value: Optional[int] = None


class savage(BaseLogic):
    def __init__(self):
        self.directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        self.goal_position: Optional[Position] = None
        self.current_direction = 0
        self.value_move = -1
        self.teleport_pos = []
        self.diamond_button_pos = []
        self.diamond1_pos = []
        self.diamond2_pos = []
        self.enemies = []
        self.base_game_pos = None
        self.board_mapping_component = []

    def move_position(self, current_position: Position, delta_x: int, delta_y: int):
        # Mekakukan gerakan dengan mengembalikan posisi baru
        return Position(current_position.y + delta_y,current_position.x + delta_x)
    
    def compute_distance(self, current_position: Position, destination_position: Position):
        # Menghitung Jarak dua buah posisi
        return abs(current_position.x - destination_position.x) + abs(current_position.y - destination_position.y)
    
    def status_coordinate_on_enemy(self, current_position: Position, enemy_position: Position):
        # Lakukan pengecekan terhadap status koordinat terhadap musuh (Apakah untung atau rugi jika bergerak ke koordinat tersebut)
        distance = self.compute_distance(current_position, enemy_position)
        if(distance==1): # Berpotensi ditackle musuh
            return -1
        elif(distance==0): # Berpotensi menackle musuh
            return 1
        else:
            return 0 # Tidak ada apa-apa
    
    def is_valid_coordinate(self, current_position: Position, width: int, height: int):
        # Lakukan pengencekan terhadap koordinat yang valid (Tidak melewati batas board)
        if(current_position.x < 0 or current_position.x >= width):
            return False
        if(current_position.y < 0 or current_position.y >= height):
            return False
        return True
    
    def store_all_component(self, board: Board, current_name: str, current_id: int):
        # Store each component items in the board to decrease the time complexity checking
        for i in board.game_objects:
            if(i.type == "TeleportGameObject"):
                self.teleport_pos.append(i.position)
            elif(i.type == "DiamondButtonGameObject"):
                self.diamond_button_pos.append(i.position)
            elif(i.type == "DiamondGameObject"):
                if(i.properties.points == 1):
                    self.diamond1_pos.append(i.position)
                else:
                    self.diamond2_pos.append(i.position)
                self.board_mapping_component[i.position.y][i.position.x] = Item(i.id, 
                                                                    i.position, 
                                                                    i.type, 
                                                                    i.properties.name, 
                                                                    i.properties.points)
            elif(i.type == "BaseGameObject"):
                if(i.properties.name == current_name):
                    self.base_game_pos = i.position
            elif(i.type == "BotGameObject"):
                if(i.id != current_id):
                    self.enemies.append(i)

    def next_move(self, board_bot: GameObject, board: Board):
        # Initialize component local variable
        current_name = board_bot.properties.name
        current_position = board_bot.position
        current_id = board_bot.id
        current_diamond = board_bot.properties.diamonds
        candidate_next_diamond = current_diamond
        max_val_dirr = [current_diamond, current_diamond, current_diamond, current_diamond]
        height = board.height
        width = board.width
        total_value_objektif = [(0,0), (0,0), (0,0), (0,0)]
        is_valid = [False, False, False, False]
        next_pos = []
        self.value_move = -1
        self.teleport_pos = []
        self.diamond_button_pos = []
        self.diamond1_pos = []
        self.diamond2_pos = []
        self.enemies = []
        self.base_game_pos = None
        self.board_mapping_component = []

        def mapping_diamonds():
            # prosedure untuk mapping diamond
            for i in range(4):
                temp_next_pos = self.move_position(current_position, self.directions[i][0], self.directions[i][1])
                next_pos.append(temp_next_pos)
                if(self.is_valid_coordinate(temp_next_pos, width, height)):
                    is_valid[i] = True

        def check_possibility_teleport():
            # Melakukan pengecekan terhadap kemungkinan teleport dan profitnya
            # Time Complexity O(M*N*K), N = 4, M = 2
            num_of_teleport = len(self.teleport_pos)
            for i in range(num_of_teleport):
                for k in range(4):
                    if(is_valid[k]):
                        # Kalo ada teleport di sekitar teleport koordinate bot
                        distance1 = self.compute_distance(next_pos[k], self.teleport_pos[i])
                        # Cek koordinat di sekitar teleport tujuan apakah ada profit
                        pos_after_teleport = self.teleport_pos[(i+1)%num_of_teleport]
                        if(self.is_valid_coordinate(pos_after_teleport, width, height)): # Cek koordinat geser tersebut valid atau tidak

                            # Kondisi pengecekan kalo udah teleport, dan ternyata basenya disekitarnya, masukkan sebagai profit
                            if(current_diamond>0):
                                distance2 = self.compute_distance(pos_after_teleport, self.base_game_pos)
                                value = MAX_GLOBAL_VALUE-(distance2+distance1)
                                if(value > total_value_objektif[k][0]):
                                    total_value_objektif[k] = (value, 0) # Profitnya MAX_GLOBAL_VALUE-2 karena jaraknya terhitung sebelum teleport

                            # Kalo udah teleport, ada diamond disekitarnya dan mencukupi buat diambil, masukkan sebagai profit
                            if(current_diamond + 1 <= 5 ):
                                for diamond1 in self.diamond1_pos:
                                    distance2 = self.compute_distance(pos_after_teleport, diamond1)
                                    value = MAX_GLOBAL_VALUE-(distance1+distance2)
                                    if(value > total_value_objektif[k][0]
                                       or (value == total_value_objektif[k][0] and total_value_objektif[k][1] < 1)):
                                        total_value_objektif[k] = (value,1) # Profitnya MAX_GLOBAL_VALUE-2 karena jaraknya erhitung sebelum teleport
                            if(current_diamond + 2 <= 5 ):
                                for diamond2 in self.diamond2_pos:
                                    distance2 = self.compute_distance(pos_after_teleport, diamond2)
                                    value = MAX_GLOBAL_VALUE-(distance1+distance2)
                                    if(value > total_value_objektif[k][0]
                                       or (value == total_value_objektif[k][0] and total_value_objektif[k][1] < 2)):
                                        total_value_objektif[k] = (value,2)

        def check_possibility_of_diamond1():
            # Melakukan pengecekan terhadap kemungkinan mendapatkan diamond 1
            # Time Complexity O(N*4)
            while len(self.diamond1_pos) != 0:
                diamond_pos = self.diamond1_pos.pop()
                for i in range(4):
                    if(is_valid[i]):
                        distance = self.compute_distance(next_pos[i], diamond_pos)
                        if(current_diamond + 1 <= 5): # Kalo masih bisa nampung gass aja
                            if(distance==0): # Kalo nextnya di posisi diamond
                                max_val_dirr[i] = current_diamond + 1
                            else: # Kalo engga hitung possibility profitnya dengan distance dan pointnya
                                value = MAX_GLOBAL_VALUE-distance
                                if(value > total_value_objektif[i][0]
                                   or (value == total_value_objektif[i][0] and total_value_objektif[i][1] < 1)):
                                    total_value_objektif[i] = (value, 1)
        
        def check_possibility_of_diamond2():
            # Melakukan pengecekan terhadap kemungkinan mendapatkan diamond 2
            # Time Complexity O(4*N)
            while len(self.diamond2_pos) != 0:
                diamond_pos = self.diamond2_pos.pop()
                for i in range(4):
                    if(is_valid[i]):
                        distance = self.compute_distance(next_pos[i], diamond_pos)
                        if(current_diamond + 2 <= 5): # Kalo masih bisa nampung, gass aja
                            if(distance==0): # Kalo nextnya di posisi diamond
                                max_val_dirr[i] = current_diamond + 2
                            else: # Kalo engga hitung possibility profitnya dengan distance dan pointnya
                                value = MAX_GLOBAL_VALUE-distance
                                if(value > total_value_objektif[i][0]
                                   or (value == total_value_objektif[i][0] and total_value_objektif[i][1] < 2)):
                                    total_value_objektif[i] = (value, 2)
        
        def check_possibility_enemy():
            # Time Complexity O(4*N)
            count_potential_increase_diamond_of_enemy = 0
            while len(self.enemies) != 0:
                enemy = self.enemies.pop()
                for i in range(4): 
                    # Dilakukan pengecekan terhadap state musuh
                    # Kemungkinan berapa musuh yang bisa dapat diamond untuk dilakukan aksi reset diamond (kalo ada diamond button disekitar)
                    enemy.position = self.move_position(enemy.position, self.directions[i][0], self.directions[i][1])
                    if(self.is_valid_coordinate(enemy.position, width, height) and self.board_mapping_component[enemy.position.y][enemy.position.x].id != None):
                        count_potential_increase_diamond_of_enemy += 1

                    # Dilakukan pengecekan terhadap bot kita 
                    if(is_valid[i]):
                        status_on_enemy = self.status_coordinate_on_enemy(next_pos[i],enemy.position)
                        if(status_on_enemy==1): # Kalo profit
                            if(enemy.properties.diamonds>0):
                                max_val_dirr[i] += enemy.properties.diamonds
                        elif(status_on_enemy==-1): # Kalo rugi
                            max_val_dirr[i] = 0
            return count_potential_increase_diamond_of_enemy
        
        def move_to_get_potential_profit_to_move():
            # Fungsi untuk melakukan pengecekan terhadap kemungkinan mendekati posisi diamond
            # Time Complexity O(N), N=4
            temp_value_max = -1
            point_max = -1
            for i in range(4):
                if(current_diamond + total_value_objektif[i][1] <= 5):
                    if(total_value_objektif[i][0] > temp_value_max or 
                       (total_value_objektif[i][0] == temp_value_max and total_value_objektif[i][1] > point_max)):
                        temp_value_max = total_value_objektif[i][0]
                        point_max = total_value_objektif[i][1]
                        self.value_move = i
            return temp_value_max

        def selection_function(count_potential_increase_diamond_of_enemy: int, candidate_next_diamond: int = candidate_next_diamond):
            # Time Complexity O(4*N)
            delta_x = 0
            delta_y = 0
            # Check possibility dari kemungkinan value dari diamond yang diperoleh pada salah satu dari 4 arah
            for i in range(4):
                if(max_val_dirr[i] > candidate_next_diamond):
                    candidate_next_diamond = max_val_dirr[i]
                    self.value_move = i

            # Jika tidak bisa mendapatkan diamond (diamond next jumlahnya tetap)
            if(candidate_next_diamond == current_diamond):
                temp_value_max = move_to_get_potential_profit_to_move()

                # Kalo udah punya diamond, coba balik ke base sambil bandingin lebih worth balik atau cari potensi dapet diamond
                if(current_diamond>0):
                    distance_to_base = self.compute_distance(self.base_game_pos,current_position)
                    if(distance_to_base>0 and MAX_GLOBAL_VALUE-temp_value_max >= distance_to_base-1): # Profit balik base lebih baik dari maximum sementara profit
                        delta_x, delta_y = get_direction(
                                                current_position.x,
                                                current_position.y,
                                                self.base_game_pos.x,
                                                self.base_game_pos.y,
                                            )
                        return delta_x, delta_y

                # Kalo enemy punya diamond dan kita deket diamond button
                # Coba ambil diamond button buat reset diamond sekitar (supaya musuh ga jadi ambil diamond disekitar kiri,kanan,atas,bawah)
                if(count_potential_increase_diamond_of_enemy>0):
                    while len(self.diamond_button_pos) != 0:
                        diamond_button_pos = self.diamond_button_pos.pop()
                        for i in range(4):
                            if(is_valid[i]):
                                distance = self.compute_distance(next_pos[i], diamond_button_pos)
                                if(distance==0):
                                    return self.directions[i][0], self.directions[i][1]

            # Kalo nextnya bakal bergerak (Ga diem aja)
            if(self.value_move != -1):
                delta_x = self.directions[self.value_move][0]
                delta_y = self.directions[self.value_move][1]
        
            return delta_x, delta_y

        # Main Logic of the Savage Bot Move

        # Simpan semua komponen diamond supaya bisa dilakukan pengecekan dengan cepat
        # Pengecekan dengan indeks array, Time Complexity O(1)
        for i in range(height):
            self.board_mapping_component.append([Item() for j in range(width)])

        self.store_all_component(board, current_name, current_id)
        
        # Candidate Checking Part
        mapping_diamonds()

        check_possibility_teleport()

        check_possibility_of_diamond1()

        check_possibility_of_diamond2()

        count_potential_increase_diamond_of_enemy = check_possibility_enemy()

        # Selection Part
        delta_x, delta_y = selection_function(count_potential_increase_diamond_of_enemy)

        return delta_x, delta_y
