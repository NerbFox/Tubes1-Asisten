from typing import Optional
import random
from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from ..util import get_direction

# Fungsi untuk menghitung jarak satu objek dengan objek lainnya
def distance(A: Position, B: Position):
    return abs(A.x-B.x) + abs(A.y-B.y)

# Fungsi untuk menghitung jarak satu objek dengan objek lainnya menggunakan teleporter
def distanceWithTeleporter(near_teleporter: int, Destination: Position, far_teleporter:Position):
    return near_teleporter + distance(Destination, far_teleporter)

# Fungsi untuk kembali ke base (return delta_x dan delta_y ke base)
def goToBase(distance: int, distance_with_tele: int, base: Position, teleporter: Position, current_position: Position):
    if distance <= distance_with_tele: # Lebih dekat ke base tanpa teleporter
        delta_x, delta_y =  get_direction(
            current_position.x,
            current_position.y,
            base.x,
            base.y,
        )
    else: # Lebih dekat ke base dengan teleporter
        delta_x, delta_y = get_direction(
            current_position.x,
            current_position.y,
            teleporter.x,
            teleporter.y,
        )
    
    # jika gerakan sumbu x dan sumbu y sama (Mencegah error akibat bug)
    if delta_x == delta_y:
        delta_x = 0
        delta_y = pow(-1, random.randint(0, 1))
    
    # return hasil
    return delta_x, delta_y

# Fungsi Algoritma diamond (Greedy by Distance)
def diamondAlgorithm(diamonds, teleporter, redButton, base, current_position, props, near_teleporter):
    # inisiasi variabel
    min_dist = 1000  # jarak terdekat, inisialisasi angka yang sangat besar.
    goal = base # tujuan, default = base.
    jumlahDiamond = 0   # jumlah diamond
    for diamond in diamonds:
        jumlahDiamond += 1  # jumalh diamond bertambah
        # jumlah diamond sudah empat dan ada red diamond, akan diskip
        if not (diamond.properties.points == 2 and props.diamonds >= 4):
            # jarak ke diamond
            dist = distance(current_position, diamond.position) # direct
            dist_with_tele = distanceWithTeleporter(near_teleporter, diamond.position, teleporter[1].position) # Jarak menggunakan teleport
            # menentukan jarak terdekat
            if (dist < min_dist):
                if dist <= dist_with_tele:
                    goal = diamond.position
                    min_dist = dist
                else:
                    goal = teleporter[0].position
                    min_dist = dist_with_tele
            elif (dist_with_tele < min_dist):
                goal = teleporter[0].position
                min_dist = dist_with_tele
    
    # Menentukan posisi dan jarak red button
    positionRedButton = redButton.position  # Memberikan posisi red button
    distRedButton = distance(current_position, positionRedButton)  # Jarak ke red button
    distRedButtonTeleport = distanceWithTeleporter(near_teleporter, positionRedButton, teleporter[1].position)

    # Menentukan jarak terdekat ke red button apakah direct atau menggunakan teleport
    if distRedButtonTeleport <= distRedButton:
        positionRedButton = teleporter[1].position
        distRedButton = distRedButtonTeleport

    # jika diamond tinggal sedikit dan jarak ke red diamond lebih dekat, akan ke red diamond
    if(jumlahDiamond <= 6 and distRedButton <= min_dist):
        goal = positionRedButton

    # menentukan arah gerak bot
    delta_x, delta_y = get_direction(
        current_position.x,
        current_position.y,
        goal.x,
        goal.y,
    )
    
    # jika gerakan sumbu x dan sumbu y sama (Mencegah error akibat bug)
    if delta_x == delta_y:
        delta_x = 0
        delta_y = pow(-1, random.randint(0, 1))
    
    # return hasil
    return delta_x, delta_y

class WadasLogic(BaseLogic):
    # inisiasi
    def __init__(self):
        # inisiasi objek tujuan
        self.goal_position: Optional[Position] = None

    # menentukan langkah selanjutnya
    def next_move(self, board_bot: GameObject, board: Board):
        props = board_bot.properties    # Properti dari bot
        current_position = board_bot.position   # Posisi bot saat ini
        base = board_bot.properties.base    # Posisi base bot
        diamonds = []
        bots = []
        teleporter = []

        # Menengambil Setiap Objek yang digunakan
        for object in board.game_objects:
            if object.type == "DiamondGameObject":
                diamonds.append(object)
            elif object.type == "BotGameObject":
                bots.append(object)
            elif object.type == "TeleportGameObject":
                teleporter.append(object)
            elif object.type == "DiamondButtonGameObject":
                redButton = object

        # Menentukan posisi teleporter dan jarak tiap teleporter
        teleporter_distance = [distance(d.position, current_position) for d in teleporter]    # jarak tiap teleporter
        # Menentukan teleporter terdekat, assign di index 0.
        if (teleporter_distance[0] > teleporter_distance[1]):
            near_teleporter = teleporter_distance[1]
            temp = teleporter[0]
            teleporter[0] = teleporter[1]
            teleporter[1] = temp
        else:
            near_teleporter = teleporter_distance[0]
        
        # Jarak ke base
        dist_base = distance(current_position, base)
        dist_base_teleport = distanceWithTeleporter(near_teleporter, base, teleporter[1].position)

        # Memeriksa jumlah diamond yang dibawa dan waktu yang tersisi
        # jika waktu kurang dari 10 detik, dan masih membawa diamond, kembali ke base
        if (props.diamonds > 0 and board_bot.properties.milliseconds_left < 10000):
            # Kembali ke base
            return goToBase(dist_base, dist_base_teleport, base, teleporter[0].position, current_position)

        # Algoritma Greedy by Tackle
        # mencari bot lawan
        for bot in bots:
            # memnentukan kapan akan membunuh bot
            # syarat:
            # jika jarak ke bot = 1 atau (< 3 dan musuh memiliki diamond > 2), bunuh bot lawan
            if bot.properties.name != board_bot.properties.name and ((distance(current_position, bot.position) < 3 and bot.properties.diamonds > 2) or distance(current_position, bot.position) == 1) :
                # Bergerak ke arah bot
                return get_direction(current_position.x, current_position.y, bot.position.x, bot.position.y)

        # jika inventory penuh atau jarak ke base dekat dan diamond > 2, ke base
        if props.diamonds == 5 or (props.diamonds > 2 and dist_base < 2):
            # Kembali ke base
            return goToBase(dist_base, dist_base_teleport, base, teleporter[0].position, current_position)

        else:   # Greedy by Distance
            return diamondAlgorithm(diamonds, teleporter, redButton, base, current_position, props, near_teleporter)