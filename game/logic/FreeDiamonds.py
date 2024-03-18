from typing import Tuple, Optional
from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from ..util import get_direction, position_equals
import random

class FreeDiamonds(BaseLogic):
    def __init__(self):
        # Inisisalisasi atribut yang diperlukan
        self.directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        self.goal_position: Optional[Position] = None
        self.current_direction = 0

    def distance(self, bot_position: Position, goal: Position):
        """ Menghitung jarak antara bot dan goal position """
        distance = abs(goal.x - bot_position.x) + abs(goal.y - bot_position.y)
        return distance # tipe data int
    
    def teleporter_distance(self, bot_position: Position, target_position: Position, teleporters: list):
        if len(teleporters) < 2:
            return float('inf'), None  # Return infinite distance jika jumlah teleporter < 2

        teleporter_positions = [teleporter.position for teleporter in teleporters]
        teleporter1, teleporter2 = teleporter_positions

        # Distance ke teleporter 1 + distance dari teleporter 2 ke target
        distance_via_teleporter1 = self.distance(bot_position, teleporter1) + self.distance(teleporter2, target_position)

        # Distance ke teleporter 2 + distance dari teleporter 1 ke target
        distance_via_teleporter2 = self.distance(bot_position, teleporter2) + self.distance(teleporter1, target_position)

        if distance_via_teleporter1 < distance_via_teleporter2:
            return distance_via_teleporter1
        else:
            return distance_via_teleporter2

    def teleport(self, bot_position: Position, board: Board, goal_position: Position):
        """ Mencari jarak terpendek dari bot ke goal position dengan mempertimbangkan teleporter """
        list_teleporter = [i for i in board.game_objects if i.type == "TeleportGameObject"]
        # Membandingkan jarak tanpa melewati teleporter
        distance = self.distance(bot_position, goal_position)
        # Membandingkan jarak jika melewati teleporter 1 dan 2
        # Dari teleporter 1 ke teleporter 2
        in_teleporter1 = self.distance(bot_position, list_teleporter[0].position)
        out_teleporter1 = self.distance(list_teleporter[1].position, goal_position)
        distance1 = in_teleporter1 + out_teleporter1
        # Dari teleporter 2 ke teleporter 1
        in_teleporter2 = self.distance(bot_position, list_teleporter[1].position)
        out_teleporter2 = self.distance(list_teleporter[0].position, goal_position)
        distance2 = in_teleporter2 + out_teleporter2
        
        choosen = min(distance, distance1, distance2) 
        if (choosen == distance1):
            # Masuk ke teleporter 1
            print("TELEPORT") # debug
            return list_teleporter[0].position
        elif (choosen == distance2):
            # Masuk ke teleporter 2
            print("TELEPORT") # debug
            return list_teleporter[1].position
        else: # Tidak melewati teleporter
            return goal_position # tipe data Position

    def get_nearest_blue(self, bot_position: Position, board: Board):
        """ Mencari diamond biru terdekat """
        shortest_distance = float('inf')
        nearest_blue_position = None
        teleporters = [i for i in board.game_objects if i.type == "TeleportGameObject"]
        listblue = [i for i in board.diamonds if i.properties.points == 1]

        for diamond in listblue:
            distance = self.distance(bot_position, diamond.position)
            teleport_distance = self.teleporter_distance(bot_position, diamond.position, teleporters)
            # Bandingkan jarak jika melewati teleporter dan tidak
            if teleport_distance < distance:
                distance = teleport_distance
            if distance < shortest_distance:
                shortest_distance = distance
                nearest_blue_position = diamond.position
        print("NEAREST BLUE: ", nearest_blue_position) # debug
        return nearest_blue_position # tipe data Position

    def highest_density(self, bot_position: Position, board: Board, list_diamonds: list, prefer_low_value=False):
        """ Mencari diamond dengan density tertinggi """
        highest_density = 0
        highest_density_diamond = None
        highest_density_position = None
        teleporters = [i for i in board.game_objects if i.type == "TeleportGameObject"]

        if prefer_low_value:
            # Jika prefer_low_value True, cari diamond dengan poin 1
            diamond_position = self.get_nearest_blue(bot_position, board)
            return diamond_position # tipe data Position
        else:    
            for diamond in list_diamonds:
                distance = self.distance(bot_position, diamond.position)
                teleporters_distance = self.teleporter_distance(bot_position, diamond.position, teleporters)
                # Bandingkan jarak jika melewati teleporter dan tidak
                if teleporters_distance < distance:
                    distance = teleporters_distance
                    
                point = diamond.properties.points
                if distance != 0:
                    # Hitung density
                    density = point / distance
                    if density > highest_density or (density == highest_density and point > highest_density_diamond.properties.points):
                        # Bandingkan density, pilih yang tertinggi
                        # Jika density sama, pilih yang memiliki poin lebih tinggi
                        highest_density = density
                        highest_density_diamond = diamond
                        highest_density_position = diamond.position

            return highest_density_position # tipe data Position
    
    def is_tackle(self, board_bot: GameObject, bot_position: Position, board: Board):
        """ Mengecek apakah ada musuh yang bisa di-tackle """
        enemy = [i for i in board.bots if (i.position != bot_position)]
        target_position = None

        for target in enemy:
            if ((target.properties.diamonds > 0) and (board_bot.properties.diamonds < board_bot.properties.inventory_size) and (board_bot.properties.milliseconds_left < target.properties.milliseconds_left)):
                # Jika musuh memiliki diamond, bot belum penuh, dan waktu bot lebih sedikit
                # return target.position
                if (bot_position.x == target.position.x) and (abs(bot_position.y - target.position.y) == 1):
                    # Jika musuh ada di atas atau bawah bot
                    target_position = target.position
                elif (bot_position.y == target.position.y) and (abs(bot_position.x - target.position.x) == 1):
                    # Jika musuh ada di kiri atau kanan bot
                    target_position = target.position

        return target_position # tipe data Position
        
    def push_red_button(self, bot_position:Position, highest_density_position:Position, board: Board):
        """ Memilih antara red button atau diamond dengan density tertinggi berdasarkan jarak terdekat """
        list_red_button = [i for i in board.game_objects if i.type == "DiamondButtonGameObject"]
        diamond_distance = self.distance(bot_position, highest_density_position)
        
        for button in list_red_button:
            button_distance = self.distance(bot_position, button.position)
            if (button_distance < diamond_distance):
                print("OKE, KE RED BUTTON") # debug
                return button.position # tipe data Position
            else:
                print("GAMAU, KE DIAMOND AJA. LEBIH DEKET.") # debug
                return highest_density_position # tipe data Position 

    def next_move(self, board_bot: GameObject, board: Board) -> Tuple[int, int]:
        inventory_size = board_bot.properties.inventory_size if board_bot.properties.inventory_size else 5 # default 5
        bot_position = board_bot.position
        list_diamonds = board.diamonds
        collected = board_bot.properties.diamonds
        tackle_check = self.is_tackle(board_bot, bot_position, board)
        base_position = board_bot.properties.base
        milliseconds_left = board_bot.properties.milliseconds_left if board_bot.properties.milliseconds_left else 0
        seconds_left = milliseconds_left / 1000

        distance_to_base = self.distance(bot_position, base_position)

        if (collected == inventory_size):
            # Jika inventory penuh, kembali ke base
            self.goal_position = base_position
            print("FULL, AYO KE BASE") # debug
        elif (tackle_check):
            # Jika ada musuh yang bisa di-tackle, lakukan tackle
            self.goal_position = tackle_check
            print("TACKLE: ", tackle_check) # debug
        else:
            if (collected == inventory_size - 1):
                # Jika inventory hampir penuh, ubah strategi untuk mengumpulkan diamond poin 1
                highest_density_position = self.highest_density(bot_position, board, list_diamonds, True)
                print("INVENTORY HAMPIR PENUH, KE DIAMOND BIRU") # debug
            else:
                # Ke diamond dengan density tertinggi
                highest_density_position = self.highest_density(bot_position, board, list_diamonds, False)
                print("KE DIAMOND DENGAN DENSITY TERTINGGI") # debug

            if (seconds_left - 2 <= distance_to_base and collected > 0):
                # Jika waktu tersisa dalam detik kurang lebih sama dengan jarak ke base, kembali ke base
                if (not position_equals(bot_position, base_position)):  
                    self.goal_position = base_position
                    print("WAKTU HABIS, AYO KE BASE") # debug
            elif (len(list_diamonds) <= 7):
                # Jika diamond kurang dari 7, pilih antara red button atau diamond dengan density tertinggi
                self.goal_position = self.push_red_button(bot_position, highest_density_position, board)
                print("DIAMOND KURANG, AYO PENCET RED BUTTON") # debug
            else:
                # Ke diamond dengan density tertinggi
                print("AMBIL DIAMOND!!!") # debug
                self.goal_position = highest_density_position

        if (self.goal_position == None):
            # jika tidak ada goal position, ke base
            self.goal_position = base_position
            print("KE BASE AJA LAH, CAPEK") # debug
        
        
        # Jika ada goal position, cek apakah teleporter perlu digunakan
        self.goal_position = self.teleport(bot_position, board, self.goal_position)
        delta_x, delta_y = get_direction(
            bot_position.x,
            bot_position.y,
            self.goal_position.x,
            self.goal_position.y,
        )

        # Handling invalid move
        i = 0
        while (not board.is_valid_move(bot_position, delta_x, delta_y)):
            # Jika gerakan tidak valid, random gerakan lain
            delta_x = self.directions[i][0]
            delta_y = self.directions[i][1]
            i += 1
            print("RANDOM MOVE") # debug

        return delta_x, delta_y