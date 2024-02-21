from abc import ABC
from typing import Tuple

from game.models import Board, GameObject


class BaseLogic(ABC):
    def next_move(self, board_bot: GameObject, board: Board) -> Tuple[int, int]:
        raise NotImplementedError()
