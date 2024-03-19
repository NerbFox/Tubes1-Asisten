import random
from typing import Optional

from ..logic.base import BaseLogic
from ..models import Bot, GameObject, Board, Position

# from ..util import get_direction
import threading


def get_dist(pa: Position, pb: Position) -> int:
    return abs(pa.x - pb.x) + abs(pa.y - pb.y)


class Processor:
    def __init__(self):
        pass


class ButtonProcessor:
    bot: Bot
    further_but_not_far_enough = 50
    closer = 30
    find_rad = 4

    def get_bot_pos(self, board: Board) -> (int, int):
        for game_object in board.game_objects:
            if game_object.type == "BotGameObject" and game_object.id == self.bot.id:
                return game_object.position.x, game_object.position.y
        return -1, -1

    def __init__(self):
        pass

    def eval_button(
        self, dist_but: int, dist_dia: int, likelihood: int, multiplier: int
    ) -> int:
        return likelihood + multiplier * (dist_dia - dist_but)

    def process(
        self, board_bot: GameObject, board: Board
    ) -> list[tuple[int, Position]]:
        funcGO = lambda x, y: abs(x.x - y.x) + abs(x.y - y.y)
        closestDiamonds = list(
            filter(
                lambda g: g.type == "DiamondGameObject"
                and funcGO(g.position, board_bot.position) <= self.find_rad,
                board.game_objects,
            )
        )
        num_of_dia = len(closestDiamonds)
        buttonNow: list[GameObject] = list(
            filter(
                lambda g: g.type == "DiamondButtonGameObject"
                and funcGO(g.position, board_bot.position) <= self.find_rad,
                board.game_objects,
            )
        )
        num_button: int = len(buttonNow)
        if num_button == 0:
            return []
        multiplier = 0
        likelihood = 0
        invNow = board_bot.properties.diamonds
        if invNow == 0:
            likelihood = 100
        elif invNow == 1:
            likelihood = 70
            multiplier = 20
        elif invNow == 2:
            likelihood = 30
            multiplier = 30
        elif invNow >= 3:
            likelihood = 10
        dist_dia = 5
        dist_but = funcGO(buttonNow[0].position, board_bot.position)
        if num_of_dia != 0:
            nearest_dia = min(
                closestDiamonds, key=lambda g: funcGO(g.position, board_bot.position)
            )
            dist_dia = funcGO(nearest_dia.position, board_bot.position)
        return [
            (
                self.eval_button(dist_but, dist_dia, likelihood, multiplier),
                buttonNow[0].position,
            )
        ]


class DiamondProcessor(Processor):
    def __init__(self):
        self.take_n = 4
        self.rad_consider = 3
        self.return_diamond = 2
        self.prio_dia = [
            0,
            100,
            90,
            85,
            80,
            75,
            51,
            30,
            20,
            10,
            9,
            8,
            7,
            6,
            5,
            4,
            3,
            2,
            1,
        ]
        super().__init__()

    """
    def isInventoryRed(self, board_bot: GameObject) -> bool:
        if(board_bot.properties.diamonds == 4):
            return True
        else:
            return False

    def redDiamond(self, arr: list[GameObject]) -> list[GameObject]: 
        ans = []
        for i in arr: 
            if(i.properties.points == 2): 
                ans.append(i)
        return ans
    
    def blueDiamond(self, arr: list[GameObject]) -> list[GameObject]: 
        ans = [] 
        for i in arr: 
            if(i.properties.points == 1): 
                ans.append(i) 
        return ans

    def eval_elem(self, diamond: GameObject, diamonds: list[GameObject]):
        cnt: int = 0
        for d in diamonds:
            if abs(d.position.x - diamond.position.x) + abs(d.position.y - diamond.position.y) <= self.rad_consider:
                cnt += 1
        return cnt
    """

    def nearestDiamond(
        self, diamonds: list[GameObject], board_bot: GameObject
    ) -> list[GameObject]:
        diamonds.sort(
            key=lambda g: abs(g.position.x - board_bot.position.x)
            + abs(g.position.y - board_bot.position.y)
        )
        first_n_elem = diamonds[: self.take_n]
        # first_n_elem.sort(key=lambda g: self.eval_elem(g, diamonds), reverse=True)
        return first_n_elem[: self.return_diamond]

    def process(
        self, board_bot: GameObject, board: Board
    ) -> Optional[list[tuple[int, Position]]]:
        # diamonds = [game_object for game_object in board.game_objects if game_object.type == "DiamondGameObject"]
        diamonds = list(
            filter(lambda x: x.type == "DiamondGameObject", board.game_objects)
        )
        if not diamonds:
            return []
        if board_bot.properties is not None:
            if board_bot.properties.diamonds == 4:
                diamonds = list(filter(lambda x: x.properties.points == 1, diamonds))
        processed: list[GameObject] = self.nearestDiamond(diamonds, board_bot)
        return [
            (
                self.prio_dia[
                    abs(game_object.position.x - board_bot.position.x)
                    + abs(game_object.position.y - board_bot.position.y)
                ],
                game_object.position,
            )
            for game_object in processed
            if abs(game_object.position.x - board_bot.position.x)
            + abs(game_object.position.y - board_bot.position.y)
            < len(self.prio_dia)
        ]


class GoHomeProcessor(Processor):
    def __init__(self):
        super().__init__()

    def calc_prio(
        self, dist_home, dist_dia, multiplier, likelihood, notCalled=False
    ) -> int:
        constant = 20
        if likelihood == 100 and not notCalled:
            return 500
        if not notCalled:
            return likelihood + multiplier * (dist_dia - dist_home)
        else:
            return likelihood + multiplier * (dist_dia - dist_home - constant)

    def process(
        self, board_bot: GameObject, board: Board, dtl: int = 0, calledfromtele=False
    ) -> list[tuple[int, Position]]:
        home_pos: Position = board_bot.properties.base
        diamonds = list(
            filter(lambda x: x.type == "DiamondGameObject", board.game_objects)
        )
        inv_now: int = board_bot.properties.diamonds
        # no diamond, store ke base aja
        if not diamonds:
            return [(inv_now * 100, home_pos)]  # kalo inventory = 0 gak ngaruh
        secLeft: int = board_bot.properties.milliseconds_left // 1000
        # kalo waktu dikit -> pulang, takut mubazir, ambil diamond deket base aja
        if secLeft - get_dist(home_pos, board_bot.position) <= 1 and not calledfromtele:
            return [(501, home_pos)]
        likelihood: int = 0
        multiplier: int = 0
        # print("INV_NOW", inv_now)
        if inv_now == 1:
            likelihood = 10
            multiplier = 18
        elif inv_now == 2:
            likelihood = 40
            multiplier = 20
        elif inv_now == 3:
            likelihood = 75
        elif inv_now == 4:
            likelihood = 90
        elif inv_now == 5:
            likelihood = 100
        nearest_diamond: GameObject = min(
            diamonds, key=lambda y: get_dist(y.position, board_bot.position)
        )
        dist_dia: int = get_dist(nearest_diamond.position, board_bot.position)
        dist_home: int = get_dist(home_pos, board_bot.position)
        priority_home = self.calc_prio(
            dist_home + dtl, dist_dia + dtl, multiplier, likelihood, calledfromtele
        )
        if priority_home <= 0:
            return []
        return [(priority_home, home_pos)]


class Processor:

    def __init__(self):
        pass


class Teleporter(Processor):
    def __init__(self):
        super().__init__()
        self.DiamondProcessor: DiamondProcessor = DiamondProcessor()
        self.GoHomeProcessor: GoHomeProcessor = GoHomeProcessor()
        self.multiplier = 2

    """
    def teleportPosition(self, board: Board) -> list[GameObject]:
        teleporter: list[GameObject] = []

        for game_object in board.game_objects:
            if game_object.type == "TeleportGameObject":
                teleporter.append(game_object)
        return teleporter

    # bot teleport
    def nearTeleport(self, teleporter: list[GameObject], board_bot: GameObject) -> tuple[int, Position]:
        closestTeleport = min(
            teleporter,
            key = lambda x: abs(x.position.x - board_bot.position.x) + abs(x.position.y - board_bot.position.y)
        )
        dist: int = abs(closestTeleport.position.x - board_bot.position.x) + abs(closestTeleport.position.y - board_bot.position.y)
        return dist, closestTeleport.position

    # nearest diamond teleport
    def nearTeleDia(self, teleporter: list[GameObject], diamond: list[GameObject]) -> tuple[int, GameObject, GameObject]:
        closestTeleport1 = min(
            diamond,
            key= lambda x: abs(teleporter[0].position.x - x.position.x) + abs(teleporter[0].position.y - x.position.y)
        )

        closestTeleport2 = min(
            diamond,
            key= lambda x: abs(teleporter[1].position.x - x.position.x) + abs(teleporter[1].position.y - x.position.y)
        )

        nearTele1: int = abs(closestTeleport1.position.x - teleporter[0].position.x) + abs(closestTeleport1.position.y - teleporter[0].position.y)
        nearTele2: int = abs(closestTeleport2.position.x - teleporter[1].position.x) + abs(closestTeleport2.position.y - teleporter[1].position.y)

        if(nearTele1 < nearTele2):
            return nearTele1, closestTeleport1, teleporter[0]
        else:
            return nearTele2, closestTeleport1, teleporter[1]


    def TeleOrDia(self, botTele: tuple[int, Position], nearestDia: tuple[int, Position], nearestTele: tuple[int, GameObject, GameObject]) -> tuple[int, Position]:
        distDia  = nearestDia[0]
        distTele: int = botTele[0] + nearestTele[0]

        if(distDia > distTele):
            return 1000, botTele[1]
    """

    def process(
        self, board_bot: GameObject, board: Board, maxi_val: int, dist_to_home: int
    ) -> list[tuple[int, Position]]:
        teleporter = list(
            filter(lambda x: x.type == "TeleportGameObject", board.game_objects)
        )
        diamonds = list(
            filter(lambda x: x.type == "DiamondGameObject", board.game_objects)
        )
        if not teleporter:
            return []
        tele1, tele2 = teleporter
        # tele_obj1, tele_obj2 = GameObject(0, tele1.position, ""), GameObject(0, tele2.position, "")
        funcGO = lambda x, y: abs(x.position.x - y.position.x) + abs(
            x.position.y - y.position.y
        )
        minDia1 = min(diamonds, key=lambda x: funcGO(x, tele1))
        minDia2 = min(diamonds, key=lambda x: funcGO(x, tele2))
        dtl1 = funcGO(tele1, board_bot)
        dtl2 = funcGO(tele2, board_bot)
        if funcGO(minDia1, tele1) + dtl2 >= len(self.DiamondProcessor.prio_dia):
            max1 = -1
        else:
            max1 = self.DiamondProcessor.prio_dia[funcGO(minDia1, tele1) + dtl2]
        if funcGO(minDia2, tele2) + dtl1 >= len(self.DiamondProcessor.prio_dia):
            max2 = -1
        else:
            max2 = self.DiamondProcessor.prio_dia[funcGO(minDia2, tele2) + dtl1]
        ans = []
        if max1 > 0 and max1 > maxi_val and max1 >= max2:
            ans.append((max1, tele2.position))
        if max2 > 0 and max2 > maxi_val and max2 > max1:
            ans.append((max2, tele1.position))
        tele1GO = GameObject(
            board_bot.id, tele1.position, board_bot.type, board_bot.properties
        )
        tele2GO = GameObject(
            board_bot.id, tele2.position, board_bot.type, board_bot.properties
        )
        prio_h_through_tele1 = self.GoHomeProcessor.process(tele1GO, board, dtl1, True)
        prio_h_through_tele2 = self.GoHomeProcessor.process(tele2GO, board, dtl2, True)
        if prio_h_through_tele1:
            ans.append((prio_h_through_tele1[0][0], tele1.position))
        if prio_h_through_tele2:
            ans.append((prio_h_through_tele2[0][0], tele2.position))
        return ans


class SelfDefense(Processor):
    def __init__(self):
        super().__init__()
        self.directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        self.goal_position: Optional[Position] = None
        self.current_direction = 0

    """
    def run(self, board_bot: GameObject, board: Board, nearest: int) -> list[tuple[int, Position]]:
        wrong_move: list[tuple[int, Position]] = []
        added_ind: list[int] = [False, False, False, False]
        for game_object in board.bots:
            if abs(board_bot.position.x - game_object.position.x) + \
                    abs(board_bot.position.y - game_object.position.y) == nearest:
                for ind in range(4):
                    if added_ind[ind]:
                        continue
                    dir_x, dir_y = self.directions[ind]
                    if abs(board_bot.position.x + dir_x - game_object.position.x) + \
                            abs(board_bot.position.y + dir_y - game_object.position.y) < nearest:
                        wrong_move.append((-1, Position(dir_y, dir_x)))
                        added_ind[ind] = True
        return wrong_move


    def attack(self, board_bot: GameObject, nearest_enemy: GameObject) -> tuple[int, Position]:
        return 1000, nearest_enemy.position

    def threatened(self, board_bot: GameObject, nearest_enemy: GameObject) -> int:
        distance = abs(nearest_enemy.position.x - board_bot.position.x) + abs(
            nearest_enemy.position.y - board_bot.position.y)
        return distance
    """

    def process(self, board_bot: GameObject, board: Board):
        props = board_bot.properties
        # Analyze new state
        # Check safety
        if len(board.bots) == 1:
            return []
        func_dist = lambda x, y: abs(x.position.x - y.position.x) + abs(
            x.position.y - y.position.y
        )
        dist_one = list(
            filter(
                lambda x: func_dist(x, board_bot) == 1
                and (
                    x.position.x != x.properties.base.x
                    or x.position.y != x.properties.base.y
                ),
                board.bots,
            )
        )
        if dist_one:
            maxWithDia = max(dist_one, key=lambda x: x.properties.diamonds)
            # move_at = Position(maxWithDia.position.y - board_bot.position.y, maxWithDia.position.x - board_bot.position.x, )
            return [(-2, maxWithDia)]
        return []
        """
        dist_two = list(filter(lambda x: func_dist(x, board_bot) == 2, board.bots))
        if not dist_two:
            # Safe, return nothing
            return []
        restricted_move = []
        for dir_x, dir_y in self.directions:
            new_hyp_pos = GameObject(-1, Position(dir_x + board_bot.position.x, dir_y + board_bot.position.y), "", None)
            ex = False
            for bots in dist_two:
                if func_dist(new_hyp_pos, bots) == 1:
                    ex = True
                    break
            if ex:
                restricted_move.append((-1, Position(dir_x, dir_y)))
        return restricted_move
        """


class TBD(BaseLogic):
    def __init__(self):
        self.directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        self.goal_position: Optional[Position] = None
        self.memory_wrong_move = []
        self.current_direction = 0
        self.SelfDefenseProcessor: SelfDefense = SelfDefense()
        self.DiamondProcessor: DiamondProcessor = DiamondProcessor()
        self.TeleportProcessor: Teleporter = Teleporter()
        self.GoHomeProcessor: GoHomeProcessor = GoHomeProcessor()
        self.ButtonProcessor: ButtonProcessor = ButtonProcessor()
        self.TackleCounter = 0
        self.TackleTarget = None
        self.OldPos: Optional[Position] = None
        self.Turned = False
        self.pos_turned = False

    def no_obstacle(
        self, dist_x, dist_y, pos_fr: Position, pos_to: Position, board: Board
    ):
        teleporter = [
            game_object.position
            for game_object in list(
                filter(lambda x: x.type == "TeleportGameObject", board.game_objects)
            )
        ]
        but_l = [
            game_object.position
            for game_object in list(
                filter(
                    lambda x: x.type == "DiamondButtonGameObject", board.game_objects
                )
            )
        ]
        if pos_to in teleporter or pos_to in but_l:
            return True
        func_dist = lambda x, y: abs(x.x - y.x) + abs(x.y - y.y)
        same_x, same_y = -1, -1
        min_x, max_x, min_y, max_y = -1, -1, -1, -1
        if dist_y == 0:
            same_y = pos_fr.y
            min_x = min(pos_fr.x, pos_to.x)
            max_x = max(pos_fr.x, pos_to.x)
            same_x = pos_to.x
            min_y = min(pos_fr.y, pos_to.y)
            max_y = max(pos_fr.y, pos_to.y)
        else:
            same_y = pos_to.y
            min_x = min(pos_fr.x, pos_to.x)
            max_x = max(pos_fr.x, pos_to.x)
            same_x = pos_fr.x
            min_y = min(pos_fr.y, pos_to.y)
            max_y = max(pos_fr.y, pos_to.y)
        teleporter.extend(but_l)
        for obs in teleporter:
            if func_dist(obs, pos_fr) <= 2 and (
                (obs.x == same_x and min_y <= obs.y <= max_y)
                or (obs.y == same_y and min_x <= obs.x <= max_x)
            ):
                self.pos_turned = True
                return False
            elif (
                func_dist(obs, pos_fr) == 3
                and (
                    (obs.x == same_x and min_y <= obs.y <= max_y)
                    or (obs.y == same_y and min_x <= obs.x <= max_x)
                )
                and self.Turned
            ):
                return True
        return True

    def next_move(self, board_bot: GameObject, board: Board):
        wrong_moves = [False, False, False, False]
        self.pos_turned = False
        for wr in self.memory_wrong_move:
            wrong_moves[wr] = True
        self.memory_wrong_move = []
        possible_moves: list[tuple[int, Position]] = []
        listSelfD = self.SelfDefenseProcessor.process(board_bot, board)
        if len(listSelfD) > 0 and listSelfD[0][0] == -2:
            if (
                (
                    self.TackleTarget is not None
                    and self.TackleTarget == listSelfD[0][1].properties.name
                    and self.TackleCounter == 0
                )
                or self.TackleTarget is None
                or self.TackleTarget != listSelfD[0][1].properties.name
            ):
                self.TackleTarget = listSelfD[0][1].properties.name
                self.TackleCounter += 1
                # print(self.TackleTarget, self.TackleCounter)
                self.goal_position = None
                self.OldPos = board_bot.position
                return (
                    listSelfD[0][1].position.x - board_bot.position.x,
                    listSelfD[0][1].position.y - board_bot.position.y,
                )
        self.TackleTarget = None
        self.TackleCounter = 0
        listDia = self.DiamondProcessor.process(board_bot, board)
        listGoHome = self.GoHomeProcessor.process(board_bot, board)
        listButton = self.ButtonProcessor.process(board_bot, board)
        possible_moves.extend(listDia)
        possible_moves.extend(listGoHome)
        possible_moves.extend(listButton)
        if not listDia:
            score_dia = 0
        else:
            score_dia = listDia[0][0]
        if not listGoHome:
            dist = 0
        else:
            dist = listGoHome[0][0]
        possible_moves.extend(
            self.TeleportProcessor.process(board_bot, board, score_dia, dist)
        )
        # print(possible_moves)
        # print(board_bot.properties.diamonds)
        """
                for prio, pos in possible_moves:
            if prio == -1:
                for ind in range(4):
                    dir_x, dir_y = self.directions[ind]
                    if pos.x == dir_x and pos.y == dir_y:
                        wrong_moves[ind] = True
            else:
                real_moves.append((prio, pos))
        
        """
        cnt_wrong_mv = 0
        if board_bot.position.x == 14:
            wrong_moves[0] = True
            cnt_wrong_mv += 1
        if board_bot.position.x == 0:
            wrong_moves[2] = True
            cnt_wrong_mv += 1
        if board_bot.position.y == 14:
            wrong_moves[1] = True
            cnt_wrong_mv += 1
        if board_bot.position.y == 0:
            wrong_moves[3] = True
            cnt_wrong_mv += 1
        real_moves: list[tuple[int, Position]] = list(
            filter(lambda x: x[0] != -1, possible_moves)
        )
        real_moves.append((10, board_bot.properties.base))
        """
        minOnes = list(filter(lambda x: x[0] == -1, possible_moves))
        for noMove in minOnes:
            if noMove == self.directions[0] and not wrong_moves[0]:
                wrong_moves[0] = True
                cnt_wrong_mv += 1
            elif noMove == self.directions[1] and not wrong_moves[1]:
                wrong_moves[1] = True
                cnt_wrong_mv += 1
            elif noMove == self.directions[2] and not wrong_moves[2]:
                wrong_moves[2] = True
                cnt_wrong_mv += 1
            elif noMove == self.directions[3] and not wrong_moves[3]:
                wrong_moves[3] = True
                cnt_wrong_mv += 1
        """
        real_moves.sort(key=lambda x: x[0], reverse=True)
        teleporter = [
            game_object.position
            for game_object in list(
                filter(lambda x: x.type == "TeleportGameObject", board.game_objects)
            )
        ]
        but_l = [
            game_object.position
            for game_object in list(
                filter(
                    lambda x: x.type == "DiamondButtonGameObject", board.game_objects
                )
            )
        ]
        # print(possible_moves)
        # print(real_moves)
        # print(wrong_moves)
        # print(board_bot.position)
        # print(board_bot.position.x, board_bot.position.y)
        # print(board_bot.properties.diamonds)
        for prio, pos in real_moves:
            for ind in range(4):
                pos_turned = False
                if wrong_moves[ind]:
                    continue
                dist_x, dist_y = self.directions[ind]
                cur_dist = abs(board_bot.position.x - pos.x) + abs(
                    board_bot.position.y - pos.y
                )
                after_dist = abs(board_bot.position.x + dist_x - pos.x) + abs(
                    board_bot.position.y + dist_y - pos.y
                )
                pos_after = Position(
                    board_bot.position.y + dist_y, board_bot.position.x + dist_x
                )
                if after_dist < cur_dist:
                    if not self.no_obstacle(
                        dist_x, dist_y, board_bot.position, pos, board
                    ):
                        pass
                    else:
                        if self.pos_turned:
                            self.Turned = True
                        elif self.Turned and not self.pos_turned:
                            self.Turned = False
                        self.goal_position = pos
                        self.OldPos = board_bot.position
                        return self.directions[ind]
        self.goal_position = None
        self.OldPos = board_bot.position
        for i in range(4):
            if not wrong_moves[i]:
                return self.directions[i]
        return 0, 0
