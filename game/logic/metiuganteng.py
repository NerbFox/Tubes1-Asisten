from game.logic.base import BaseLogic
from game.models import Board, GameObject
from ..util import get_direction,position_equals

# LOGIC GREEDY UNTUK GAME DIAMOND ETIMO OLEH KELOMPOK METIUGANTENG
#---------------------metiuganteng--------------------------------

# Menentukan nilai arah apakah 1 atau -1
def clamp(n, smallest, largest):
    return max(smallest, min(n, largest))

# Mendapatkan arah gerak bot setelah beberapa konsiderasi, yakni letak teleport dan bot lawan di sekitar kita
# Jika tidak ada teleport ataupun bot di arah tujuan kita, maka bot akan memprioritaskan gerak vertikal
def get_direction(current_x, current_y, dest_x, dest_y,teleports,bots):
    delta_x = clamp(dest_x - current_x, -1, 1)
    delta_y = clamp(dest_y - current_y, -1, 1)
    # Periksa keberadaan bot lawan di sekitar, ketika salah satu komponen gerak vertikal/horizontal belum 0
    if not(delta_x==0 or delta_y==0):
        for bot in bots:
            # Jika terdapat bot lawan di kanan atau kiri kita searah tujuan yang menghalangi, bot lawan kita tabrak
            if bot.position.x == current_x+delta_x and bot.position.y == current_y:
                delta_y = 0
            # Jika terdapat bot lawan di atas atau bawah kita searah tujuan yang menghalangi, bot lawan kita tabrak
            elif bot.position.y == current_y+delta_y and bot.position.x == current_x:
                delta_x = 0
    if not(delta_x==0 or delta_y==0):
        for tele in teleports:
            # Jika terdapat teleport di kanan atau kiri kita searah tujuan yang menghalangi dan gerak tujuan bot terdapat komponen vertikal,
            # Utamakan gerak vertikal
            if tele.x == current_x+delta_x and tele.y == current_y and delta_y!=0:
                delta_x = 0
            # Jika terdapat teleport di atas atau bawah kita searah tujuan yang menghalangi dan gerak tujuan bot terdapat komponen horizontalnya,
            # Utamakan gerak horizontal
            elif tele.y == current_y+delta_y and tele.x == current_x and delta_x!=0:
                delta_y = 0
    # Jika tidak terdapat teleport dan bot di sekitar dan salah satu komponen gerak belum ada yang 0,
    # Utamakan gerak vertikal
    if not(delta_x==0 or delta_y==0):
        delta_x = 0
    return (delta_x, delta_y)

# Menghitung Manhattan Distance antara point1 dan point2
def distTotal(point1, point2):
    return abs(point1.x-point2.x) + abs(point1.y-point2.y)

# Mencari rute terbaik, apakah tidak melalui teleport, melalui teleport 1, ataupun melalui teleport 2
# Mengembalikan tuple berisi jarak terbaik, posisi tele tujuan, posisi tele keluar, dan diamond/object apa yang sedang diincar
# Jika tidak melalui teleport, posisi tele tujuan = posisi tele keluar = lokasi objek incaran
def bestRoute(tele,dest,pos):
    # Rute tanpa melalui teleport
    bestDist = distTotal(dest,pos)
    bestDest1 = dest
    bestDest2 = dest
    # Rute melalui teleport 1
    dist = distTotal(pos,tele[0])+distTotal(tele[1],dest)
    if dist<bestDist and pos != tele[0]:
        bestDist = dist
        bestDest1 = tele[0]
        bestDest2 = tele[1]
    # Rute melalui teleport 2
    dist = distTotal(pos,tele[1])+distTotal(tele[0],dest)
    if dist<bestDist and pos != tele[1]:
        bestDist = dist
        bestDest1 = tele[1]
        bestDest2 = tele[0]
    return (bestDist,bestDest1,bestDest2,dest)
    # [0] = jarak bot ke tujuan (bisa tele atau objek incaran)
    # [1] = lokasi tujuan bot sekarang (bisa tele atau objek incaran)
    # [2] = lokasi teleport keluar (optional)
    # [3] = lokasi objek incaran

# Mencari diamond terdekat dengan diamond pada lokasi "pos", yang memiliki jarak/poin terkecil
# Mengembalikan jarak terdekat dan poin diamond terdekat
def worthDim(teleports,diamonds,pos):
    minDist = 9999
    poin = 1
    for d in diamonds:
        dist = bestRoute(teleports,d.position,pos)[0]
        if(dist/d.properties.points<minDist/poin and dist != 0):
            minDist = dist
            poin = d.properties.points
    return (minDist,poin)

# Mengembalikan nilai terkecil total jarak dibagi total poin antara mengambil diamond pada dimPos aja atau
# mengambil diamond dimPos dan diamond closest
def bestRatio(poin,dimPos, botPos, diamonds, teleports):
    # distDim untuk mendapatkan jarak terdekat bot dengan diamond A
    distDim = bestRoute(teleports,dimPos,botPos)[0]
    # closest untuk mendapatkan informasi diamond yang terdekat dengan A, kita sebut B
    closest = worthDim(teleports,diamonds,dimPos)
    # Mengembalikan nilai terkecil total jarak dibagi total poin, antara dua pilihan gerak tadi
    return min(distDim/poin,(distDim+closest[0])/(poin+closest[1]))

# Menyeleksi diamonds yang telah tersort dengan key sort berupa hasil bestRatio masing2 diamond dari yang terkecil
def bestGoal(teleports,diamonds,bots,botPos,currentDim):
    defDest = 0
    defFound = False
    for dims in diamonds:
        # Jika jumlah diamond di inventory 4 dan diamond incaran berpoin 2, kita skip
        if currentDim==4 and dims.properties.points==2:
            continue
        reachable = True
        ourBest = bestRoute(teleports,dims.position,botPos)
        if not defFound:
            # Menentukan default tujuan, jika semua diamond memiliki bot lawan yang lebih dekat
            defFound = True
            defDest = ourBest
        # Membandingkan jarak kita dan jarak lawan dengan diamondnya
        for enemy in bots:
            enemyBest = bestRoute(teleports,dims.position,enemy.position) 
            if enemyBest[0]<ourBest[0]:
                # Jika terdapat satu bot saja yang lebih dekat, langsung kita pass
                reachable = False
                break
        # Jika bisa digapai (kita yang paling dekat dengan diamond), return diamond tersebut sebagai tujuan gerakan kita
        if reachable:
            return ourBest
    # Return default jika tidak ada diamond yang memenuhi
    return defDest

# Mengecek apakah point berada di antara point1 dan point2
def betweenPoint(point1,point2,point):
    valid_x = (point1.x<=point.x<=point2.x)or(point2.x<=point.x<=point1.x)
    valid_y = (point1.y<=point.y<=point2.y)or(point2.y<=point.y<=point1.y)
    return valid_x and valid_y

# Menghitung jumlah gerakan tambahan yang dibutuhkan untuk mencapai diamond, yang berlawanan dengan
# arah gerakan ketika ke base
# Misalkan jika arah untuk ke base adalah kanan bawah, maka menghitung gerakan tambahan kiri atas yang diperlukan untuk
# ke diamond
def extraMove(dest,pos,dimPos):
    if betweenPoint(dest,pos,dimPos):
        return 0
    temp = 0
    upperY = max(dest.y,pos.y)
    lowerY = min(dest.y,pos.y)
    upperX = max(dest.x,pos.x)
    lowerX = min(dest.x,pos.x)
    if dimPos.y>upperY:
        temp+=dimPos.y-upperY
    elif dimPos.y<lowerY:
        temp+= lowerY-dimPos.y
    if dimPos.x>upperX:
        temp+=dimPos.x-upperX
    elif dimPos.x<lowerX:
        temp+=lowerX-dimPos.x
    return temp    

# Total jarak perjalanan dari posisi sekarang ke diamond dan kemudian ke base
# Dapat menggunakan teleport atau tidak
def totalDistTravel(teleports,botPos,dimPos,base):
    botToTele = bestRoute(teleports,dimPos,botPos)
    teleToDim = distTotal(dimPos,botToTele[2])
    dimToTele = bestRoute(teleports,base,dimPos)
    teleToBase = distTotal(base,dimToTele[2])
    return botToTele[0]+teleToDim+dimToTele[0]+teleToBase

class botLogic(BaseLogic):
    def __init__(self):
        self.directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        self.goal = 9999 #default

    def next_move(self, board_bot: GameObject, board: Board):
        # Setup array bots, teleports, diamonds, dan lokasi shuffle
        # teleports : List of position
        teleports = []
        # bots : List of Game Object
        bots = []
        # diamonds : List of Game Object
        diamonds = []
        # Position dimana shuffle berada
        shuffle = 0
        for x in board.game_objects:
            if(x.type == "BotGameObject"):
                bots.append(x)
            elif x.type == "DiamondGameObject":
                diamonds.append(x)
            elif x.type == "TeleportGameObject":
                teleports.append(x.position)
            elif x.type == "DiamondButtonGameObject":
                shuffle = x.position

        # Variabel-variabel pendukung
        props = board_bot.properties #Properties dari bot kita
        botPos = board_bot.position #Posisi bot kita sekarang
        base = props.base #Posisi base
        toBase = bestRoute(teleports,base,botPos) #Rute menuju base dari lokasi sekarang

        # Jika jumlah diamond di inventory adalah 5, kita balik ke base
        if props.diamonds==5:
            self.goal = toBase
        # Jika jumlah diamond di inventory kurang dari 3 dan waktu permainan yang tersisa lebih dari 20 detik,
        elif props.diamonds<3 and (props.milliseconds_left//1000>=20):
            # Mensort array diamonds dengan teknik greedy, yakni (total jarak/total poin) yang terkecil
            # Nilai total jarak bagi total poin tiap diamond didapatkan dari total jarak/total poin yang terkecil antara
            # Mengambil diamond tersebut saja atau mengambil diamond lain yang terdekat dengan diamond tersebut juga
            diamonds = sorted(diamonds,key= lambda x: bestRatio(x.properties.points,x.position,botPos,diamonds,teleports))
            # Seleksi kandidat diamonds
            self.goal = bestGoal(teleports,diamonds,bots,botPos,props.diamonds)

        # Jika jumlah diamond di inventory lebih dari sama dengan 3 atau sisa waktu permainan kurang dari 20 detik lagi,
        else:
            # Mensort array diamonds dengan teknik greedy, yakni total jarak terkecil dari perjalanan posisi bot sekarang ke diamond tujuan ditambah posisi diamond tujuan ke base
            # (Dapat melalui teleport atau tidak) 
            # Jika terdapat nilai yang sama, didahulukan berdasarkan jarak terdekat dengan bot
            diamonds = sorted(diamonds, key=lambda x: (totalDistTravel(teleports, botPos, x.position, base)/x.properties.points, bestRoute(teleports, x.position, botPos)[0]))
            # Seleksi kandidat diamonds
            self.goal = bestGoal(teleports,diamonds,bots,botPos,props.diamonds)

            # Jika jumlah diamond inventory lebih besar sama dengan 3
            if props.diamonds>=3:
                # Jika diamond tujuan tidak berada di antara gerakan posisi bot menuju base
                if (not betweenPoint(botPos,toBase[1],self.goal[1]) and not betweenPoint(base,toBase[2],self.goal[1])) and min(extraMove(toBase[1],botPos,self.goal[1]),extraMove(base,toBase[2],self.goal[1]))>2:
                    self.goal = toBase

        # Jika jarak kita dengan tujuan lebih besar sama dengan jarak kita ke shuffle ditambah 5
        shuffleRoute = bestRoute(teleports,shuffle,botPos)
        if self.goal[0]+distTotal(self.goal[2],self.goal[3])>=shuffleRoute[0]+distTotal(shuffleRoute[2],shuffle)+5 and props.diamonds<3:
            self.goal = shuffleRoute

        # Jika base berada di antara bot kita dan tujuan dan posisi bot bukanlah posisi base, kunjungi base dahulu
        if betweenPoint(self.goal[1],botPos,toBase[1]) and not(botPos.x==base.x and botPos.y==base.y):
            self.goal = toBase
        
        # Jika waktu untuk mengambil diamond dan kembali ke base tidak cukup (lebih kecil dari sisa waktu), dan terdapat diamond di inventory, kembali ke base
        if totalDistTravel(teleports,botPos,self.goal[3],base)>(props.milliseconds_left//1000) and props.diamonds>0 and (not betweenPoint(toBase[1],botPos,self.goal[1]) and not betweenPoint(toBase[2],base,self.goal[1])):
            self.goal = toBase

        delta_x,delta_y = get_direction(
            botPos.x,
            botPos.y,
            self.goal[1].x,
            self.goal[1].y,
            teleports,
            bots,
        )   
        return delta_x, delta_y