from typing import Optional, List

from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from ..util import get_direction


class Drive2011(BaseLogic):
    def __init__(self):
        self.directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        self.goal_position: Optional[Position] = None
        self.current_direction = 0

    # Memilih arah pergerakan selanjutnya
    def next_move(self, board_bot: GameObject, board: Board):

        props = board_bot.properties
        current_position = board_bot.position
        base = board_bot.properties.base

        # jika diamonds sudah 5, pulang ke base
        if props.diamonds == 5:
            target_teleport_position, is_using_teleport = self.using_teleport(
                board_bot, board
            )
            # Apabila lebih baik menggunakan teleport
            if is_using_teleport:
                self.goal_position = target_teleport_position
            else:
                self.goal_position = base

        else:
            # Jika tidak ada tujuan spesifik, pilih langkah terbaik (greedy)
            goal_from_base, min_distance_base = self.nearest_diamond_from_base(
                board_bot, board
            )
            goal_from_player, min_distance_player = self.nearest_diamond_from_bot(
                board_bot, board
            )
            min_distance = min(min_distance_base, min_distance_player)
            goal_button, is_using_button = self.using_button(
                board_bot, board, min_distance
            )

            # Apabila tersisa 7 detik terakhir, Langsung pulang ke base
            if board_bot.properties.milliseconds_left < 7000:
                if min_distance_base <= 2:
                    self.goal_position = goal_from_base
                else:
                    self.goal_position = base
            # Apabila interval waktu 7-15 detik tersisa, cari diamond terdekat dari base
            elif (
                board_bot.properties.milliseconds_left >= 7000
                and board_bot.properties.milliseconds_left < 15000
            ):
                if min_distance_base <= 5:
                    self.goal_position = goal_from_base
                else:
                    self.goal_position = base
            # Apabila waktu tersisa > 15 detik, cari diamond terdekat dari base atau tekan button
            else:
                if is_using_button:
                    self.goal_position = goal_button
                else:
                    self.goal_position = goal_from_player

        if self.goal_position:
            # Arahkan ke posisi tujuan
            delta_x, delta_y = get_direction(
                current_position.x,
                current_position.y,
                self.goal_position.x,
                self.goal_position.y,
            )

        return delta_x, delta_y

    # jarak diamond terdekat dengan bot
    def nearest_diamond_from_bot(self, board_bot: GameObject, board: Board):
        diamonds = board.diamonds
        if board_bot.properties.diamonds == 4:
            blue_diamonds = [
                diamond for diamond in diamonds if diamond.properties.points == 1
            ]
            if len(blue_diamonds) > 0:
                current_position = board_bot.position
                distances = [
                    abs(current_position.x - diamond.position.x)
                    + abs(board_bot.position.y - diamond.position.y)
                    for diamond in blue_diamonds
                ]
                nearest_diamond_index = distances.index(min(distances))
                diamond_from_bot = blue_diamonds[nearest_diamond_index].position
                min_distance_diamond_bot = distances[nearest_diamond_index]
            else:
                diamond_from_bot = board_bot.properties.base
            return diamond_from_bot, min_distance_diamond_bot
        else:
            diamonds = [diamond for diamond in diamonds]
            current_position = board_bot.position
            distances = [
                abs(current_position.x - diamond.position.x)
                + abs(board_bot.position.y - diamond.position.y)
                for diamond in diamonds
            ]
            nearest_diamond_index = distances.index(min(distances))
            diamond_from_bot = diamonds[nearest_diamond_index].position
            min_distance_diamond_bot = distances[nearest_diamond_index]
            return diamond_from_bot, min_distance_diamond_bot

    # jarak diamond terdekat dengan base
    def nearest_diamond_from_base(self, board_bot: GameObject, board: Board):
        # Check for diamonds
        base = board_bot.properties.base
        min_distance_diamond_base = 100000
        if board_bot.properties.diamonds == 4:
            for gameObjects in board.game_objects:
                if (
                    gameObjects.type == "DiamondGameObject"
                    and gameObjects.properties.points == 1
                ):
                    diamond_distance = abs(gameObjects.position.x - base.x) + abs(
                        gameObjects.position.y - base.y
                    )
                    if diamond_distance < min_distance_diamond_base:
                        min_distance_diamond_base = diamond_distance
                        diamond_from_base = gameObjects.position
            return diamond_from_base, min_distance_diamond_base
        else:
            for diamond in board.diamonds:
                diamond_distance = abs(diamond.position.x - base.x) + abs(
                    diamond.position.y - base.y
                )
                if diamond_distance < min_distance_diamond_base:
                    min_distance_diamond_base = diamond_distance
                    diamond_from_base = diamond.position
            return diamond_from_base, min_distance_diamond_base

    # jarak terdekat bot lawan
    def chasing_enemy(self, board_bot: GameObject, board: Board, diamond_distance):
        min_distance_enemy = 100000
        current_position = board_bot.position
        nearest_enemy_position = None
        for enemy_bot in board.bots:
            if enemy_bot != board_bot:
                if 5 * enemy_bot.properties.diamonds >= diamond_distance:
                    if (
                        abs(enemy_bot.position.x - current_position.x)
                        + abs(enemy_bot.position.y - current_position.y)
                        < min_distance_enemy
                    ):
                        min_distance_enemy = abs(
                            enemy_bot.position.x - current_position.x
                        ) + abs(enemy_bot.position.y - current_position.y)
                        nearest_enemy_position = enemy_bot.position
        return nearest_enemy_position, min_distance_enemy

    # gunakan teleport saat pulang ke base (diamond sudah berjumlah 5)
    def using_teleport(self, board_bot: GameObject, board: Board):
        is_using_teleport = False
        base = board_bot.properties.base
        current_position = board_bot.position
        teleport_objects: List[Position] = []

        for game_object in board.game_objects:
            if game_object.type == "TeleportGameObject":
                teleport_objects.append(game_object.position)

        distance_teleport_first_from_bot = abs(
            teleport_objects[0].x - current_position.x
        ) + abs(teleport_objects[0].y - current_position.y)
        distance_teleport_second_from_bot = abs(
            teleport_objects[1].x - current_position.x
        ) + abs(teleport_objects[1].y - current_position.y)
        distance_teleport_first_from_base = abs(teleport_objects[0].x - base.x) + abs(
            teleport_objects[0].y - base.y
        )
        distance_teleport_second_from_base = abs(teleport_objects[1].x - base.x) + abs(
            teleport_objects[1].y - base.y
        )
        distance_bot_from_base = abs(current_position.x - base.x) + abs(
            current_position.y - base.y
        )

        if distance_teleport_first_from_bot <= distance_teleport_second_from_bot:
            if (
                distance_teleport_first_from_bot + distance_teleport_second_from_base
            ) <= distance_bot_from_base:
                is_using_teleport = True
                return teleport_objects[0], is_using_teleport
            else:
                return None, is_using_teleport

        else:
            if (
                distance_teleport_second_from_bot + distance_teleport_first_from_base
            ) <= distance_bot_from_base:
                is_using_teleport = True
                return teleport_objects[1], is_using_teleport
            else:
                return None, is_using_teleport

    # menggunakan button jika posisi diamonds jauh dari bot sehingga memungkinkan bot memperoleh diamond lebih dekat
    def using_button(self, board_bot: GameObject, board: Board, min_distance: int):
        current_position = board_bot.position
        button_position: List[Position] = []

        for game_object in board.game_objects:
            if game_object.type == "DiamondButtonGameObject":
                button_position.append(game_object.position)
                break

        distance_bot_button = abs(current_position.x - button_position[0].x) + abs(
            current_position.y - button_position[0].y
        )

        if min_distance > 5 and distance_bot_button < min_distance:
            is_using_button = True
        else:
            is_using_button = False

        return button_position[0], is_using_button

    # jarak terdekat bot lawan
    def attack(self, board_bot: GameObject, board: Board):
        enemy_bot_position: List[Position] = []
        is_tackle = False
        for enemy_bot in board.bots:
            if enemy_bot != board_bot:
                diff_x = abs(enemy_bot.position.x - board_bot.position.x)
                diff_y = abs(enemy_bot.position.y - board_bot.position.y)
                if (enemy_bot.position.x == board_bot.position.x and diff_y == 1) or (
                    enemy_bot.position.y == board_bot.position.y and diff_x == 1
                ):
                    enemy_bot_position.append(enemy_bot.position)

        if len(enemy_bot_position) > 0:
            is_tackle = True

        # target kotak biar ga ditackle
        if is_tackle:
            return enemy_bot_position[0], is_tackle

        else:
            return None, is_tackle

    # jarak terdekat bot lawan
    def defend(self, board_bot: GameObject, board: Board):
        enemy_bot_position: List[Position] = []
        is_tackle = False
        for enemy_bot in board.bots:
            if enemy_bot != board_bot:
                diff_x = abs(enemy_bot.position.x - board_bot.position.x)
                diff_y = abs(enemy_bot.position.y - board_bot.position.y)
                if (enemy_bot.position.x == board_bot.position.x and diff_y == 1) or (
                    enemy_bot.position.y == board_bot.position.y and diff_x == 1
                ):
                    enemy_bot_position.append(enemy_bot.position)

        if len(enemy_bot_position) > 0:
            is_tackle = True

        # target kotak biar ga ditackle
        if is_tackle:
            if enemy_bot_position[0].x == board_bot.position.x:
                return (
                    Position(board_bot.position.y, board_bot.position.x + 1),
                    is_tackle,
                )

            elif enemy_bot_position[0].y == board_bot.position.y:
                return (
                    Position(board_bot.position.y + 1, board_bot.position.x),
                    is_tackle,
                )

        else:
            return None, is_tackle
