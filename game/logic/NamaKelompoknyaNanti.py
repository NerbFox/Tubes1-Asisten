from typing import Optional
from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from ..util import get_direction

# Tenang, komen-komen disini bukan Lobotomy Kaisen lagi
# Anyway, domain expansio-

# Bot ini dibuat berdasarkan solusi greed nearest diamond dengan mempertimbangkan teleporter
class NamaKelompoknyaNanti(BaseLogic) :
    # Constructor bot, jadi botnya diinisiasi dulu
    def __init__(self) :
        self.directions = [(1, 0), (0, 1), (-1, 0), (0, -1)] # Mendefinisikan NORTH, WEST, EAST, dan SOUTH
        self.current_direction = 0 # Sementara NORTH

    # Sebuah fungsi untuk menghitung jarak antar 2 titik
    def distance(self, a: Position, b:Position):
        return abs(a.x - b.x) + abs(a.y - b.y) # Ya ini rumus menghitung jarak
    
    # Sebuah fungsi untuk menghitung komponen mana sih (base, diamond, etc) yang terdekat dengan teleporter
    def nearestWithTele(self, targetPos : Position, botPos : Position, listTeleporters : list[GameObject]):
        TeleA = listTeleporters[0].position
        TeleB = listTeleporters[1].position
        teleState = 0
        nearestDistance = self.distance(botPos, targetPos) 
        # Yang terdekat melalui teleporter A
        if (nearestDistance > (self.distance(botPos, TeleA) + self.distance(TeleB, targetPos))):
            teleState = 1 
            nearestDistance = self.distance(botPos, TeleA) + self.distance(TeleB, targetPos)
        # Yang terdekat melalui teleporter B
        if (nearestDistance > (self.distance(botPos, TeleB) + self.distance(TeleA, targetPos))):
            teleState = 2 
            nearestDistance = self.distance(botPos, TeleB) + self.distance(TeleA, targetPos)
        return nearestDistance, teleState

    # Fungsi mencari diamond terdekat (Yea i mean apalagi)
    def findNearestDiamond(self, listDiamond: list[GameObject], listTeleporters: list[GameObject], bot: GameObject):
        nearestDistance = 0
        rewardnya = 0
        nearestDiamond = Position(0,0)
        teleState = 0
        firstItem = True
        # Untuk setiap posisi diamond, hitung jarak
        for diamond in listDiamond:
            if firstItem: # Sebagai basis
                nearestDistance, teleState = self.nearestWithTele(diamond.position, bot.position, listTeleporters) 
                rewardnya = diamond.properties.points # Reward sebagai pertimbangan, mungkin botnya beneran rakus lebih milih merah meski lebih jauh dikit
                nearestDiamond = diamond.position
            else: # Nah ini baru membandingkan
                tempDistance, tempTeleState = self.nearestWithTele(diamond.position, bot.position, listTeleporters)
                if (tempDistance) < (nearestDistance) or (abs(tempDistance-nearestDistance) <= 2 and diamond.properties.points > rewardnya) :
                    nearestDistance = tempDistance
                    nearestDiamond = diamond.position
                    rewardnya = diamond.properties.points 
                    teleState = tempTeleState
            firstItem = False
        
        return nearestDiamond, teleState, nearestDistance, rewardnya

    # Fungsi mencari diamond terdekat cuma tidak memikirkan rewardnya
    def findNearestDiamondAlt(self, listDiamond: list[GameObject], listTeleporters: list[GameObject], bot: GameObject):
        nearestDistance = 0
        rewardnya = 0
        nearestDiamond = Position(0,0)
        teleState = 0
        firstItem = True
        # Ya kurang lebih sama dengan yang di atas
        for diamond in listDiamond:
            if firstItem:
                nearestDistance, teleState = self.nearestWithTele(diamond.position, bot.position, listTeleporters)
                rewardnya = diamond.properties.points
                nearestDiamond = diamond.position
            else:
                tempDistance, tempTeleState = self.nearestWithTele(diamond.position, bot.position, listTeleporters)
                if (tempDistance) < (nearestDistance):
                    nearestDistance = tempDistance
                    nearestDiamond = diamond.position
                    rewardnya = diamond.properties.points
                    teleState = tempTeleState
            firstItem = False
        
        return nearestDiamond, teleState, nearestDistance, rewardnya

    # Saatnya bot untuk menentukan langkah berikutnya (bisa jadi ambil berkas jadi cakahim HMIF)
    def next_move(self, board_bot: GameObject, board: Board) :        

        props = board_bot.properties
        current_position = board_bot.position
        
        # Woilah cik kok susah dibaca, intinya variable list or something
        listDiamond = board.diamonds
        listTeleporters = [d for d in board.game_objects if d.type == "TeleportGameObject"]
        baseDist, teleState1 = self.nearestWithTele(board_bot.properties.base, board_bot.position, listTeleporters)
        
        # Ini kalau misal diamondnya kurang dari 3 dan ini tu gimana ya njelasinnya, pokoknya punya waktu cukup untuk ngambil diamond
        # sebelum meninggal dan tidak sempat pulang (diamondnya ilang cik)
        if props.diamonds < 3 and not ((baseDist + 1 >= (board_bot.properties.milliseconds_left/1000))):
            # Intinya dapetin goal_position dkk
            self.goal_position, teleState, nearestDist, rewardnya = self.findNearestDiamond(listDiamond, listTeleporters, board_bot)
            # Ini apa ya
            # Intinya berdasarkan teleState, bot ke diamond/teleporter untuk ke diamond, sekaligus validasi move
            if teleState == 1 and self.distance(board_bot.position, listTeleporters[0].position) != 0:
                self.goal_position = listTeleporters[0].position
                print(f"otw, poinnya {rewardnya}")
                print(f"TeleporterA : ({self.goal_position.x}, {self.goal_position.y})")
            elif teleState == 2 and self.distance(board_bot.position, listTeleporters[1].position) != 0:
                self.goal_position = listTeleporters[1].position
                print(f"otw, poinnya {rewardnya}")
                print(f"TeleporterB : ({self.goal_position.x}, {self.goal_position.y})")
            else: # teleState == 0:
                print(f"waktumu sisa {board_bot.properties.milliseconds_left}")
                print(f"otw, poinnya {rewardnya}")
                print(f"Diamond : x = ({self.goal_position.x}, {self.goal_position.y})")
            
        else :
            # Ini apa lagi
            # Ya yang ini declare variable
            gp, teleState2, nearestDistDM, rewardnya = self.findNearestDiamondAlt(listDiamond, listTeleporters, board_bot)
            # Ini tuh waktu pulang, nah, kebetulan ada diamond deket di jalan, ambil dikit nggak ngaruh
            # Sama kalau misal masih sempet pulang sebelum meninggal
            if (nearestDistDM <= 2 and (props.diamonds+rewardnya)<=5) and not ((baseDist + 1 >= (board_bot.properties.milliseconds_left/1000))):
                # Mirip kayak teleState diatas
                if teleState2 == 1 and self.distance(board_bot.position, listTeleporters[0].position) != 0:
                    self.goal_position = listTeleporters[0].position
                elif teleState2 == 2 and self.distance(board_bot.position, listTeleporters[1].position) != 0:
                    self.goal_position = listTeleporters[1].position
                else: 
                    self.goal_position = gp
            # Udah kenyang cik woilah
            else:
                self.goal_position = board_bot.properties.base
                if teleState1 == 1 and self.distance(board_bot.position, listTeleporters[0].position) != 0:
                    self.goal_position = listTeleporters[0].position
                    print(f"TeleporterA (Base) : ({self.goal_position.x}, {self.goal_position.y})")
                elif teleState1 == 2 and self.distance(board_bot.position, listTeleporters[1].position) != 0:
                    self.goal_position = listTeleporters[1].position
                    print(f"TeleporterB (Base) : ({self.goal_position.x}, {self.goal_position.y})")
                else: #teleState == 0:
                    print(f"Base : ({self.goal_position.x}, {self.goal_position.y})")

        # Ya setelah perhitungan di atas, kita ambil arahnya
        delta_x, delta_y = get_direction(
            current_position.x,
            current_position.y,
            self.goal_position.x,
            self.goal_position.y,
        )
        
        # Ini untuk corner case (actually corner)
        if (delta_x == 0 and delta_y == 0):
            if (current_position.y == 0):
                delta_x = 0; delta_y = 1
            else:
                delta_x = 0; delta_y = -1

        # Akhirnya
        return delta_x, delta_y