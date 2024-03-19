from typing import Tuple
from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from queue import Queue


def distance(a: Position, b: Position):
    return abs(a.x - b.x) + abs(a.y - b.y)


RETREAT_DELAY: int = 3


class DNALogic(BaseLogic):

    def __init__(self):
        self.board_bot = None
        self.board = None

    # Find the closest diamond to the current position
    def closest_diamond(self) -> Position:
        diamonds: list[Position] = []
        for d in self.board.diamonds:
            diamonds.append(d.position)

        def distance_to_bot(x: Position):
            return distance(x, self.board_bot.position)

        return min(diamonds, key=distance_to_bot)

    # Returns the position of the red diamonds worth 2 points each.
    def red_matrix(self) -> list[list[bool]]:
        matrix: list[list[bool]] = [[False for i in range(15)] for j in range(15)]
        for d in self.board.diamonds:
            if d.properties.points == 2:
                matrix[d.position.x][d.position.y] = True
        return matrix

    # Find distances to the goal using BFS taking teleporters into account.
    def distance_matrix(self, goal: Position) -> list[list[int]]:
        #
        # The key is how to model edges so that teleporters are taken into account
        # and all of the weights are equal so that we can use BFS.
        #
        # The graph is described as below:
        #  - Every cell in the 15 x 15 board is a vertex.
        #  - Every two adjacent cells that are not teleporters is connected by 2 directed edges in the opposite direction (of weight 1).
        #  - If a cell (a teleporter cell or not) is adjacent to another cell that is a teleporter cell,
        #    then there is a directed edge (of weight 1) between the cell and the *other* teleporter cell.
        #  - Every teleporter cell is connected to all adjacent non-teleporter cells.
        #
        # Note that since the board size is very small, we can efficiently iterate every cell in the board for every move.

        is_vulnerable: list[list[bool]] = [
            [False for i in range(15)] for j in range(15)
        ]

        # for enemy in self.board.bots:
        #     if enemy.id == self.board_bot.id:
        #         continue

        #     for dx in [-1, 0, 1]:
        #         for dy in [-1, 0, 1]:
        #             if (
        #                 (dx == 0 or dy == 0)
        #                 and 0 <= enemy.position.x + dx < 15
        #                 and 0 <= enemy.position.y + dy < 15
        #             ):
        #                 is_vulnerable[enemy.position.x + dx][
        #                     enemy.position.y + dy
        #                 ] = True

        first_teleporter, second_teleporter = None, None
        for teleport in self.board.game_objects:
            if teleport.type == "TeleportGameObject":
                if first_teleporter == None:
                    first_teleporter = teleport.position
                elif second_teleporter == None:
                    second_teleporter = teleport.position
                    break

        visited = [[False for i in range(15)] for j in range(15)]
        distance = [[999 for i in range(15)] for j in range(15)]
        visited[goal.x][goal.y] = True
        distance[goal.x][goal.y] = 0

        q: Queue[Tuple[int, int]] = Queue()
        q.put((goal.x, goal.y))

        while not q.empty():
            v = q.get()
            x, y = v[0], v[1]

            edges: list[Tuple[int, int]] = []
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if (
                        ((dx == 0) ^ (dy == 0))
                        and 0 <= x + dx < 15
                        and 0 <= y + dy < 15
                    ):
                        if is_vulnerable[x + dx][y + dy]:
                            continue

                        is_first_teleporter = (
                            Position(y + dy, x + dx) == first_teleporter
                        )
                        is_second_teleporter = (
                            Position(y + dy, x + dx) == second_teleporter
                        )
                        if is_first_teleporter:
                            edges.append((second_teleporter.x, second_teleporter.y))
                        elif is_second_teleporter:
                            edges.append((first_teleporter.x, first_teleporter.y))
                        else:
                            edges.append((x + dx, y + dy))

            for edge in edges:
                if not visited[edge[0]][edge[1]]:
                    visited[edge[0]][edge[1]] = True
                    distance[edge[0]][edge[1]] = distance[x][y] + 1
                    q.put(edge)

        return distance

    def next_move(self, board_bot: GameObject, board: Board):
        self.board_bot = board_bot
        self.board = board

        cur_pos, base = board_bot.position, board_bot.properties.base
        closest_diamond = self.closest_diamond()
        is_red = self.red_matrix()

        goal: Position
        if (
            board_bot.properties.diamonds == board_bot.properties.inventory_size
            or distance(cur_pos, closest_diamond)
            + distance(closest_diamond, base)
            + RETREAT_DELAY
            > (board_bot.properties.milliseconds_left) / 1000.0
            or (
                board_bot.properties.diamonds == board_bot.properties.inventory_size - 1
                and is_red[closest_diamond.x][closest_diamond.y]
            )
        ):
            goal = base
        else:
            goal = closest_diamond

        distance_matrix = self.distance_matrix(goal)
        closest_cell, ideal_direction = 99999, None
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if (
                    ((dx == 0) ^ (dy == 0))
                    and 0 <= cur_pos.x + dx < 15
                    and 0 <= cur_pos.y + dy < 15
                ):
                    if closest_cell > distance_matrix[cur_pos.x + dx][cur_pos.y + dy]:
                        closest_cell = distance_matrix[cur_pos.x + dx][cur_pos.y + dy]
                        ideal_direction = (dx, dy)

        return ideal_direction
