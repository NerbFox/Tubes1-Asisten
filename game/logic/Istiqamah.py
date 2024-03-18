import random
from typing import Optional

from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from ..util import get_direction


class Istiqamah(BaseLogic):
    # Inisialisasi
    def __init__(self):
        self.directions = [
            (1, 0),
            (0, 1),
            (-1, 0),
            (0, -1),
        ]  # pergerakan bot ke arah kanan, atas, kiri, bawah
        self.goal_position: Optional[Position] = None  # posisi tujuan bot
        self.teleport: Optional[Position] = None  # posisi teleport
        self.isTeleport = False  # status teleport , bot masuk atau tidak
        self.current_direction = 0  # arah pergerakan bot sekarang
        self.idTeleport = -1  # id teleport
        self.isDiamond = 0  # status diamond yang telah diambil
        self.previous_goal: Optional[Position] = None  # posisi tujuan sebelumnya

    # Fungsi untuk menghitung jarak antara dua titik
    def pytagoras(self, x1, y1, x2, y2):
        return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5

    # Fungsi untuk menghitung jumlah langkah yang diperlukan untuk mencapai tujuan
    def countSteps(self, goal: Position, current: Position):
        return abs(goal.x - current.x) + abs(goal.y - current.y)

    # Fungsi untuk menghitung jumlah diamond di sekitar suatu titik
    def count(self, board: Board, center, rad):
        count = 0
        for game_object in board.game_objects:
            # mendeteksi diamond di sekitar suatu titik
            if game_object.type == "DiamondGameObject":
                if self.countSteps(game_object.position, center) <= rad:
                    count += 1
                    if count >= 4:
                        break
        return count

    # Fungsi untuk mencari diamond terdekat
    def Diamond(self, board_bot: GameObject, board: Board):
        props = board_bot.properties
        current_position = board_bot.position  # posisi bot sekarang
        jarak = 0  # inisialisasi jarak antara bot dengan diamond terdekat
        x = -1  # inisialisasi koordinat x diamond terdekat
        y = -1  # inisialisasi koordinat y diamond terdekat
        for objek in board.game_objects:  # iterasi semua objek di board
            if objek.type == "DiamondGameObject":  # jika objek adalah diamond
                cek = False
                for k in range(len(board.diamonds)):  # iterasi semua diamond di board
                    if (
                        board.diamonds[k].position.x == objek.position.x
                        and board.diamonds[k].position.y == objek.position.y
                        and board.diamonds[k].properties.points + props.diamonds > 5
                    ):
                        # jumlah diamond bot = 4 dan terdekat ternyata diamond merah yang 2 poin maka akan di skip
                        cek = True
                if cek:
                    continue  # skip diamond merah jika akan melebihi 5 poin
                if (
                    jarak == 0
                ):  # jika jarak masih 0 maka diinisialisasi dengan diamond yang pertama ditemukan
                    jarak = self.pytagoras(
                        current_position.x,
                        current_position.y,
                        objek.position.x,
                        objek.position.y,
                    )
                    x = objek.position.x
                    y = objek.position.y
                else:  # jika jarak tidak 0 maka akan di cek apakah jarak dengan diamond yang ditemukan lebih kecil dari jarak sebelumnya
                    if jarak > self.pytagoras(
                        current_position.x,
                        current_position.y,
                        objek.position.x,
                        objek.position.y,
                    ):
                        # jika ya maka jarak diupdate dengan jarak yang lebih kecil
                        jarak = self.pytagoras(
                            current_position.x,
                            current_position.y,
                            objek.position.x,
                            objek.position.y,
                        )
                        x = objek.position.x
                        y = objek.position.y
        # mengembalikan koordinat diamond terdekat
        return (y, x)

    # Fungsi untuk mencari diamond atau teleport terdekat
    def NewCheckSekitar(self, board_bot: GameObject, board: Board):
        props = board_bot.properties  # inisialisasi properties bot
        current_position = board_bot.position  # inisialisasi posisi bot sekarang
        jarak = 0  # inisialisasi jarak antara bot dengan diamond atau teleport terdekat
        x = -1  # inisialisasi koordinat x diamond atau teleport terdekat
        y = -1  # inisialisasi koordinat y diamond atau teleport terdekat
        for objek in board.game_objects:  # iterasi semua objek di board
            if (
                objek.type == "DiamondGameObject" or objek.type == "TeleportGameObject"
            ):  # jika objek adalah diamond atau teleport
                cek = False
                if objek.type == "TeleportGameObject":  # jika objek adalah teleport
                    for tele in board.game_objects:  # iterasi semua objek di board
                        if (
                            tele.type == "TeleportGameObject" and tele.id != objek.id
                        ):  # jika objek adalah teleport dan id teleport tidak sama dengan id teleport sekarang
                            if (
                                self.count(board, tele.position, 6) < 3
                            ):  # jika jumlah diamond di sekitar teleport kurang dari 4 maka akan di skip
                                continue
                            else:
                                self.teleportid = tele.id

                elif objek.type == "DiamondGameObject":  # jika objek adalah diamond
                    for k in range(
                        len(board.diamonds)
                    ):  # iterasi semua diamond di board
                        if (
                            board.diamonds[k].position.x == objek.position.x
                            and board.diamonds[k].position.y == objek.position.y
                            and board.diamonds[k].properties.points + props.diamonds > 5
                        ):
                            cek = True  # jumlah diamond bot = 4 dan terdekat ternyata diamond merah yang 2 poin maka akan di skip
                if cek:
                    continue  # skip diamond merah jika akan melebihi 5 poin
                if (
                    jarak == 0
                ):  # jika jarak masih 0 maka diinisialisasi dengan diamond atau teleport yang pertama ditemukan
                    jarak = self.pytagoras(
                        current_position.x,
                        current_position.y,
                        objek.position.x,
                        objek.position.y,
                    )
                    x = objek.position.x
                    y = objek.position.y
                else:  # jika jarak tidak 0 maka akan di cek apakah jarak dengan diamond atau teleport yang ditemukan lebih kecil dari jarak sebelumnya
                    if jarak > self.pytagoras(
                        current_position.x,
                        current_position.y,
                        objek.position.x,
                        objek.position.y,
                    ):
                        # jika ya maka jarak diupdate dengan jarak yang lebih kecil
                        jarak = self.pytagoras(
                            current_position.x,
                            current_position.y,
                            objek.position.x,
                            objek.position.y,
                        )
                        x = objek.position.x
                        y = objek.position.y
        # mengembalikan koordinat diamond atau teleport terdekat
        return (y, x)

    def isObjectTeleport(self, board: Board, x, y):
        # Fungsi untuk mengecek apakah di koordinat x, y ada teleport
        for game_object in board.game_objects:
            if (
                game_object.position.x == x
                and game_object.position.y == y
                and game_object.type == "TeleportGameObject"
            ):
                return True
        return False

    def isTaken(self, board: Board, x, y):
        # Fungsi untuk mengecek apakah di koordinat x, y objek diamond masih ada atau sudah diambil
        for game_object in board.game_objects:
            if (
                game_object.position.x == x
                and game_object.position.y == y
                and game_object.type != "DiamondGameObject"
            ):
                return True
        return False

    def isTeleportReset(self, board: Board, Goal: Position, Id: int):
        # Fungsi untuk mengecek apakah teleport sudah di reset atau belum
        for objek in board.game_objects:
            if objek.type == "TeleportGameObject" and objek.id == Id:
                if objek.position.x != Goal.x and objek.position.y != Goal.y:
                    return True
                else:
                    return False

    def next_move(self, board_bot: GameObject, board: Board):
        # Fungsi untuk menghitung langkah selanjutnya yang akan diambil oleh bot
        print("Goal Position: ", self.goal_position)
        props = board_bot.properties
        current_position = board_bot.position  # inisialisasi posisi bot sekarang
        sessionlegth = props.milliseconds_left  # inisialisasi sisa waktu
        base_x = board_bot.properties.base.x  # inisialisasi koordinat x base
        base_y = board_bot.properties.base.y  # inisialisasi koordinat y base

        if (
            self.isTeleport
        ):  # jika bot diarahkan melalui teleport agar lebih dekat menuju base
            print("Teleporting to: ", self.teleport)
            delta_x, delta_y = get_direction(
                current_position.x, current_position.y, self.teleport.x, self.teleport.y
            )  # menghitung langkah yang diperlukan untuk menuju teleport
            if (
                current_position.x + delta_x == self.teleport.x
                and current_position.y + delta_y == self.teleport.y
            ):
                # jika bot sudah berada di teleport maka status teleport di reset
                self.isTeleport = False
                self.teleport = None
                self.idTeleport = -1
                self.goal_position = None
            elif self.isTeleportReset(board, self.teleport, self.idTeleport):
                # jika teleport sudah di reset maka status teleport di reset
                self.isTeleport = False
                self.teleport = None
                self.idTeleport = -1
                self.goal_position = None
            # mengembalikan langkah yang diperlukan untuk menuju teleport
            return delta_x, delta_y

        if self.goal_position == Position(
            base_y, base_x
        ):  # jika tujuan bot adalah base
            print("Moving to base")
            if (
                self.goal_position.x == board_bot.position.x
                and self.goal_position.y == board_bot.position.y
            ):
                # jika bot sudah berada di base maka tujuan bot di reset
                self.goal_position = None

            else:
                # cek apakah ada teleport yang akan mempercepat bot menuju base
                temp = False
                for tele1 in board.game_objects:
                    if tele1.type == "TeleportGameObject":
                        for tele2 in board.game_objects:
                            if (
                                tele2.type == "TeleportGameObject"
                                and tele2.id != tele1.id
                            ):
                                if self.countSteps(
                                    current_position, tele1.position
                                ) + self.countSteps(
                                    tele2.position, Position(base_y, base_x)
                                ) < self.countSteps(
                                    current_position, Position(base_y, base_x)
                                ):
                                    # jika ada teleport yang mempercepat bot menuju base maka bot diarahkan menuju teleport
                                    # status teleport di set menjadi true
                                    # id teleport di set menjadi id teleport yang diarahkan
                                    # tujuan bot di set menjadi teleport yang diarahkan
                                    self.teleport = Position(
                                        tele1.position.y, tele1.position.x
                                    )
                                    self.isTeleport = True
                                    self.idTeleport = tele1.id
                                    temp = True
                                    break
                        if temp:
                            break

        elif self.goal_position != None and self.goal_position != Position(
            base_y, base_x
        ):
            # jika tujuan bot bukan base
            if (
                self.goal_position.x == board_bot.position.x
                and self.goal_position.y == board_bot.position.y
            ):
                # jika bot sudah berada di tujuan maka tujuan bot di reset
                self.goal_position = None
            elif self.isTaken(board, self.goal_position.x, self.goal_position.y):
                # jika tujuan bot sudah diambil maka tujuan bot di reset
                self.goal_position = None

        if sessionlegth < 10000 and props.diamonds > 2:
            # jika sisa waktu kurang dari 10 detik dan jumlah diamond bot lebih dari 2
            # maka bot diarahkan menuju base
            self.goal_position = Position(base_y, base_x)

        if self.goal_position == None:
            if props.diamonds == 5:
                # jika jumlah diamond bot = 5
                # maka bot diarahkan menuju base
                self.goal_position = Position(base_y, base_x)

            else:
                # mencari objek selain diamond jika telah mengambil diamond lebih dari 2
                if self.isDiamond == 2:
                    check = self.NewCheckSekitar(
                        board_bot, board
                    )  # mencari diamond atau teleport terdekat
                    if self.isObjectTeleport(
                        board, check[1], check[0]
                    ):  # jika objek terdekat adalah teleport
                        self.isDiamond = False
                        self.isTeleport = True
                        self.teleport = Position(
                            check[0], check[1]
                        )  # tujuan bot di set menjadi teleport terdekat
                        self.isDiamond = 0  # status diamond di reset
                else:
                    check = self.Diamond(board_bot, board)
                    self.isDiamond += 1  # bot telah mengambil 1 diamond

                if props.diamonds >= 3:
                    # jika jumlah diamond bot lebih dari 3
                    if self.countSteps(
                        current_position, Position(check[0], check[1])
                    ) <= self.countSteps(current_position, board_bot.properties.base):
                        # jika jarak antara bot dengan diamond terdekat lebih kecil dari jarak antara bot dengan base
                        self.goal_position = Position(check[0], check[1])
                        return get_direction(
                            current_position.x,
                            current_position.y,
                            self.goal_position.x,
                            self.goal_position.y,
                        )
                    else:
                        # jika jarak antara bot dengan diamond terdekat lebih besar dari jarak antara bot dengan base
                        self.goal_position = Position(base_y, base_x)
                        self.previous_goal = Position(base_y, base_x)
                        return get_direction(
                            current_position.x,
                            current_position.y,
                            self.goal_position.x,
                            self.goal_position.y,
                        )
                elif check[0] != -1:
                    # jika diamond terdekat ditemukan
                    self.goal_position = Position(check[0], check[1])
                    self.previous_goal = Position(check[0], check[1])
                    return get_direction(
                        current_position.x,
                        current_position.y,
                        self.goal_position.x,
                        self.goal_position.y,
                    )

        if self.goal_position.x == -1 and self.goal_position.y == -1:
            # jika tujuan bot tidak ditemukan
            # maka bot diarahkan menuju red button
            for red in board.game_objects:
                if red.type == "DiamondButtonGameObject":
                    self.goal_position = Position(red.position.y, red.position.x)
                    break
        return get_direction(
            current_position.x,
            current_position.y,
            self.goal_position.x,
            self.goal_position.y,
        )  # mengembalikan langkah yang diperlukan untuk menuju tujuan bot
