from typing import Optional
from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from ..util import get_direction, position_equals


def coordinate_diamond_ratio(coordinates, points, current_position):
    # IS: list koordinat dari kumpulan objek diamond, list poin dari kumpulan objek diamond, posisi inisial yang diinginkan terdefinisi
    # FS: akan menghasilkan list of list koordinat dan points, juga ratio dari setiap objek diamond yang didapat dari poin/jarak (jika jarak = 0 maka akan diassign -1)

    sum_coordinates = [((coordinate.x - current_position.x) ** 2 + (coordinate.y - current_position.y) ** 2) for
                       coordinate in coordinates]
    ratio = []

    for i in range(len(sum_coordinates)):
        if (sum_coordinates[i] == 0):
            ratio.append(-1)
        else:
            ratio.append(points[i] / sum_coordinates[i])

    return [coordinates, points], ratio


def get_coordinate_goal_for_diamond(list_ratio, list_coordinates, inventory_diamonds, list_point):
    # IS: list ratio diamond, list koordinat, jumlah diamond yang dibawa, dan list point terdefinisi
    # FS: akan menghasilkan koordinat dari diamond yang diinginkan

    # cari index dari nilai max list ratio
    max_ratio = max(list_ratio)
    index = list_ratio.index(max_ratio)

    # mengabaikan diamond berpoin 2 jika diamond yang dibawa adalah 4
    while (list_point[index] == 2 and inventory_diamonds == 4):
        list_ratio[index] = -1
        max_ratio = max(list_ratio)
        index = list_ratio.index(max_ratio)

    if (list_ratio[index] == -1):  # abaikan diamond merah
        return list_coordinates[index], True

    if (inventory_diamonds == 4):
        if (list_point[index] == 2):
            index -= 1

    return list_coordinates[index], False


def red_button(red_pos, curr_pos, diamond_ratio, n_diamond_left):
    # IS: posisi red button, rasio diamond, jumlah diamond tersisa dalam board terdefinisi
    # FS : akan menghasilkan true jika poin (perhitungan modifikasi sendiri untuk mencari poin) lebih dari nilai tertinggi dari rasio diamond, dan menghasilkan false untuk kondisi sebaliknya
    distance = ((red_pos.x - curr_pos.x) ** 2 + (red_pos.y - curr_pos.y) ** 2)
    poin = (2 / (distance * n_diamond_left))
    if (poin > max(diamond_ratio)):
        return True
    else:
        return False


def teleport_use(diamond_pos, diamond_ratio, teleport2_pos, points):
    # IS: posisi diamond, rasio diamond, posisi teleport sebrang (teleport terjauh dari posisi bot), points dari setiap diamond terdefinisi.
    #       Tujuan bot untuk cari diamond, lalu bertemu teleport terdekat dalam radius yang sudah ditentukan
    # FS: proses akan mengecek diamond terdekat ada di posisi saat ini atau di teleport terjauh, dengan cara membandingkan nilai rasionya.
    #       Fungsi ini akan menghasilkan true jika ratio teleport lebih besar dari ratio diamond dari current position
    _, ratio_teleport = coordinate_diamond_ratio(diamond_pos, points, teleport2_pos)
    if (max(ratio_teleport) > max(diamond_ratio)):
        return True
    else:
        return False


def teleport_use_base(curr_pos, tel2_pos, base):
    # IS: posisi saat ini, posisi teleport sebrang (teleport terjauh dari posisi bot), posisi base.
    #       Tujuan bot ke base, lalu bertemu teleport terdekat dalam radius yang sudah ditentukan
    # FS: proses akan mengecek jarak terdekat untuk pulang ke base ini memrlukan teleport atau tidak.
    #       Fungsi ini akan menghasilkan true jika jarak terdekat ditempuh menggunakan teleport, false jika sebaliknya
    if ((base.x - tel2_pos.x) ** 2 + (base.y - tel2_pos.y) ** 2 > (base.x - curr_pos.x) ** 2 + (
            base.y - curr_pos.y) ** 2):
        return True
    else:
        return False


def avoid_teleport(goal_position, current_position, delta_x):
    # IS: posisi dari goal, posisi saat ini, gerakan horizontal terdefinisi. saat ingin menuju ke tujuan lalu bertemu teleport, tapi tidak ingin melewatinya
    # FS: Akan menghasilkan delta_x dan delta_y baru untuk menghindari teleport
    # (0,0) itu kotak paling kiri atas
    if (delta_x == 0):  # pergerakan vertikal
        # berarti bisa digeser kanan atau kiri, tergantung posisi relatif goal terhadap tujuan
        selisih_x = goal_position.x - current_position.x  # kalo positif artinya goal ada di sebelah kanan, kita geser ke kanan aja. kalaupun selisihnya nol, kita bebas mau ambil kanan atau kiri
        if (selisih_x >= 0 and current_position.x != 14):
            return 1, 0
        else:
            return -1, 0
    else:  # artinya delta_x bergerak ke kanan atau ke kiri, yang mana nilai delta_y pasti 0
        # berarti bisa digeser atas atau bawah, tergantung posisi relatif goal terhadap tujuan
        selisih_y = goal_position.y - current_position.y  # kalo positif artinya goal ada di sebelah bawah, kita geser ke bawah aja. kalaupun selisihnya nol, kita bebas mau ambil atas atau bawah
        if (selisih_y >= 0) and current_position.y != 14:
            return 0, 1
        else:
            return 0, -1


def get_dir(current_position, dest):
    # IS: posisi saat ini dan posisi tujuan terdefinisi
    # FS: akan menghasilkan langkah yang dilakukan untuk mencapai tujuan. fungsi ini adalah fungsi buatan untuk memudahkan kontrol ketika menghindari teleport
    gap_x = dest.x - current_position.x
    gap_y = dest.y - current_position.y

    if abs(gap_x) >= abs(gap_y):  # gerak sumbu x
        return (1 if gap_x >= 0 else -1, 0)
    else:  # gerak sumbu y
        return (0, 1 if gap_y >= 0 else -1)


class SambutRamadhanLogic(BaseLogic):
    def __init__(self):
        # inisiasi attribut kelas
        self.directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        self.goal_position: Optional[Position] = None
        self.current_direction = 0
        self.avoid = False
        self.teleport = False

    def next_move(self, board_bot: GameObject, board: Board):
        # proses tackle:
        current_position = board_bot.position
        if (board_bot.properties.diamonds >= 1):
            enemy_location = [(bot.position, bot.properties.name, bot.properties.diamonds) for bot in board.bots if
                              bot.position.x != current_position.x and bot.position.y != current_position.y and (
                                          (bot.position.x - current_position.x) ** 2 + (
                                              bot.position.y - current_position.y) ** 2 < 2)]
        else:
            enemy_location = [(bot.position, bot.properties.name, bot.properties.diamonds) for bot in board.bots if
                              bot.position.x != current_position.x and bot.position.y != current_position.y and (
                                          (bot.position.x - current_position.x) ** 2 + (
                                              bot.position.y - current_position.y) ** 2 < 2) and bot.properties.diamonds >= 2]
        if (len(enemy_location) > 0):
            x, y = get_direction(current_position.x, current_position.y, enemy_location[0][0].x, enemy_location[0][0].y)
            return x, y

        # inisiasi hal hal yang diperlukan
        props = board_bot.properties
        red_pos = [obj.position for obj in board.game_objects if obj.type == "DiamondButtonGameObject"]
        teleport_location = [object.position for object in board.game_objects if object.type == "TeleportGameObject"]
        diamond_pos_in_game = [coordinate.position for coordinate in board.diamonds]
        diamond_point_in_game = [coordinate.properties.points for coordinate in board.diamonds]
        coordinate_and_point, ratio = coordinate_diamond_ratio(diamond_pos_in_game, diamond_point_in_game,
                                                               current_position)
        goal, is_base = get_coordinate_goal_for_diamond(ratio, coordinate_and_point[0], props.diamonds,
                                                        coordinate_and_point[1])

        # Kebijakan red button
        if (red_button(red_pos[0], current_position, ratio, len(diamond_point_in_game))):
            goal = red_pos[0]

        # Kebijakan pulang ke base
        base = board_bot.properties.base
        if props.diamonds >= 5:
            # Move to base
            self.goal_position = base
        else:
            if (
            is_base):  # pulang dengan kasus jika diamond terdekat adalah diamond merah tetapi inventori sudah 4, mending pulang dulu aja
                # Move to base
                self.goal_position = base

            else:
                # Move to goal
                self.goal_position = goal

        # Pemilihan algoritma bergerak menuju posisi tujuan berdasarkan status telah melakukan penghindaran teleport atau belum
        if (self.avoid):
            delta_x, delta_y = get_dir(current_position, self.goal_position)  # menuju path dengan algo zigzag
            self.avoid = False
        else:
            delta_x, delta_y = get_direction(current_position.x, current_position.y, self.goal_position.x,
                                             self.goal_position.y)  # menuju path algo awal

        # Kebijakan terhadap teleport button
        # jika statusnya belum teleport dan diamond di kantong masi kurang dari 4 maka akan masuk pengecekan
        if (self.teleport == False and props.diamonds < 4):
            # mengecek apakah ada teleport terdekat dari posisi bot saat ini
            for tel in teleport_location:
                if ((tel.x - current_position.x) ** 2 + (tel.y - current_position.y) ** 2 < 2):
                    if (self.goal_position != base):
                        # Jika ada dan tujuannya bukan pulang, maka cek apakah perlu ngambil diamondnya pake teleport atau ngga
                        if (teleport_use(diamond_pos_in_game, ratio, (
                        teleport_location[0] if position_equals(teleport_location[1], tel) else teleport_location[1]),
                                         diamond_point_in_game)):
                            # Jika iya maka set status teleport menjadi true agar selanjutnya tidak akan melewati teleport lagi
                            delta_x, delta_y = get_direction(current_position.x, current_position.y, tel.x, tel.y)
                            self.teleport = True

                        else:
                            # Jika tidak akan menggunakan teleport maka lanjut aja
                            if ((delta_x + current_position.x) == tel.x and (delta_y + current_position.y) == tel.y):
                                # tapi jika langkah selanjutnya adalah teleport maka hindari dan set status menghindari teleport menjadi true
                                delta_x, delta_y = avoid_teleport(self.goal_position, current_position, delta_x)
                                self.avoid = True

                    else:
                        # Jika tujuannya adalah pulang maka gunakan pengecekan apakah pulangnya memerlukan teleport atau tidak
                        if (teleport_use_base(current_position, (
                        teleport_location[0] if position_equals(teleport_location[1], tel) else teleport_location[1]),
                                              base)):
                            # Jika iya, maka set status menggunakan teleport menjadi true agar tidak melewati teleport lagi di langkah berikutnya
                            delta_x, delta_y = get_direction(current_position.x, current_position.y, tel.x, tel.y)
                            self.teleport = True
                        else:
                            # Jika tidak akan menggunakan teleport maka lanjut aja
                            if ((delta_x + current_position.x) == tel.x and (delta_y + current_position.y) == tel.y):
                                # tapi jika langkah selanjutnya adalah teleport maka hindari dan set status menghindari teleport menjadi true
                                delta_x, delta_y = avoid_teleport(self.goal_position, current_position, delta_x)
                                self.avoid = True
                    # break agar jika telah menemukan posisi teleport terdekat, kita tidak akan mengecek teleport yang jauhnya
                    break
        else:
            # jika kondisi status menggunakan teleport adalah true atau diamond yang dibawa >=4, maka tidak perlu melakukan pengecekan
            # lalu set status menggunakan teleport menjadi false lagi agar bisa melewati teleport di langkah berikutnya
            self.teleport = False

        return delta_x, delta_y
