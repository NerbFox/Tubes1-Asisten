from dataclasses import dataclass
from typing import List, Optional, Union
from colorama import Fore, Style


@dataclass
class Bot:
    name: str
    email: str
    id: str


@dataclass
class Position:
    y: int
    x: int


@dataclass
class Base(Position): ...


@dataclass
class Properties:
    points: Optional[int] = None
    pair_id: Optional[str] = None
    diamonds: Optional[int] = None
    score: Optional[int] = None
    name: Optional[str] = None
    inventory_size: Optional[int] = None
    can_tackle: Optional[bool] = None
    milliseconds_left: Optional[int] = None
    time_joined: Optional[str] = None
    base: Optional[Base] = None


@dataclass
class GameObject:
    id: int
    position: Position
    type: str
    properties: Optional[Properties] = None


@dataclass
class Config:
    generation_ratio: Optional[float] = None
    min_ratio_for_generation: Optional[float] = None
    red_ratio: Optional[float] = None
    seconds: Optional[int] = None
    pairs: Optional[int] = None
    inventory_size: Optional[int] = None
    can_tackle: Optional[bool] = None


@dataclass
class Feature:
    name: str
    config: Optional[Config] = None


@dataclass
class Board:
    id: int
    width: int
    height: int
    features: List[Feature]
    minimum_delay_between_moves: int
    game_objects: Optional[List[GameObject]]

    @property
    def bots(self) -> List[GameObject]:
        return [d for d in self.game_objects if d.type == "BotGameObject"]

    @property
    def diamonds(self) -> List[GameObject]:
        return [d for d in self.game_objects if d.type == "DiamondGameObject"]

    def get_bot(self, bot: Bot) -> Optional[GameObject]:
        for b in self.bots:
            if b.properties.name == bot.name:
                return b
        return None

    def is_valid_move(
        self, current_position: Position, delta_x: int, delta_y: int
    ) -> bool:
        if not (-1 <= delta_x <= 1) or not (-1 <= delta_y <= 1):
            print(
                Fore.RED + Style.BRIGHT + "Invalid move:" + Style.RESET_ALL,
                "Delta values must be between -1 and 1 inclusive",
            )
            return False

        if delta_x == delta_y:
            print(
                Fore.RED + Style.BRIGHT + "Invalid move:" + Style.RESET_ALL,
                "Delta_x and delta_y cannot be equal",
            )
            return False

        if not (0 <= current_position.x + delta_x < self.width):
            print(
                Fore.RED + Style.BRIGHT + "Invalid move:" + Style.RESET_ALL,
                "X-coordinate out of bounds",
            )
            return False

        if not (0 <= current_position.y + delta_y < self.height):
            print(
                Fore.RED + Style.BRIGHT + "Invalid move:" + Style.RESET_ALL,
                "Y-coordinate out of bounds",
            )
            return False

        return True
