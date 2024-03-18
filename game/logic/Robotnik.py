from typing import List, Optional
from ..util import get_direction
    
from game.logic.base import BaseLogic
from game.models import Board, GameObject, Position, Properties
    
class Robotnik(BaseLogic):
    def __init__(self):
        self.directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        self.goal_position: Optional[Position] = None
        self.poin_lama: int = 0
    
    def next_move(self, board_bot: GameObject, board: Board):
        # FUNGSI PEMBANTU
        def isEqualPosition(Pos1, Pos2):
            # Mengembalikan true jika Pos1 sama dengan Pos2
            if not(Pos1 and Pos2):
                return False
            return (Pos1.x == Pos2.x and Pos1.y == Pos2.y)
        def isTargetValid(diamonds, teleporters):   
            # Mengembalikan true jika terdapat diamond / teleporter pada posisi self.goal_position
            return (any(isEqualPosition(diamond.position, self.goal_position) for diamond in diamonds) or \
                    any(isEqualPosition(teleporter.position, self.goal_position) for teleporter in teleporters))
        def isTeleporter(board_bot: GameObject, teleporters: List[GameObject]) -> bool:
            # Mengembalikan true jika terdapat teleporter pada posisi bot
            return (any(isEqualPosition(teleporter.position, board_bot.position) for teleporter in teleporters))
        def Jarak(Pos1: Position, Pos2: Position) -> int:
            # Mengembalikan jumlah gerakan yang diperlukan untuk bergerak dari Pos1 ke Pos2
            return (abs(Pos1.y - Pos2.y) + abs(Pos1.x - Pos2.x))
        def JarakTeleporter(board_bot: GameObject, teleporters: List[GameObject], diamond: Optional[GameObject], base: Optional[Position]):
            # Mengembalikan teleporter terdekat dan jarak diamond melalui teleporter terdekat tsb
            nearest_teleporter = teleporters[0]
            farthest_teleporter = teleporters[1]

            current_position = board_bot.position
            if Jarak(current_position, teleporters[1].position) < Jarak(current_position, teleporters[0].position):
                nearest_teleporter = teleporters[1]
                farthest_teleporter = teleporters[0]
            if base:
                return nearest_teleporter, Jarak(current_position, nearest_teleporter.position) + Jarak(base, farthest_teleporter.position)
            return nearest_teleporter, Jarak(current_position, nearest_teleporter.position) + Jarak(diamond.position, farthest_teleporter.position)
        
        # FUNGSI SELEKSI
        def seleksi(diamonds: List[GameObject], board_bot: GameObject, board: Board) -> tuple[Optional[GameObject], Optional[GameObject]]:
            # Mengembalikan diamond atau none jika tidak terdapat diamond yang memenuhi fungsi kelayakan

            # FUNGSI KELAYAKAN
            def layak(kandidatSolusi: tuple[Optional[GameObject], Optional[GameObject]], board_bot: GameObject) -> bool:
                # Mengembalikan true jika diamond yang dipilih layak
                if kandidatSolusi[0]:
                    if isEqualPosition(board_bot.position, kandidatSolusi[0].position):
                        return False
                if kandidatSolusi[1]:
                    if isEqualPosition(board_bot.position, kandidatSolusi[1].position):
                        return False
                    if (kandidatSolusi[1].properties.points == 2 and board_bot.properties.diamonds >= 4):
                        return False
                    # return (board_bot.properties.diamonds + kandidatSolusi.properties.points <= 5)    
                return True

            def rumus(n: GameObject, isTeleporter: bool, teleporters):
                if (isTeleporter):
                    nearest_teleporter, dist = JarakTeleporter(board_bot, teleporters, n, None)
                    return (nearest_teleporter, (dist / n.properties.points))
                return ((Jarak(current_position, n.position) / n.properties.points))
            
            teleporters = [t for t in board.game_objects if t.type == "TeleportGameObject"]

            # list poin diamond dengan jarak tanpa melalui teleporter & melalui teleporter
            poin = [rumus(n, False, teleporters) for n in diamonds]
            poin_teleporter = [rumus(n, True, teleporters) for n in diamonds]
            
            # jarak minimum diamond tanpa melalui teleporter
            min_nt = min(poin)
            index_min = poin.index(min_nt)

            # cari min + index min dari poin_teleporter
            index_min_tel, index = 0, 0
            min_teleporter = poin_teleporter[0][1]
            for i in poin_teleporter:
                if i[1] < min_teleporter:
                    min_teleporter = i[1]
                    index_min_tel = index
                index += 1
            
            # membandingkan jarak terdekat melalui teleporter dengan jarak terdekat tanpa melalui teleporter
            isTeleporter = False
            if (min_teleporter < min_nt): 
                index_min = index_min_tel
                isTeleporter = True # apabila jarak terdekat melalui teleporter maka target teleporter terdekat

            kandidatSolusi = poin_teleporter[index_min][0] if isTeleporter else None, diamonds[index_min]

            # mengecek kelayakan kandidat solusi
            while not layak(kandidatSolusi, board_bot):
                if len(diamonds) - 1 == 0:
                    # Tidak ada diamond yang layak, balik ke base
                    kandidatSolusi = None, None
                    break
                del diamonds[index_min]
                kandidatSolusi = seleksi(diamonds, board_bot, board) 

            return (kandidatSolusi)
        
        # FUNGSI OBYEKTIF
        def resetTarget(current_position: Position, stats: Properties, teleporters: List[GameObject]) -> bool:
            # Mengembalikan true jika:
            if isEqualPosition(current_position, stats.base):
                # Ada di base 
                return True
            if isTeleporter(board_bot, teleporters):
                # Masuk teleporter
                return True
            if  self.goal_position:
                if isEqualPosition(self.goal_position, current_position):
                    # Sudah sampai tujuan
                    return True
                if not isEqualPosition(self.goal_position, stats.base) and not isTargetValid(diamonds, teleporters):
                    # Target yang dituju sudah tidak ada di board
                    return True
                if self.poin_lama != stats.diamonds:
                    # Poin berubah
                    return True
            return False
        
        # FUNGSI SOLUSI
        def fungsiSolusi(stats: Properties) -> bool:
            # Mengembalikan TRUE jika inventory bot penuh
            return (stats.diamonds == 5)

        # ------------------------------------------------------------------------------------------------------- #

        stats = board_bot.properties
        current_position = board_bot.position
        diamonds = board.diamonds
        teleporters = [t for t in board.game_objects if t.type == "TeleportGameObject"]
    
        if resetTarget(current_position, stats, teleporters):
            self.goal_position = None

        if fungsiSolusi(stats):
            # Apabila inventory penuh kembali ke base
            self.goal_position = stats.base
        elif stats.diamonds != 5 and self.goal_position == None:    
            solusi = seleksi(diamonds, board_bot, board)
            self.poin_lama = board_bot.properties.diamonds

            if not solusi[1]:
                self.goal_position = stats.base
            else:
                self.goal_position = solusi[1].position if not solusi[0] else solusi[0].position
        
        if isEqualPosition(self.goal_position, stats.base):
            nearest_teleporter, distTeleporter = JarakTeleporter(board_bot, teleporters, None, stats.base)
            distNormal = Jarak(current_position, stats.base)
            if( distTeleporter < distNormal):
                self.goal_position = nearest_teleporter.position
            else:
                self.goal_position = stats.base

        delta_x, delta_y = get_direction(
            current_position.x,
            current_position.y,
            self.goal_position.x,
            self.goal_position.y,
        )
        
        # Bug Handler
        if (delta_x == delta_y):
            for i in self.directions:
                if (0 <= current_position.x + i[0] < board.width) and (0 <= current_position.y + i[1] < board.height):
                    delta_x = i[0]
                    delta_y = i[1]
                    break

        return delta_x, delta_y