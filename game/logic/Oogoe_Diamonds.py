import random
from typing import Optional

from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from ..util import get_direction

# test bot
# python main.py --logic ratio --email=ratio@email.com --name=ratio --password=123456 --team etimo

class Greedy_by_Ratio(BaseLogic):
# Algoritma Greedy yang memilih diamond berdasarkan rasio (jarak : point)
# Bot akan memilih diamond yang memiliki rasio (jarak : point) terkecil

    def __init__(self):
        self.directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        self.goal_position: Optional[Position] = None
        self.current_direction = 0

    def next_move(self, board_bot: GameObject, board: Board):
        # Menentukan arah gerak bot selanjutnya
        # Mencari diamond dengan rasio (jarak : point) terkecil
        self.goal_position : Position = search_diamond_with_minimum_ratio(board_bot, board)       
        # Mendapatkan Properti Bot
        props = board_bot.properties

        ################################ MENENTUKAN KONDISI BOT SAAT INI ################################
        if props.diamonds == 5:
            # Jika inventory sudah penuh, bergerak ke base
            base = board_bot.properties.base
            self.goal_position = base
        elif props.diamonds >= 3 and props.milliseconds_left < 12000 :
            # 12 detik terakhir, harus kembali ke base (jika sudah memiliki 3 atau lebih diamond)
            self.goal_position = board_bot.properties.base
        
        ################################ MENENTUKAN DELTA_X DAN DELTA_Y ################################
        current_position = board_bot.position
        if self.goal_position:
            # Bergerak ko objek yang spesifik, hitung delta
            delta_x, delta_y = get_direction(
                current_position.x,
                current_position.y,
                self.goal_position.x,
                self.goal_position.y,
            )
        else:
            # Bergerak ke sekitar
            delta = self.directions[self.current_direction]
            delta_x = delta[0]
            delta_y = delta[1]
            if random.random() > 0.6:
                self.current_direction = (self.current_direction + 1) % len(
                    self.directions
                )
        
        # Menghindari invalid move
        if (delta_x == 0 and delta_y == 0):
            delta_y = 1
        elif (delta_x == 1 and delta_y == 1):
            delta_y = 0
        elif (delta_x == -1 and delta_y == -1):
            delta_y = 0

        return delta_x, delta_y

def search_diamond_with_minimum_ratio(board_bot: GameObject, board: Board) -> Position:
# Mengembalikan posisi diamond yang memiliki rasio (jarak : point) terkecil jika ada
# Mengembalikan posisi diamond button jika tidak ada diamond yang tersedia
    Object_Position = Position
    min_ratio = 9999

    # Memilih untuk mendekati tombol reset terlebih dahulu
    diamond_button: Position = get_diamond_button_position(board)
    delta_x = abs(board_bot.position.x - diamond_button.x)
    delta_y = abs(board_bot.position.y - diamond_button.y)
    ratio_diamond = (delta_x + delta_y) / 0.8               # Rasio (jarak : point) untuk diamond button
    if ratio_diamond < min_ratio:
        Object_Position = diamond_button
        min_ratio = ratio_diamond

    # Mencari diamond yang memiliki rasio (jarak : point) terkecil
    for i in range(len(board.diamonds)):
        delta_x = abs(board_bot.position.x - board.diamonds[i].position.x)
        delta_y = abs(board_bot.position.y - board.diamonds[i].position.y)
        jumlah_langkah = delta_x + delta_y
        ratio_diamond = jumlah_langkah / board.diamonds[i].properties.points
        
        # Menghindari bertabrakan dengan musuh (main aman aja)
        langkah_musuh = the_closest_enemy_to_the_diamond(board, board.diamonds[i].position)
        if ratio_diamond < min_ratio and jumlah_langkah <= langkah_musuh :
            if not (board.diamonds[i].properties.points == 2 and board_bot.properties.diamonds == 4) : 
                min_ratio = ratio_diamond
                Object_Position = board.diamonds[i].position
    
    return Object_Position

def get_diamond_button_position(board: Board) -> Position :
# Mengembalikan posisi diamond button
    for i in range (len(board.game_objects)) :
        if(board.game_objects[i].type == 'DiamondButtonGameObject'):
            return board.game_objects[i].position

def the_closest_enemy_to_the_diamond(board:Board, diamondposition: Position) -> int :
# Mengembalikan jarak musuh terdekat ke diamond yang kita tuju
    step_musuh = 9999
    for i in range(len(board.bots)) :
        x = abs(board.bots[i].position.x - diamondposition.x)
        y = abs(board.bots[i].position.y - diamondposition.y)
        if step_musuh > (x+y) :
            step_musuh = x+y
    return step_musuh