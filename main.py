import argparse
from time import sleep

from colorama import Back, Fore, Style, init
from game.api import Api
from game.board_handler import BoardHandler
from game.bot_handler import BotHandler
from game.logic.random import RandomLogic
from game.logic.asisten import AsistenLogic
from game.util import *
from game.logic.base import BaseLogic
# import from tubes mahasiswa:
from game.logic.ArticaKenapaBatal import MeowNearestDiamond
from game.logic.Cijawjaw import CijawjawLogic
from game.logic.DNA import DNALogic
from game.logic.Dujari import DujariLogic
from game.logic.QUEEN import QUEENLogic
from game.logic.terkesTima import TerkesTimaLogic
from game.logic.TheYuds import TheYudsLogic
from game.logic.OlahragaGuntur import OlahragaGunturLogic
from game.logic.SambutRamadhan import SambutRamadhanLogic
from game.logic.MrNaginski import MrNaginskiLogic
from game.logic.TipisTipis import TipisTipisLogic
from game.logic.Tulas import TulasLogic
from game.logic.TonggokuNyalegNdes import TonggokuNyalegNdesLogic
from game.logic.Janggar import JanggarLogic
from game.logic.urbanGym import BotsMove as UrbanGymLogic
from game.logic.bingung import Pulang as BingungLogic
from game.logic.silverqueen import SuperSilverqueen as SilverqueenLogic
from game.logic.HolderRNDR import NearestBase as HolderLogic
from game.logic.TuanKrabs import GradientLogic as TuanKrabsLogic
from game.logic.metiuganteng import botLogic as MetiuLogic
from game.logic.Robotnik import Robotnik as RobotnikLogic
from game.logic.Kelompok56 import Kelompok56 as Kel56Logic
from game.logic.tbfoReborn import MyBot as tbfoRebornLogic
from game.logic.susugratis import Logic as susugratisLogic
from game.logic.gatauHehe import LTD as gatauHeheLogic
from game.logic.SiniMainSamaOm import OptBot as SiniMainSamaOmLogic
from game.logic.ilmuPadi import Padibot as ilmuPadiLogic
from game.logic.MVP import GreedyDiamondLogic as MVPLogic
from game.logic.SulfatGemoy import SulfatGemoy as SulfatGemoyLogic

init()
BASE_URL = "http://localhost:3000/api"
DEFAULT_BOARD_ID = 4
CONTROLLERS = {
    "Random": RandomLogic,
    "Asisten": AsistenLogic,
    # Controllers from tubes mahasiswa:
    "ArticaKenapaBatal": MeowNearestDiamond,
    "Cijawjaw": CijawjawLogic,
    "DNA": DNALogic,
    "Dujari": DujariLogic,
    "QUEEN": QUEENLogic,
    "terkesTima": TerkesTimaLogic,
    "TheYuds": TheYudsLogic,
    "OlahragaGuntur": OlahragaGunturLogic,
    "SambutRamadhan": SambutRamadhanLogic,
    "MrNaginski": MrNaginskiLogic,
    "TipisTipis": TipisTipisLogic,
    "Tulas": TulasLogic,
    "TonggokuNyalegNdes": TonggokuNyalegNdesLogic,
    "Janggar": JanggarLogic,
    "UrbanGym" : UrbanGymLogic,
    "Bingung" : BingungLogic,
    "Silverqueen" : SilverqueenLogic,
    "HolderRNDR" : HolderLogic,
    "TuanKrabs": TuanKrabsLogic,
    "Metiuganteng" : MetiuLogic,
    "Robotnik" : RobotnikLogic,
    "Kelompok56" : Kel56Logic
}

###############################################################################
#
# Parse command line arguments
#
###############################################################################
parser = argparse.ArgumentParser(description="Diamonds example bot")
group = parser.add_mutually_exclusive_group()
group.add_argument(
    "--token",
    help="A bot token to use when running using an existing bot",
    action="store",
)
group.add_argument("--name", help="The name of the bot to register", action="store")
parser.add_argument("--email", help="The email of the bot to register", action="store")
parser.add_argument(
    "--password", help="The password of the bot to register", action="store"
)
parser.add_argument("--team", help="The team of the bot to register", action="store")
parser.add_argument(
    "--board", help="Id of the board to join", default=DEFAULT_BOARD_ID, action="store"
)
parser.add_argument(
    "--time-factor",
    help="A factor to multiply each move command with. If you want to run the bot in a slower mode e.g. use --time-factor=5 to multiply each delay with 5.",
    default=1,
    action="store",
)
parser.add_argument(
    "--logic",
    help="The logic controller to use. Valid options are: {}".format(
        ", ".join(list(CONTROLLERS.keys()))
    ),
    action="store",
)
group = parser.add_argument_group("API connection")
group.add_argument(
    "--host", action="store", default=BASE_URL, help="Default: {}".format(BASE_URL)
)
args = parser.parse_args()

time_factor = int(args.time_factor)
api = Api(args.host)
bot_handler = BotHandler(api)
board_handler = BoardHandler(api)

###############################################################################
#
# (Try and) Register a new bot if we have not supplied a token
#
###############################################################################
if not args.token:
    recovered_token = bot_handler.recover(args.email, args.password)
    args.token = recovered_token
    if not recovered_token:
        bot = bot_handler.register(args.name, args.email, args.password, args.team)
        if bot:
            print("")
            print(
                Style.BRIGHT
                + "Bot registered. Token: {}".format(bot.id)
                + Style.RESET_ALL
            )
            args.token = bot.id
        else:
            print(
                Fore.RED
                + Style.BRIGHT
                + "Error: "
                + Style.RESET_ALL
                + "Unable to register bot"
            )
            exit(1)

###############################################################################
#
# Setup bot using token and play game
#
###############################################################################
bot = bot_handler.get_my_info(args.token)
logic_controller = args.logic
if logic_controller not in CONTROLLERS:
    print(
        Fore.RED
        + Style.BRIGHT
        + "Error: "
        + Style.RESET_ALL
        + "Invalid logic controller"
    )
    exit(1)

if not bot.name:
    print(Fore.RED + Style.BRIGHT + "Error: " + Style.RESET_ALL + "Bot does not exist")
    exit(1)
print(Fore.BLUE + Style.BRIGHT + "Welcome back, " + Style.RESET_ALL + bot.name)

# Setup variables
logic_class = CONTROLLERS[logic_controller]
bot_logic: BaseLogic = logic_class()

###############################################################################
#
# Find a board to join
#
###############################################################################
current_board_id = int(args.board)

if not current_board_id:
    # List active boards to find one we can join if we haven't specified one
    boards = board_handler.list_boards()
    for board in boards:
        # Try to join board
        board_joined = False
        current_board_id = board.id
        success = bot_handler.join(bot.id, current_board_id)
        if success:
            board_joined = True
            break

    if not board_joined:
        exit()
else:
    # Try to join the one we specified
    success = bot_handler.join(bot.id, current_board_id)
    if not success:
        current_board_id = None

# Did we manage to join a board?
if not current_board_id:
    print(
        Fore.RED
        + Style.BRIGHT
        + "Error: "
        + Style.RESET_ALL
        + "Unable to find any boards to join"
    )
    exit(1)

###############################################################################
#
# Prepare state from current board
#
###############################################################################
board = board_handler.get_board(current_board_id)
move_delay = board.minimum_delay_between_moves / 1000

###############################################################################
#
# Game play loop
#
###############################################################################
while True:
    # Find our info among the bots on the board
    board_bot = board.get_bot(bot)
    if not board_bot:
        # Managed to get game over
        break

    # Calculate next move
    delta_x, delta_y = bot_logic.next_move(board_bot, board)
    # delta_x, delta_y = (1, 0)
    if not board.is_valid_move(board_bot.position, delta_x, delta_y):
        print(
            Fore.YELLOW + Style.BRIGHT + "Warn:" + Style.RESET_ALL,
            "Invalid move will be ignored."
            + f" Your move: ({delta_x}, {delta_y}). Your position: ({board_bot.position.x}, {board_bot.position.y})",
        )
        sleep(1)
        continue

    try:
        # Try to perform move
        board = bot_handler.move(bot.id, current_board_id, delta_x, delta_y)
    except Exception as e:
        break

    if not board:
        # Read new board state
        board = board_handler.get_board(current_board_id)

    # Get new state
    board_bot = board.get_bot(bot)
    if not board_bot:
        # Managed to get game over after move
        break

    # Don't spam the board more than it allows!
    # sleep(move_delay * time_factor)
    sleep(1)


###############################################################################
#
# Game over!
#
###############################################################################
print(Fore.BLUE + Style.BRIGHT + "Game over!" + Style.RESET_ALL)
