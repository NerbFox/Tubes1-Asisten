from typing import Optional
from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from ..util import position_equals


class TipisTipisLogic(BaseLogic):
    def __init__(self):
        self.goal_position: Optional[Position] = None
        self.passPortal = False

    # Fungsi mencari satu step berikutnya
    def next_move(self, board_bot: GameObject, board: Board):
        # Inisialisasi
        props = board_bot.properties
        current = board_bot.position

        # Cari teleport paling dekat
        portal_1, portal_2 = self.sorted_portal(current, board)
        self.passPortal = False

        timeLeft = props.milliseconds_left
        backBase = self.calculate_move(current, props.base) * board.minimum_delay_between_moves * 10
        inventory = props.diamonds

        # Back to base jika diamond sudah 5 atau waktu hampir habis
        if inventory == 5 or ((backBase >= timeLeft - 3000 and backBase < timeLeft)
                              and not position_equals(current, props.base)):
            self.goal_position = None
            toBase = self.calculate_move(current, props.base)

            # Kembali ke base sambil mencari diamond
            if inventory < 5:
                diamond = board.diamonds
                temp = 0
                # Iterasi ke setiap diamond, lalu cari diamond dengan poin/move paling besar
                for d in diamond:
                    point = d.properties.points
                    takeDiamond = self.calculate_move(current, d.position) + self.calculate_move(d.position, props.base)
                    distancePortal = self.calculate_move(current, portal_1) + self.calculate_move(portal_2, d.position) \
                                     + self.calculate_move(d.position, props.base)
                    if inventory == 4 and point == 2:  # Tidak bisa ambil red diamond
                        continue
                    else:  # Masih bisa ambil red diamond
                        denseDiamond = point / takeDiamond
                        densePortal = point / distancePortal
                        if toBase >= takeDiamond:
                            temp = self.destination(denseDiamond, temp, 0, d.position, portal_1)
                        if toBase >= distancePortal:
                            temp = self.destination(0, temp, densePortal, d.position, portal_1)

            # Handle jika tidak ditemukan diamond, langsung pulang ke base
            # Langsung kembali ke base
            if self.goal_position == None:
                portalToBase = self.calculate_move(current, portal_1) + self.calculate_move(portal_2, props.base)
                if (portalToBase < toBase):
                    self.goal_position = portal_1
                    self.passPortal = True
                else:
                    self.goal_position = props.base

        # Mencari diamond (belum pulang ke base)
        else:
            diamond = board.diamonds
            distanceButton = self.calculate_move(current, board.game_objects[2].position)
            temp = 0
            # Inisialisasi red button sebagai goal_position
            if distanceButton > 0:
                temp = (4 / 9) / distanceButton
                self.goal_position = board.game_objects[2].position

            # Iterasi ke setiap diamond, lalu cari diamond dengan poin/move paling besar
            for d in diamond:
                point = d.properties.points
                distanceDiamond = self.calculate_move(current, d.position)
                distancePortal = (self.calculate_move(current, portal_1) + self.calculate_move(portal_2, d.position))
                if inventory <= 3:  # Masih bisa ambil red diamond
                    denseDiamond = point / distanceDiamond
                    densePortal = point / distancePortal
                    temp = self.destination(denseDiamond, temp, densePortal, d.position, portal_1)

                elif (point != 2):  # Tidak bisa ambil red diamond
                    distanceBase = self.calculate_move(d.position, props.base)
                    denseDiamond = point / (distanceDiamond + distanceBase)
                    densePortal = point / (distancePortal + distanceBase)
                    temp = self.destination(denseDiamond, temp, densePortal, d.position, portal_1)

            # Jalan ke goal_position sambil men-store diamond ke base jika efektif
            toBase = self.calculate_move(current, props.base) + self.calculate_move(props.base, self.goal_position)
            distanceDiamond = self.calculate_move(current, self.goal_position)
            if (toBase == distanceDiamond and not position_equals(current, props.base)):
                self.goal_position = props.base

        # cari direction dari destination
        delta_x, delta_y = self.direction(
            current.x, current.y,
            self.goal_position.x, self.goal_position.y
        )

        # Hindari portal
        if self.avoid_portal(board, delta_x + current.x, delta_y + current.y) and not self.passPortal:
            if delta_x != 0:
                delta_x, delta_y = 0, -1 if self.goal_position.y < current.y else 1
            elif delta_y != 0:
                delta_x, delta_y = -1 if self.goal_position.x < current.x else 1, 0

        # Validasi move dan bergerak ke arah sebaliknya jika move tidak valid. Hal ini bisa terjadi ketika ingin menghindari portal
        if (not Board.is_valid_move(board, current, delta_x, delta_y)):
            delta_x *= -1
            delta_y *= -1

        return delta_x, delta_y

    # Mencari destinasi posisi berdasarkan poin per jarak
    def destination(self, denseDiamond, temp, densePortal, diamond: Position, portal: Position):
        if (temp >= denseDiamond) and (temp >= densePortal):
            return temp
        else:
            if (denseDiamond > temp):
                self.goal_position = diamond
                self.passPortal = False
                temp = denseDiamond
            if (densePortal > temp):
                self.goal_position = portal
                self.passPortal = True
                temp = densePortal
            return temp

    # Mengembalikan true jika x dan y adalah posisi portal
    def avoid_portal(self, board: Board, x, y) -> bool:
        # koordinat portal 1
        xPortal_1 = board.game_objects[0].position.x
        yPortal_1 = board.game_objects[0].position.y
        # koordinat portal 2
        xPortal_2 = board.game_objects[1].position.x
        yPortal_2 = board.game_objects[1].position.y

        return (xPortal_1 == x and yPortal_1 == y) or (xPortal_2 == x and yPortal_2 == y)

    # Jarak current ke tiap portal
    def sorted_portal(self, current: Position, board: Board):
        portal_1 = self.calculate_move(current, board.game_objects[0].position)
        portal_2 = self.calculate_move(current, board.game_objects[1].position)
        # cari portal terdekat
        if (portal_1 < portal_2):
            portal_1 = board.game_objects[0].position
            portal_2 = board.game_objects[1].position
        else:
            portal_1 = board.game_objects[1].position
            portal_2 = board.game_objects[0].position

        return (portal_1, portal_2)  # sorted ascending

    # Hitung jarak antara dua titik
    def calculate_move(self, current: Position, other: Position) -> int:
        return abs(current.x - other.x) + abs(current.y - other.y)

    # Cari jalan 1 step ke destination
    def direction(self, current_x, current_y, dest_x, dest_y):
        delta_x = current_x - dest_x
        delta_y = current_y - dest_y
        if abs(delta_x) > abs(delta_y):
            return (1 if delta_x < 0 else -1, 0)
        else:
            return (0, 1 if delta_y < 0 else -1)