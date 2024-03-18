from typing import Optional, Tuple, List

from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from ..util import clamp
from random import randint

# constants
MAX_INT: int = float("inf")

# UTILITY FUNCTIONS
# TODO: return manhattan distance between two points
def count_pos_dist(p1: Position, p2: Position) -> int:
  return abs(p2.x - p1.x) + abs(p2.y - p1.y)

# TODO: return minimum distance between two points (current point and destination point) by considering if an object should go through teleports or not
# this function will return a tuple consists of the minimum distance, the target position, and a boolean use_portal
# if the minimum distance is achieved by stepping through the teleports, the target position will be the corresponding teleport and use_portal will be true
# otherwise, the target position will be the destination position and use_portal will be false
def get_minimum_dist(curr: Position, dest: Position, teleport_list: List[GameObject], board_width: int, board_height: int) -> Tuple[int, Position, bool]:
  # count relative distance without teleports
  curr_dist: int = count_pos_dist(curr, dest)
  init_curr_dist = curr_dist
  curr_target: Position = dest
  use_portal: bool = False

  # These long if-else codes aim to find the exact distance from current position to a destination without utilizing
  # teleports. This codes consider almost all (if not all) edge cases that occurs if the current x-axis or y-axis position
  # only have one step difference from the destination x-axis or y-axis position, and the teleports are in the area of those two points

  # CASE 1: current y-axis position only have 1 step difference from destination y-axis position
  # check if the teleports are in the area between those two points
  if (curr.x <= teleport_list[0].position.x <= dest.x or curr.x >= teleport_list[0].position.x >= dest.x) and (curr.x <= teleport_list[1].position.x <= dest.x or curr.x >= teleport_list[1].position.x >= dest.x):
    if curr.y == dest.y:
      if teleport_list[0].position.y == dest.y:
        if teleport_list[1].position.y == teleport_list[0].position.y:
          curr_dist += 2
        elif teleport_list[1].position.y == teleport_list[0].position.y - 1:
          if curr.y + 1 < board_height:
            curr_dist += 2
          else:
            curr_dist += 4
            if teleport_list[1].position.x == dest.x:
              curr_dist += 2
        elif teleport_list[1].position.y == teleport_list[0].position.y + 1:
          if curr.y - 1 >= 0:
            curr_dist += 2
          else:
            curr_dist += 4
            if teleport_list[1].position.x == dest.x:
              curr_dist += 2        
      elif teleport_list[1].position.y == dest.y:
        if teleport_list[1].position.y == teleport_list[0].position.y:
          curr_dist += 2
        elif teleport_list[1].position.y - 1 == teleport_list[0].position.y:
          if curr.y + 1 < board_height:
            curr_dist += 2
          else:
            curr_dist += 4
            if teleport_list[0].position.x == dest.x:
              curr_dist += 2
        elif teleport_list[1].position.y + 1 == teleport_list[0].position.y:
          if curr.y - 1 >= 0:
            curr_dist += 2
          else:
            curr_dist += 4  
            if teleport_list[0].position.x == dest.x:
              curr_dist += 2          
    elif curr.y == dest.y - 1:
      if curr.y == teleport_list[0].position.y and dest.y == teleport_list[1].position.y:
        curr_dist += 3
        if dest.y + 1 >= board_height and teleport_list[0].position.x == dest.x:
          curr_dist += 2
      elif curr.y == teleport_list[1].position.y and dest.y == teleport_list[0].position.y:
        curr_dist += 3
        if dest.y + 1 >= board_height and teleport_list[1].position.x == dest.x:
          curr_dist += 2
    elif curr.y == dest.y + 1:
      if curr.y == teleport_list[0].position.y and dest.y == teleport_list[1].position.y:
        curr_dist += 3
        if dest.y - 1 < 0 and teleport_list[0].position.x == dest.x:
          curr_dist += 2
      elif curr.y == teleport_list[1].position.y and dest.y == teleport_list[0].position.y:
        curr_dist += 3
        if dest.y - 1 < 0 and teleport_list[1].position.x == dest.x:
          curr_dist += 2

  # CASE 2: current x-axis position only have 1 step difference from destination y-axis position
  # check if the teleports are in the area between those two points
  if (curr.y <= teleport_list[0].position.y <= dest.y or curr.y >= teleport_list[0].position.y >= dest.y) and (curr.y <= teleport_list[1].position.y <= dest.y or curr.y >= teleport_list[1].position.y >= dest.y) and curr_dist == init_curr_dist:
    if curr.x == dest.x:
      if teleport_list[0].position.x == dest.x:
        if teleport_list[1].position.x == teleport_list[0].position.x:
          curr_dist += 2
        elif teleport_list[1].position.x == teleport_list[0].position.x - 1:
          if curr.x + 1 < board_width:
            curr_dist += 2
          else:
            curr_dist += 4
            if teleport_list[1].position.y == dest.y:
              curr_dist += 2
        elif teleport_list[1].position.x == teleport_list[0].position.x + 1:
          if curr.x - 1 >= 0:
            curr_dist += 2
          else:
            curr_dist += 4
            if teleport_list[1].position.y == dest.y:
              curr_dist += 2
      elif teleport_list[1].position.x == dest.x:
        if teleport_list[1].position.x == teleport_list[0].position.x:
          curr_dist += 2
        elif teleport_list[1].position.x - 1 == teleport_list[0].position.x:
          if curr.x + 1 < board_width:
            curr_dist += 2
          else:
            curr_dist += 4
            if teleport_list[0].position.y == dest.y:
              curr_dist += 2
        elif teleport_list[1].position.x + 1 == teleport_list[0].position.x:
          if curr.x - 1 >= 0:
            curr_dist += 2
          else:
            curr_dist += 4  
            if teleport_list[0].position.y == dest.y:
              curr_dist += 2
    elif curr.x == dest.x - 1:
      if curr.x == teleport_list[0].position.x and dest.x == teleport_list[1].position.x:
        curr_dist += 3
        if dest.x + 1 >= board_width and teleport_list[0].position.y == dest.y:
          curr_dist += 2
      elif curr.x == teleport_list[1].position.x and dest.x == teleport_list[0].position.x:
        curr_dist += 3
        if dest.x + 1 >= board_width and teleport_list[1].position.y == dest.y:
          curr_dist += 2
    elif curr.x == dest.x + 1:
      if curr.x == teleport_list[0].position.x and dest.x == teleport_list[1].position.x:
        curr_dist += 3
        if dest.x - 1 < 0 and teleport_list[0].position.y == dest.y:
          curr_dist += 2
      elif curr.x == teleport_list[1].position.x and dest.x == teleport_list[0].position.x:
        curr_dist += 3
        if dest.x - 1 < 0 and teleport_list[1].position.y == dest.y:
          curr_dist += 2     

  # count the distance between two points by using teleports
  for i in range(2):
    dist = count_pos_dist(curr, teleport_list[i].position) + count_pos_dist(dest, teleport_list[1 - i].position)
    # if current distance is lesser than the previously computed distance, choose current distance as the minimum distance
    # while changing the current target
    if dist < curr_dist:
      use_portal = True
      curr_dist = dist
      curr_target = teleport_list[i].position
  return curr_dist, curr_target, use_portal

# TODO: randomize delta_x and delta_y for determining next position
# this function is used when the delta_x != 0 and delta_y != 0 to give random move effect
def randomize_position(delta_x: int, delta_y: int) -> Tuple[int, int]:
  random_number = randint(0, 1)
  if random_number == 0:
    return (0, delta_y)
  else:
    return (delta_x, 0)

# TODO: get next move position if bot want to go from the current position to destination position
# if bot want to avoid teleports, set avoid to true. otherwise, set to false
def get_direction_position(curr: Position, dest: Position, teleport_list: List[GameObject], avoid: bool, width: int, height: int):
  # get initial delta_x and delta_y by using clamp function provided in util.py
  delta_x = clamp(dest.x - curr.x, -1, 1)
  delta_y = clamp(dest.y - curr.y, -1, 1)
  # get teleport position
  tel1_pos = teleport_list[0].position
  tel2_pos = teleport_list[1].position

  # if current position is equal to destination position, use random move
  # while this case rarely (or hardly ever) appears, it still important to prevent error by not sending (0,0) to the server
  if delta_x == 0 and delta_y == 0:
    return get_random_move(curr, width, height)

  # if delta_y = 0, delta_x != 0, and avoid is true,
  # check if the next teleport is located in the next position
  # if it's true, then go to the available y-axis first
  if delta_y == 0 and avoid:
    if (tel1_pos.y == curr.y and tel1_pos.x == curr.x + delta_x) or (tel2_pos.y == curr.y and tel2_pos.x == curr.x + delta_x):
      if curr.y + 1 < height:
        delta_x = 0
        delta_y = 1
      else:
        delta_x = 0
        delta_y = -1
  # if delta_x = 0, delta_y != 0, and avoid is true,
  # check if the next teleport is located in the next position
  # if it's true, then go to the available x-axis first
  elif delta_x == 0 and avoid:
    if (tel1_pos.x == curr.x and tel1_pos.y == curr.y + delta_y) or (tel2_pos.x == curr.x and tel2_pos.y == curr.y + delta_y):
      if curr.x + 1 < width:
        delta_y = 0
        delta_x = 1
      else:
        delta_y = 0
        delta_x = -1
  elif delta_y != 0 and delta_x != 0:
    # it delta_x != 0, delta_y != 0, and avoid is true
    if avoid:
      # check if bot's next position will be blocked by teleport and move accordingly
      if curr.x + delta_x == tel1_pos.x and tel1_pos.x == dest.x and (curr.y < tel1_pos.y < dest.y or curr.y > tel1_pos.y > dest.y): 
        delta_x = 0
      elif curr.x + delta_x == tel2_pos.x and tel2_pos.x == dest.x and (curr.y < tel2_pos.y < dest.y or curr.y > tel2_pos.y > dest.y): 
        delta_x = 0
      elif curr.y + delta_y == tel1_pos.y and tel1_pos.y == dest.y and (curr.x < tel1_pos.x < dest.x or curr.x > tel1_pos.x > dest.x): 
        delta_y = 0
      elif curr.y + delta_y == tel2_pos.y and tel2_pos.y == dest.y and (curr.x < tel2_pos.x < dest.x or curr.x > tel2_pos.x > dest.x): 
        delta_y = 0  
      elif curr.x + delta_x == tel1_pos.x and curr.y == tel1_pos.y:
        delta_x = 0
      elif curr.x + delta_x == tel2_pos.x and curr.y == tel2_pos.y:
        delta_x = 0
      elif curr.x == tel1_pos.x and curr.y + delta_y == tel1_pos.y:
        delta_y = 0
      elif curr.x == tel2_pos.x and curr.y + delta_y == tel2_pos.y:
        delta_y = 0   
      else:
        # give random effect to bot's movement
        delta_x, delta_y = randomize_position(delta_x, delta_y)
    else: 
      # give random effect to bot's movement
      delta_x, delta_y = randomize_position(delta_x, delta_y)
  return delta_x, delta_y

# TODO: get shortest distance from a certain diamond to its base and corresponding diamond
# this function will return list of list of integer, namely arr[N][3] where n is the amount of diamonds
# 1. arr[i][0] is the distance from ith diamond to jth diamond where jth diamond is the nearest diamond from ith diamond
# 2. arr[i][1] is the minimum distance from ith diamond to its base
# 3. arr[i][2] is the corresponding diamond's index from arr[i][0], namely the index-j from the explanation above
def get_all_diamonds_dist(diamonds: List[GameObject], teleports: List[GameObject], base: Position,width: int, height: int) -> List[List[int]]:
  n: int = len(diamonds)
  if n == 0:
    return []
  res = [[MAX_INT, MAX_INT, 0] for _ in range(n)]
  for i in range(n):
    # for ith diamond, get the minimum distance to base and assign the value to res[i][1]
    base_dist, _, _ = get_minimum_dist(diamonds[i].position, base, teleports, width, height)
    res[i][1] = base_dist
    for j in range(i + 1, n):
      dist, _, _ = get_minimum_dist(diamonds[i].position, diamonds[j].position, teleports, width, height) 
      # if current distance is lesser than the previously computed distance from ith diamond,
      # choose current distance as the minimum distance and assign j to res[i][2]
      if dist < res[i][0]:
        res[i][0] = dist
        res[i][2] = j
      # do the same thing for jth diamond
      if dist < res[j][0]:
        res[j][0] = dist
        res[j][2] = i
  return res

# TODO: check if two positions are equal
def is_position_equal(p1: Position, p2: Position) -> bool:
  return p1.x == p2.x and p1.y == p2.y

# TODO: check if a point is in the area between two points
def is_position_in_area(base: Position, dest: Position, query_obj: Position) -> bool:
  if base.x == query_obj.x and base.y == query_obj.y:
    return False
  check_x = base.x <= query_obj.x <= dest.x or base.x >= query_obj.x >= dest.x
  check_y = base.y <= query_obj.y <= dest.y or base.y >= query_obj.y >= dest.y
  return check_x and check_y

# TODO: pick optimal diamond
# this function will return the optimal diamond target's position and a boolean use_portal
# if the optimal distance is achieved by stepping through the teleports, the target position will be corresponding teleport's position, use_portal will be true
# otherwise, the target position will be the optimal diamond's position and use_portal will be false
def pick_optimal_diamond(curr_pos: Position, diamond_list: List[GameObject], teleport_list: List[GameObject], diamond_dist_list: List[List[int]], num_of_diamond_needed: int, width: int, height: int) -> Tuple[Position, bool]:
  min_score = MAX_INT
  min_base_dist = MAX_INT # used when number of diamond needed is > 2
  is_portal_used = False
  selected_diamond = None
  diamond_len = len(diamond_list)

  for i in range(diamond_len):
    # skip if ith diamond's point is greater than number of diamond needed
    if diamond_list[i].properties.points > num_of_diamond_needed:
      continue
    # get distance from current position to ith diamonds
    curr_dist, curr_target, curr_is_portal_used = get_minimum_dist(curr_pos, diamond_list[i].position, teleport_list, width, height)
    # calculate current score based on number of diamond needed
    d_needed = num_of_diamond_needed - diamond_list[i].properties.points
    base_dist = diamond_dist_list[i][1]
    # if the number of diamond needed is 1, 
    # current score is the distance from current position to ith diamond plus the distance from ith diamond the the base
    if num_of_diamond_needed == 1:
      curr_score = curr_dist + base_dist
    elif num_of_diamond_needed == 2:
      # if the number of needed diamond is 2 and ith diamond's point is equal to 1,
      # current score is the distance from current position to ith diamond plus the distance from ith diamond to jth diamond (where jth diamond is the nearest diamond from i)
      # plus the distance from jth diamond to the base
      if d_needed != 0 and diamond_len > 1:
        curr_score = curr_dist + diamond_dist_list[i][0] + diamond_dist_list[diamond_dist_list[i][2]][1]
      # if the number of needed diamond is 2 and ith diamond's point is equal to 2 or there is no remaning diamond (diamond_len == 1),
      # current score is the distance from current position to ith diamond plus the distance from ith diamond the the base
      else:
        curr_score = curr_dist + base_dist
    else:
      # if the number of diamond needed is 1 and ith diamond point is equal to 1,
      # current score is the distance from current position to the ith diamond's position plus the distance between ith diamond and jth diamond (where jth diamond is the nearest diamond from i)
      # otherwise, the score is just the distance from current position to the ith diamond
      curr_score = curr_dist
      if diamond_list[i].properties.points == 1 and diamond_len > 1:
        curr_score += diamond_dist_list[i][0]
    # if current score is lesser than minimum score
    # or current score is equal to minimum score and ith diamond distance to base is lesser than minimum base distance (case when number of diamond needed is 2)
    # set current score as the minimum score
    if curr_score < min_score or (curr_score == min_score and base_dist < min_base_dist and num_of_diamond_needed > 2):
      min_score = curr_score
      selected_diamond = curr_target
      is_portal_used = curr_is_portal_used
      min_base_dist = base_dist

  return selected_diamond, is_portal_used

# TODO: get random move from current position
def get_random_move(curr_pos: Position, width: int, height: int):
  if curr_pos.x + 1 < width:
    return 1, 0
  elif curr_pos.x - 1 >= 0:
    return -1, 0
  elif curr_pos.y + 1 < height:
    return 0, 1
  else:
    return 0, -1

# TODO: take the nearest diamond with some considerations
class MeowNearestDiamond(BaseLogic):
  def __init__(self) -> None:
    self.directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
    self.goal_position: Optional[Tuple[int, int]] = None
    self.current_direction = 0
  
  def next_move(self, board_bot: GameObject, board: Board) -> Tuple[int]:
    props = board_bot.properties
    # initialize variables needed
    curr_pos: Position = board_bot.position
    curr_points: int = props.diamonds
    width: int = board.width
    height: int = board.height
    base_pos: Position = board_bot.properties.base
    remaining_time: int = props.milliseconds_left // 1000
    inventory_size: int = props.inventory_size

    # initialize object lists
    teleport_list: List[GameObject] = []
    diamond_list: List[GameObject] = []
    red_button: GameObject = None

    # get all object list
    for obj in board.game_objects:
      if obj.type == "TeleportGameObject":
        teleport_list.append(obj)
      elif obj.type == "DiamondGameObject":
        diamond_list.append(obj)
      elif obj.type == "DiamondButtonGameObject":
        red_button = obj
    
    # get list of shortest distance from a certain diamond to its base and corresponding diamond (read comments from line 230 - 234)
    diamond_dist_list = get_all_diamonds_dist(diamond_list, teleport_list, base_pos, width, height)
    # get distance from current position to base
    base_dist, base_target, base_use_portal = get_minimum_dist(curr_pos, base_pos, teleport_list, width, height)
    # get optimal diamond (target) position
    diamond_picked, is_portal_used = pick_optimal_diamond(curr_pos, diamond_list, teleport_list, diamond_dist_list, inventory_size - curr_points, width, height)
    # if remaining time is lesser than the distance from current position to base (by the assumption of 1 movement/second)
    if remaining_time < base_dist + 2:
      # if current points is not equal to zero, go to the base
      if (curr_points != 0):
        # if the optimal diamond's position is in the area between current position and base, traverse through the optimal diamond
        if (0 < curr_points < inventory_size and diamond_picked != None and not is_portal_used and is_position_in_area(curr_pos, base_target, diamond_picked)):
          return get_direction_position(curr_pos, diamond_picked, teleport_list, True, width, height)
        # if the red button's position is in the area between current position and base, traverse through the red button
        elif (is_position_in_area(curr_pos, base_target, red_button.position)):
          return get_direction_position(curr_pos, red_button.position, teleport_list, True, width, height)
        else:
          return get_direction_position(curr_pos, base_target, teleport_list, not base_use_portal, width, height)
      # if current points is equal to zero, go to optimal diamond's position if possible
      else:
        return get_direction_position(curr_pos, diamond_picked, teleport_list, not is_portal_used, width, height)
    else:
      if (curr_points < inventory_size):
        # if there's optimal diamond
        if diamond_picked != None:
          # traverse through base if the base' position is in the area between current position and optimal diamond's position
          if is_position_in_area(curr_pos, diamond_picked, base_pos):
            return get_direction_position(curr_pos, base_pos, teleport_list, True, width, height)
          # traverse through red button if the red button's position is in the area between current position and optimal diamond's position
          elif is_position_in_area(curr_pos, diamond_picked, red_button.position):
            return get_direction_position(curr_pos, red_button.position, teleport_list, True, width, height)
          else:
            return get_direction_position(curr_pos, diamond_picked, teleport_list, not is_portal_used, width, height)
        # go to base if there is no optimal diamond
        else:
          return get_direction_position(curr_pos, base_target, teleport_list, not base_use_portal, width, height)
      # if inventory is full, go to the base
      else:
        return get_direction_position(curr_pos, base_target, teleport_list, not base_use_portal, width, height)
# BIAR PAS 400 LINES HEHE