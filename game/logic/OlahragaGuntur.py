from game.logic.base import BaseLogic
from game.models import Board, GameObject, Position, Properties
from typing import Tuple
from ..util import get_direction
import sys


class greedyGanteng(BaseLogic):
    def __init__(self) -> None:
        self.current_position: Position = None

    def isInventoryFull(self, board_bot: GameObject) -> bool:
        # Check if the players inventory full
        return board_bot.properties.inventory_size == board_bot.properties.diamonds

    def getLength(self, pos1: Position) -> float:
        # Return the length from current position to pos1
        deltaX = abs(pos1.x - self.current_position.x)
        deltaY = abs(pos1.y - self.current_position.y)
        return deltaX + deltaY

    def go_to_base(self, board_bot: GameObject, board: Board) -> Tuple[int, int]:
        # Mencari posisi dari base
        base = board_bot.properties.base
        self.goal_position = base

        # Fungsi Solusi
        # mengembalikan langkah selanjutnya yang harus ditempuh oleh bot
        delta_x, delta_y = get_direction(
            self.current_position.x,
            self.current_position.y,
            self.goal_position.x,
            self.goal_position.y,
        )
        return delta_x, delta_y


class OlahragaGunturLogic(greedyGanteng):
    def getPricePerLength(self, position: Position, gana: Properties) -> float:
        length = self.getLength(position)
        if (gana.points):
            return gana.points / length
        else:
            return sys.float_info.max

    def go_to_diamond(self) -> Tuple[int, int]:
        # Himpunan Kandidat dengan Fungsi Kelayakan
        # Kelayakan dinilai dengan nilai diamond + diamond yang sudah ada <= ukuran inventory
        existing_diamonds = [diamond for diamond in self.current_board.diamonds if
                             diamond.properties.points + self.player_bot.properties.diamonds <= self.player_bot.properties.inventory_size]

        # Fungsi Seleksi
        # memilih nilai maksimum dari seluruh rasio nilai diamond dengan jarak dari seluruh himpunan diamond
        nearest_diamond = max(existing_diamonds, key=lambda x: self.getPricePerLength(x.position, x.properties))

        # Fungsi Solusi
        # mengembalikan langkah selanjutnya yang harus ditempuh oleh bot
        delta_x, delta_y = get_direction(
            self.current_position.x,
            self.current_position.y,
            nearest_diamond.position.x,
            nearest_diamond.position.y
        )

        return delta_x, delta_y

    """
    Fungsi next_move menentukan langkah selanjutnya yang akan ditempuh oleh bot.
    Logika dasar dalam menentukan langkah selanjutnya dari bot ini adalah nilai maximum dari rasio nilai diamond dengan jarak.

    @param board_bot: bot yang digunakan oleh program ini
    @param board: seluruh objek dan attribut yang ada pada permainan
    """

    def next_move(self, board_bot: GameObject, board: Board) -> Tuple[int, int]:
        self.current_position = board_bot.position
        self.player_bot = board_bot
        self.current_board = board

        bx, by = board_bot.properties.base.x, board_bot.properties.base.y
        base_pos = Position(by, bx)

        # If distance to home is super close and diamonds > 0, go home immedieately
        if self.player_bot.properties.diamonds > 1 and self.getLength(base_pos) < 2:
            return self.go_to_base(board_bot, board)
        elif self.player_bot.properties.diamonds > 0 and self.getLength(base_pos) <= 1:
            return self.go_to_base(board_bot, board)

        # If time is 10 seconds or less, diamonds not empty, go home
        time_left = self.player_bot.properties.milliseconds_left // 1000
        if time_left < 10 and self.player_bot.properties.diamonds > 0:
            return self.go_to_base(board_bot, board)

        # If inventory is full, go home
        if self.isInventoryFull(board_bot):
            return self.go_to_base(board_bot, board)
        else:
            return self.go_to_diamond()
