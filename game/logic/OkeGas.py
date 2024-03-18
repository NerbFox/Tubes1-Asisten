import random
from typing import Optional

from game.logic.base import BaseLogic
from game.models import Board, GameObject, Position

from ..util import get_direction


class Greedy2Logic(BaseLogic):
    def __init__(self):
        self.directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        self.goal_position: Optional[Position] = None
        self.current_direction = 0
        self.button = None

    def next_move(self, board_bot: GameObject, board: Board):
        props = board_bot.properties
        current_position = board_bot.position
        base = board_bot.properties.base

        # Cari diamond berdasarkan density
        self.findByDensityDiamond(board_bot, board)

        # Gunakan button atau nggak
        self.useButtonOrNot(board_bot, board)

        # Jika inventory sudah full kembali ke base
        if props.diamonds == 5:
            self.goal_position = base

        # Jika inventory sudah terisi >= 3 putuskan kembali ke base atau lanjut mengambil diamond
        elif props.diamonds >= 3:
            self.cekBaseOrDir(board_bot, board)

        # Jika waktu yang tersisa dikurangi waktu posisi sekarang ke base < 2.5 detik, bot kembali ke base
        distBase = abs(board_bot.properties.base.x - current_position.x) + abs(
            board_bot.properties.base.y - current_position.y
        )
        if((props.milliseconds_left - distBase*1000)<2500 and distBase !=0):
            self.goal_position = base

        # print(props.milliseconds_left)
        if self.goal_position:
            delta_x, delta_y = get_direction(
                current_position.x,
                current_position.y,
                self.goal_position.x,
                self.goal_position.y,
            )
        else:
            # Move to base
            base = board_bot.properties.base
            self.goal_position = base
        return delta_x, delta_y

    # Fungsi untuk mencari langkah berdasarkan point/jarak
    def findByDensityDiamond(self, board_bot: GameObject, board: Board):
        current_position = board_bot.position
        props = board_bot.properties
        minDen = -1
        goal = current_position
        # Iterasi seluruh game object
        for i in board.game_objects:
            # Tentukan jarak dengan objek
            dist = abs(i.position.x - current_position.x) + abs(
                i.position.y - current_position.y
            )
            # Jika ditemukan diamond cek apakah diamond merupakan diamond yang memiliki point/jarak terdekat
            if i.type == "DiamondGameObject" and dist != 0:
                tmp = i.properties.points / dist
                if tmp != 0:
                    if props.diamonds == 4:
                        if i.properties.points == 1:
                            if minDen == -1:
                                minDen = tmp
                                goal = i.position
                            elif tmp > minDen:
                                minDen = tmp
                                goal = i.position
                    else:
                        if minDen == -1:
                            minDen = tmp
                            goal = i.position
                        elif tmp > minDen:
                            minDen = tmp
                            goal = i.position

            # Jika ketemu diamond button simpan di self.button
            if i.type == "DiamondButtonGameObject":
                self.button = i
        self.goal_position = goal

    # Fungsi untuk menentukan langkah kembali ke base atau melanjutkan mengambil diamond
    # Jika Jarak ke base lebih dekat dibanding jarak ke diamond maka kembali kebase
    # Sebaliknya jika lebih dekat jarak ke diamond
    def cekBaseOrDir(self, board_bot: GameObject, board: Board):
        current_position = board_bot.position

        distBase = abs(board_bot.properties.base.x - current_position.x) + abs(
            board_bot.properties.base.y - current_position.y
        )

        distNow = abs(self.goal_position.x - current_position.x) + abs(
            self.goal_position.y - current_position.y
        )

        if distBase != 0 and distNow != 0:
            if distBase < distNow:
                self.goal_position = board_bot.properties.base

    # Fungsi untuk menentukan menggunakan button atau tidak
    # Jika Jarak ke button lebih dekat dibanding jarak ke diamond maka gunakan button
    # Sebaliknya jika lebih dekat jarak ke diamond
    def useButtonOrNot(self, board_bot: GameObject, board: Board):
        current_position = board_bot.position

        distButton = abs(self.button.position.x - current_position.x) + abs(
            self.button.position.y - current_position.y
        )

        distNow = abs(self.goal_position.x - current_position.x) + abs(
            self.goal_position.y - current_position.y
        )

        if distButton < distNow:
            self.goal_position = self.button.position
