import math
from ..util import get_direction
from game.models import Board, GameObject

class Pulang(object):
    def __init__(self):
        #Menginisialisasi goal_position, previous_position, dan turn_direction
        self.goal_position = None # goal_position adalah posisi yang ingin dicapai oleh bot, dan akan diinisialisasi dengan None karena belum ada goal position
        self.previous_position = (None, None) # previous_position adalah posisi sebelumnya yang diinisialisasi dengan (None, None) karena bot belum bergerak
        self.turn_direction = 1 # turn_direction adalah arah putaran bot yang diinisialisasi dengan 1 yang berarti ke kanan
    
    # Fungsi ini digunakan untuk pulang ke base jika beberapa kondisi terpenuhi
    def go_home(self, board_bot: GameObject, board: Board):
        props = board_bot.properties

        # Mendapatkan waktu yang tersisa dalam milisecond
        current_time = props.milliseconds_left

        # Mengubah waktu yang tersisa dari milisecond ke detik
        new_time = current_time / 1000

        base = props.base

        # Menghitung estimasi waktu yang dibutuhkan untuk sampai ke base dengan manhattan distance
        estimated_time_to_base = abs(base.x - board_bot.position.x) + abs(base.y - board_bot.position.y)

        # Jika waktu yang tersisa kurang dari 10 detik dan estimasi waktu yang dibutuhkan untuk sampai ke base lebih besar sama dengan dari waktu yang tersisa
        # atau jika diamond yang dimiliki bot adalah 3 atau 4 dan estimasi waktu yang dibutuhkan untuk sampai ke base kurang dari 4
        # Maka goal positionnya adalah base
        if current_time < 10000 and estimated_time_to_base >= new_time or (props.diamonds in [3,4] and estimated_time_to_base < 4 ):
            self.goal_position = base 
        else:
            self.goal_position = None
    
    # Fungsi ini digunakan untuk mencari diamond dengan rasio terbesar pada setiap langkahnnya
    # yang mana merupakan implementasi dari algoritma greedy
    def purge(self, board_bot: GameObject, board: Board):
        # Mendapatkan semua diamond yang ada di board dengan cara mengiterasi semua game object pada board
        # lalu mencari type yang diinginkan yakni "DiamondGameObject"
        diamonds = [go for go in board.game_objects if go.type == "DiamondGameObject"]
        
        # Menginisialisasi max_ratio dengan -1 dan min_index dengan None
        max_ratio = -1
        min_index = None

        # Untuk setiap diamond, kalkulasi rasio dari diamond point dengan jarak manhattan antara bot dan diamond
        for i, diamond in enumerate (diamonds):
            bot_diamonds = board_bot.properties.diamonds # Mendapatkan jumlah diamond yang dimiliki oleh bot
            diamond_points = diamond.properties.points # Mendapatkan point dari diamond

            if (bot_diamonds + diamond_points > 5): # Jika jumlah diamond yang dimiliki bot setelah mengambil diamond ini lebih dari 5, maka skip diamond ini
                continue

            # Melakukan kalkulasi jarak manhattan antara bot dan diamond
            # Dengan cara mengurangi x dan y koordinat dari posisi diamond dengan posisi bot
            # Lalu hasilnya diabsolutkan agar tidak ada nilai negatif
            x_dist = abs(board_bot.position.x - diamond.position.x)
            y_dist = abs(board_bot.position.y - diamond.position.y)
            manhattan_dist = x_dist + y_dist        

            # Jika jarak manhattannya 0, berarti bot sudah berada di posisi diamond, yang berarti
            # bot tidak lagi perlu melakukan kalkulasi ratio untuk diamond yang ini, jadi diamond yang ini akan diskip perhitungannya
            # dan akan langsung dilanjutkan ke diamond selanjutnya
            if manhattan_dist == 0: 
                continue
            
            # Mengkalkulasi rasio dari diamond point dengan jarak dari bot ke diamond
            # Rasio ini akan digunakan untuk menentukan diamond mana yang akan dijadikan goal position
            # Diamond dengan point yang lebih tinggi dan jarak yang lebih dekat akan memiliki rasio lebih besar
            ratio = diamond_points / manhattan_dist

            # Jika rasio ini adalah rasio terbesar yang ditemukan sejauh ini, maka update max_ratio dan min_index
            # max_ratio digunakan untuk menyimpan rasio terbesar yang ditemukan sejauh ini
            # min_index digunakan untuk menyimpan index dari diamond yang memiliki rasio terbesar
            if ratio > max_ratio:
                max_ratio = ratio
                min_index = i

        # Jika min_index tidak None, maka kita sudah menemukan dimaond dengan rasio terbesar
        # Maka kita set goal positionnya menjadi posisi dari diamond tersebut
        if min_index is not None:
            self.goal_position = board.diamonds[min_index].position
    
    # Fungsi ini digunakan untuk menyesuaikan goal position dari bot agar dapat terhindar dari obstacle (Dalam kasus ini adalah teleporter)
    def avoid_obstacle(self, board_bot: GameObject, board: Board):
        
        # Mendapatkan semua teleporter yang ada di board dengan melakukan iterasi untuk semua game object di board
        # dan menyeleksi game object dengan type "TeleporterGameObject"
        teleporters = [go for go in board.game_objects if go.type == "TeleporterGameObject"]
        
        # Jika tidak ada teleporter di board, maka langsung return
        if not teleporters:
            return

        # Jika ada teleporter maka akan diiterasi untuk masing-masing teleporter
        for teleporter in teleporters:
            # Ini akan melakukan pengecekan apakah bot berada dalam garis lurus antara teleporter dan goal position
            if self.is_in_line(board_bot.position, teleporter.position, self.goal_position):
                # Jika teleporter berada di kiri bot, maka goal positionnya akan diubah ke kanan bot
                if teleporter.position.x > board_bot.position.x:
                    self.goal_position.x = board_bot.position.x - 1
                # Jika teleporter berada di kanan bot, maka goal positionnya akan diubah ke kiri bot
                elif teleporter.position.x < board_bot.position.x:
                    self.goal_position.x = board_bot.position.x + 1
                # Jika teleporter berada di atas bot, maka goal positionnya akan diubah ke bawah bot
                if teleporter.position.y > board_bot.position.y:
                    self.goal_position.y = board_bot.position.y - 1
                # Jika teleporter berada di bawah bot, maka goal positionnya akan diubah ke atas bot
                elif teleporter.position.y < board_bot.position.y:
                    self.goal_position.y = board_bot.position.y + 1
    
    # Fungsi ini digunakan untuk mengecek apakah 3 posisi berada dalam satu garis lurus
    def is_in_line(self, pos1, pos2, pos3):
        # Mengkalkulasi perbedaan koordinat x dan y antara pos1 dan pos2
        dx1 = pos2.x - pos1.x
        dy1 = pos2.y - pos1.y

        # Setelah itu, dilakukan kalkulasi perbedaan koordinat x dan y antara pos2 dan pos3
        dx2 = pos3.x - pos2.x
        dy2 = pos3.y - pos2.y

        # Jika posisi berada dalam satu garis lurus, maka dx1, dx2, dy1, dan dy2 akan bernilai 0
        if dx1 == dx2 == 0:
            return True
        if dy1 == dy2 == 0:
            return True
           

        # Jika dx1 dan dx2 tidak 0, dan dy1/dx1 sama dengan dy2/dx2, maka posisi berada dalam satu garis lurus
        if dx1 != 0 and dx2 != 0 and dy1/dx1 == dy2/dx2:
            return True

        # Jika tidak memenuhi kondisi, maka posisi tidak berada dalam satu garis lurus
        return False

    # Fungsi ini digunakan untuk melakukan kalkulasi untuk gerakan selanjutnya dari bot
    def next_move(self, board_bot: GameObject, board: Board):

        # Mendapatkan properties dari bot
        props = board_bot.properties

        # Jika bot sudah mengumpulkan 5 diamond, maka goal positionnya adalah base
        if props.diamonds == 5:
            base = props.base
            self.goal_position = base
        
        else:
            # Memanggil metode go_home untuk mengecek apakah bot harus pulang ke base
            # Jika iya, maka goal positionnya adalah base
            self.go_home(board_bot, board)
            if self.goal_position is None:
                # Memanggil metode purge untuk mencari diamond dengan rasio terbesar
                # yang akan dijadikan goal position
                self.purge(board_bot,board)
    
        # Jika bot sudah mempunyai posisi goal, maka akan dihitung gerakan untuk mendekati posisi tersebut
        if self.goal_position:
            # Akan dipanggil fungsi avoid_obstacle untuk menyesuaikan posisi goal dari bot agar dapat terhindar dari obstacle
            self.avoid_obstacle(board_bot, board)

            # Mendapatkan posisi bot sekarang
            current_position = board_bot.position
            cur_x = current_position.x
            cur_y = current_position.y

            # Memanggil fungsi get_direction untuk mendapatkan delta x dan delta y yang akan digunakan untuk bergerak dari posisi sekarang ke posisi goal
            delta_x, delta_y = get_direction(
                cur_x,
                cur_y,
                self.goal_position.x,
                self.goal_position.y,
            )

            # Jika bot tidak bergerak semenjak langkah sebelumnya, maka botnya stuck
            if (cur_x, cur_y) == self.previous_position:

                # Cara bot keluar dari posisi stuck adalah dengan mencoba mengganti arah. Misalkan arah gerak sebelumnya ada horizontal,
                # maka akan dicoba gerak secara vertikal, dan sebaliknya
                if delta_x != 0:
                    delta_y = delta_x * self.turn_direction
                    delta_x = 0
                elif delta_y != 0:
                    delta_x = delta_y * self.turn_direction
                    delta_y = 0

                # Akan mengganti arah putaran untuk langkah selanjutnya
                self.turn_direction = -self.turn_direction

            # Akan menyimpan posisi sekarang sebagai previous position untuk langkah selanjutnya
            self.previous_position = (cur_x, cur_y)

            # Akan mengembalikan delta x dan delta y yang akan digunakan untuk bergerak
            return delta_x, delta_y

        # Jika bot tidak mempunyai posisi goal, maka akan mengembalikan 0, 0 yang berarti bot tidak akan bergerak
        return 0, 0