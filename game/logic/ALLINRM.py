from ..util import get_direction
from game.models import Board, GameObject, Properties

class Manhattan(object):
    def __init__(self):
        self.goal_position = None
        self.previous_position = (None, None)
        self.turn_direction = 1
        self.teleporter_visits = {}
        self.button_pressed = False

    def next_move(self, board_bot: GameObject, board: Board):
        # Dapatkan properti dari board
        props = board_bot.properties

        # Kumpulkan teleporter dan button yang berada di board
        teleporter = [obj for obj in board.game_objects if obj.type == "TeleportGameObject"]
        button = [obj for obj in board.game_objects if obj.type == "DiamondButtonGameObject"]
        
        # Hitung jarak antara bot dengan base
        base = props.base
        xDist_base = abs(board_bot.position.x - base.x)
        yDist_base = abs(board_bot.position.y - base.y)
        distance_base = xDist_base + yDist_base

        # Apabila bot memiliki 5 diamond, atau bot memiliki 3 sampai 4 diamond tetapi dekat ke base, atau waktu tersisa kurang dari 5 detik, maka jadikan base sebagai tujuan
        if (props.diamonds == 5 or props.milliseconds_left == 5000 or props.milliseconds_left == 3000) or (props.diamonds in [3, 4] and distance_base <= 3):
            self.goal_position = base

        else:
            max_score = -1
            target = None

            # Cari letak diamond
            for diamond in board.diamonds:
                if (board_bot.properties.diamonds + diamond.properties.points > 5):
                    continue
                # Hitung density diamond terhadap bot dengan pembagian jarak berdasarkan jarak manhattan dengan bobot diamond
                xDist = abs(board_bot.position.x - diamond.position.x)
                yDist = abs(board_bot.position.y - diamond.position.y)
                distance = xDist + yDist
                score = diamond.properties.points / distance

                # Diamond dengan density terbesar dijadikan target oleh bot untuk didatangi
                if (score > max_score):
                    max_score = score
                    target = diamond

            # Interaksi dengan bot lain
            for other_bot in board.bots:
                if other_bot.id == board_bot.id:
                    continue
                
                # Menghitung jarak bot dengan bot lain menggunakan jarak manhattan
                xDist = abs(board_bot.position.x - other_bot.position.x)
                yDist = abs(board_bot.position.y - other_bot.position.y)
                distance = xDist + yDist
                
                # Apabila jarak bot lain secara manhattan dibawah satu dan can_tackle bernilai true, maka jadikan bot lain sebagai target
                if distance <= 1 and props.can_tackle:
                    target = other_bot

            # Interaksi dengan button
            for btn in button:
                # Hitung jarak button dengan bot menggunakan jarak manhattan
                xDist = abs(board_bot.position.x - btn.position.x)
                yDist = abs(board_bot.position.y - btn.position.y)
                distance = xDist + yDist
                
                # Jika jarak button kurang dari 1 dan button belum terpencet, maka jadikan button sebagai target bot
                if distance <= 1 and not self.button_pressed:
                    target = btn
                    self.button_pressed = True

            if target is not None:
                self.goal_position = target.position


        # Sesuaikan arah pergerakan bot, khususnya untuk gerak berbelok
        if self.goal_position:
            current_position = board_bot.position
            cur_x = current_position.x
            cur_y = current_position.y
            delta_x, delta_y = get_direction(
                cur_x,
                cur_y,
                self.goal_position.x,
                self.goal_position.y,
            )

            # Interaksi dengan teleport
            for tp in teleporter:
                if tp.position.x == cur_x + delta_x and tp.position.y == cur_y + delta_y:
                    # Bila sudah sekali masuk ke teleporter koordinat tertentu, maka tidak bisa masuk lagi
                    if self.teleporter_visits.get(tp.id, 0) >= 2:
                        delta_x, delta_y = -delta_x, -delta_y
                        break
                    else:
                        self.teleporter_visits[tp.id] = self.teleporter_visits.get(tp.id, 0) + 1

            if (cur_x, cur_y) == self.previous_position:
                if delta_x != 0:
                    delta_y = delta_x * self.turn_direction
                    delta_x = 0
                elif delta_y != 0:
                    delta_x = delta_y * self.turn_direction
                    delta_y = 0
                self.turn_direction = -self.turn_direction

            self.previous_position = (cur_x, cur_y)
            # Kembalikan nilai delta x dan delta y untuk pergerakan bot
            return delta_x, delta_y

        return 0, 0