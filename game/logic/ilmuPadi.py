from typing import Optional
from typing import List
from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position


class Padibot(BaseLogic):
    def __init__(self):
        self.directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        self.goal_position: Optional[Position] = None
        self.current_direction = 0
        self.chaseSteps = 0
        self.isPortal = False

    #! DIAMOND SECTION
    # fungsi mengambil lokasi kumpulan diamond yang ada di sekitar base dalam bentuk list
    # implementasi greedy by closest to base
    def diamondsaroundbase(self, board_bot: GameObject, board:Board):
        props = board_bot.properties
        diamonds = board.diamonds
        
        base_x, base_y = props.base.x, props.base.y
        diamond_loc = [diamond.position for diamond in diamonds
                       if base_x - 3 <= diamond.position.x <= base_x + 3
                       and base_y - 3 <= diamond.position.y <= base_y + 3]
        
        return diamond_loc
    
    # memeriksa apakah lokasi bot lagi di sekitar base
    # implementasi greedy by closest to base
    def botaroundbase(self, board_bot: GameObject):
        props = board_bot.properties
        current_position = board_bot.position
        return ((props.base.x-3) <= current_position.x <= (props.base.x+3) and (props.base.y-3) <= current_position.y <= (props.base.y+3))
    
    # mencari diamond biru yang paling dekat base dengan posisi bot
    # implementasi greedy by shortest path to current position
    def closestdiamondbase(self, board_bot: GameObject, diamonds: List[Position]):
        current_position = board_bot.position
        closest_diamond = min(diamonds, key=lambda diamond: abs(diamond.x - current_position.x) + abs(diamond.y - current_position.y))
        return closest_diamond
    
    # cek apakah ada diamond sekitar base
    # implementasi greedy by closest to base
    def cekdiamondbase(self, board_bot: GameObject, board:Board):
        ada = False
        diamonds = board.diamonds
        
        # lokasi diamonds sekitar base
        for diamond in diamonds:
            if (board_bot.properties.base.x-2) <= diamond.position.x <= (board_bot.properties.base.x+2) and (board_bot.properties.base.y-2) <= diamond.position.y <= (board_bot.properties.base.y+2):
                return True
                
        return ada
    
    # cari diamond terdekat dengan bot (bebas di mana aja)
    # implementasi greedy by chasing diamond
    def closestdiamond(self, board_bot: GameObject,board:Board):
        current_position = board_bot.position
        diamonds = [diamond for diamond in board.diamonds if diamond.properties.points == 1]
        if not diamonds:
            return None  # Jika tidak ada blue diamond, kembalikan None
        closest_red_diamond = min(diamonds, key=lambda diamond: abs(diamond.position.x - current_position.x) + abs(diamond.position.y - current_position.y))
        return closest_red_diamond.position

    # mencari jarak bot dengan diamond terdekat
    def closestdiamonddist(self, board_bot: GameObject,board: Board):
        closest = self.closestdiamond(board_bot, board)
        current_position = board_bot.position
        
        if closest is None:
            return 999
        
        return abs(closest.x-current_position.x)+abs(closest.y-current_position.y)
    
     # cari red diamond terdekat dengan bot (bebas di mana aja)
     # implementasi greedy by chasing diamond
    def closestreddiamond(self, board_bot: GameObject, board:Board):
        current_position = board_bot.position
        red_diamonds = [diamond for diamond in board.diamonds if diamond.properties.points == 2]

        if not red_diamonds:
            return None  # Jika tidak ada red diamond, kembalikan None

        closest_red_diamond = min(red_diamonds, key=lambda diamond: abs(diamond.position.x - current_position.x) + abs(diamond.position.y - current_position.y))
        return closest_red_diamond.position
    
    # mencari jarak bot dengan diamond merah terdekat
    def closestreddiamonddist(self, board_bot: GameObject, board: Board):
        current_position = board_bot.position
        red_diamonds = [diamond for diamond in board.diamonds if diamond.properties.points == 2]

        if not red_diamonds:
            return 999
        
        closest_red_diamond = min(red_diamonds, key=lambda diamond: abs(diamond.position.x - current_position.x) + abs(diamond.position.y - current_position.y))
        distance = abs(closest_red_diamond.position.x - current_position.x) + abs(closest_red_diamond.position.y - current_position.y)
        return distance
    
    # mencari jarak bot dengan base
    def basedistance(self, board_bot: GameObject):
        # mencari jarak bot dengan base
        current_position = board_bot.position
        base = board_bot.properties.base
        return abs(base.x - current_position.x) + abs(base.y - current_position.y)

    #! BOT SECTION
    # implementasi greedy by chasing enemy
    # Menghitung jarak (x, y) dari enemy bot ke kita
    def calculateDistanceToBots(self, board_bot: GameObject, enemy_bot: GameObject):
        return (enemy_bot.position.x - board_bot.position.x, enemy_bot.position.y - board_bot.position.y)
    
    # Mencari semua bot yang memiliki diamonds >= 3 saja dan diamonds nya lebih banyak dari kita
    def findAllBots(self, board_bot: GameObject, board: Board):
        listBots = []
        for bot in board.bots:
            if (bot.id != board_bot.id and bot.properties.base.x != bot.position.x and bot.properties.base.y != bot.position.y):
                if (bot.properties.diamonds > board_bot.properties.diamonds and bot.properties.diamonds >= 3):
                    listBots.append(bot)
        return listBots
    
    # Menjadikan bot sebagai goal_position, jika jarak ke bot musuh adalah 3, dan jarak bot kita ke base tidak lebih dari 6
    def chaseBots(self, board_bot: GameObject, board: Board):
        if self.basedistance(board_bot) <= 4 and self.chaseSteps <= 5:
            listBots = self.findAllBots(board_bot, board)
            for bot in listBots:
                dist = self.calculateDistanceToBots(board_bot, bot)
                if (dist[0] == 0 and dist[1] == 0):
                    # Bot sudah berhasil di-tackle, kembali ke base
                    self.goal_position = board_bot.properties.base
                    return False
                elif (dist[0] <= 3 and dist[1] <= 3):
                    self.goal_position = bot.position
                    return True
                else:
                    self.goal_position = None
                    return False
        else:
            self.goal_position = None
            self.chaseSteps = 0
            self.isPortal = False
            return False
    
    #! RED BUTTON
    # implementasi greedy by inventory
    # Mencari red button
    def findRedButton(self, board: Board):
        for item in board.game_objects:
            if item.type == "DiamondButtonGameObject":
                return item
    
    # Compare jarak closest diamond dengan red button. Lebih baik generate ulang daripada ke diamond jauh
    # Hanya jika diamond yang ada di board sedikit (pre-checked in next_move)
    def compareClosestDiamondToRedButton(self, board_bot: GameObject, board: Board):
        if self.closestdiamond(board_bot,board) is not None:
            if self.calculateDistanceRedButton(board_bot, board) < self.closestdiamonddist(board_bot, board):
                return True
        return False
    
    # Menghitung jarak ke red button 
    def calculateDistanceRedButton(self, board_bot: GameObject, board: Board):
        redButton = self.findRedButton(board)
        return abs(redButton.position.x - board_bot.position.x) + abs(redButton.position.y - board_bot.position.y)
    
    #! TELEPORTER
    # implementasi dari greedy by shortest path
    # Mencari semua teleporter yang ada
    def findAllTeleporter(self, board_bot: GameObject, board: Board):
        teleporters = [item for item in board.game_objects if item.type == "TeleportGameObject"]
        return sorted(teleporters, key=lambda tele: (abs(tele.position.x - board_bot.position.x) + abs(tele.position.y - board_bot.position.y)))
    
    # Mencari jarak dari teleporter ke base
    def goToBaseWithTeleporter(self, board_bot: GameObject, board: Board):
        teleporters = self.findAllTeleporter(board_bot, board)
        distToBase = abs(board_bot.properties.base.y - teleporters[1].position.y) + abs(board_bot.properties.base.x - teleporters[1].position.x)
        if (distToBase == abs(board_bot.properties.base.y - teleporters[0].position.y) + abs(board_bot.properties.base.x - teleporters[0].position.x)):
            return
        distToBot = abs(board_bot.position.x - teleporters[0].position.x) + abs(board_bot.position.y - teleporters[0].position.y)
        if (distToBase + distToBot < self.basedistance(board_bot)):
            self.isPortal = True
            self.goal_position = teleporters[0].position

    #! GET DIRECTIONS
    # Set direction and move, 2nd main function
    def get_directions(self,current_x, current_y, dest_x, dest_y):
        # bikin biar geraknya rada zigzag
        # cari jarak x dan y nya dulu
        delta_x = abs(dest_x - current_x)
        delta_y = abs(dest_y - current_y)
        x=0
        y=0

        if (dest_x - current_x)<0:
            x = -1 # jalan ke kiri
        else:
            x = 1 # jalan ke kanan

        if (dest_y - current_y)<0:
            y = -1 # jalan ke bawah
        else:
            y = 1 # jalan ke atas

        if delta_x >= delta_y: # ini kalau posisinya belum kotak dia bakal gerak horizontal sampai kotak
            dx = x
            dy = 0
        elif delta_x < delta_y: # kalau udah kotak dia bakal jalan vertikal
            dy = y
            dx = 0
        return (dx, dy)

    def next_move(self, board_bot: GameObject, board: Board):
        props = board_bot.properties
        current_position = board_bot.position
        
        # kalau mepet waktu, langsung balik ke base
        if self.basedistance(board_bot) == props.milliseconds_left:
            base = board_bot.properties.base
            self.goal_position = base
        
        # kalau pas cari diamond lewat base, bot mampir ke base dulu
        elif (self.basedistance(board_bot)==2 and props.diamonds >2) or (self.basedistance(board_bot)==1 and props.diamonds >0):
            base = board_bot.properties.base
            self.goal_position = base

        # kalau full segera balik ke base
        elif props.diamonds ==5:
            base = board_bot.properties.base
            self.goal_position = base

        # kalau diamond yang dimiliki sudah lebih dari 3 maka bot diarahkan balik ke base
        elif props.diamonds >= 3:
            # ternyata ada diamond dekat base, maka bot akan ke sana
            if self.closestdiamond(board_bot,board) is not None or self.closestreddiamond(board_bot,board) is not None:
                if props.diamonds == 3 and self.closestreddiamonddist(board_bot,board) <= 3:
                    self.goal_position = self.closestreddiamond(board_bot,board)
                elif self.closestdiamonddist(board_bot,board)<=3:
                    self.goal_position = self.closestdiamond(board_bot,board)
                else:
                    base = board_bot.properties.base
                    self.goal_position = base
            elif self.cekdiamondbase(board_bot,board):
                diamond_list = self.diamondsaroundbase(board_bot,board)
                self.goal_position = self.closestdiamondbase(board_bot,diamond_list)
            # kalau pas jalan pulang ternyata ada diamond yang deket dan inventory belum penuh (sekalian ambil)
            else:
            # balik ke base karena diamond sudah banyak
                base = board_bot.properties.base
                self.goal_position = base
            
        # kalau masih kurang 3 akan cari diamond
        elif props.diamonds < 3:
            # didahuluin cari yang ada di sekitar base dulu (bot kita juga di sekitar base)
            if (self.cekdiamondbase(board_bot,board) and self.botaroundbase(board_bot)) or (self.cekdiamondbase(board_bot,board) and len(self.diamondsaroundbase(board_bot,board))>=3) :
                diamond_list = self.diamondsaroundbase(board_bot,board)
                self.goal_position = self.closestdiamondbase(board_bot,diamond_list)
            elif (self.chaseBots(board_bot, board)):
                self.chaseSteps += 1
            # kalau gak ada baru cari yang lebih jauh
            # Prioritaskan red diamond jika lebih dekat dari pada diamond biasa
            elif self.compareClosestDiamondToRedButton(board_bot, board):
                self.goal_position = self.findRedButton(board).position
            elif self.closestreddiamond(board_bot, board) is not None: 
                if (self.closestdiamond(board_bot, board) is not None):
                    if (self.closestreddiamonddist(board_bot, board) < self.closestdiamonddist(board_bot, board)) :
                        self.goal_position = self.closestreddiamond(board_bot,board)
                    else:
                        self.goal_position = self.closestdiamond(board_bot, board)
                else: # misal sisa red diamonds aja
                    self.goal_position = self.closestreddiamond(board_bot,board)
            else: # sisa diamond biru
                self.goal_position = self.closestdiamond(board_bot, board)
                
        # bot sedang tidak ada tujuan maka di arahkan ke base
        if self.goal_position is None:
            self.goal_position = board_bot.properties.base
        
        if self.goal_position == board_bot.properties.base and not self.isPortal:
            self.goToBaseWithTeleporter(board_bot, board)
        
        delta_x, delta_y = self.get_directions(
            current_position.x,
            current_position.y,
            self.goal_position.x,
            self.goal_position.y,
        )

        return delta_x, delta_y
