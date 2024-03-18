import random
from typing import Optional
from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from ..util import *

def count_distance(current_x, current_y, dest_x, dest_y):
        delta_x = dest_x - current_x
        delta_y = dest_y - current_y
        return (abs(delta_x) + abs(delta_y))
    
def find_densest(diamonds, eps=1, min_samples=3):
    clusters = []
    visited = set()
    noise = set()

    def neighbors(diamond):
        return [other for other in diamonds if count_distance(diamond.position.x, diamond.position.y, other.position.x, other.position.y) <= eps]

    for diamond in diamonds:
        if diamond.id in visited:
            continue
        visited.add(diamond.id)
        neighbor_diamonds = neighbors(diamond)
        if len(neighbor_diamonds) < min_samples:
            noise.add(diamond.id)
        else:
            cluster = []
            clusters.append(cluster)
            cluster.append(diamond)
            for neighbor in neighbor_diamonds:
                if neighbor.id in noise:
                    cluster.append(neighbor)
                    noise.remove(neighbor.id)
                if neighbor.id not in visited:
                    visited.add(neighbor.id)
                    more_neighbors = neighbors(neighbor)
                    if len(more_neighbors) >= min_samples:
                        neighbor_diamonds.extend(more_neighbors)
                    if neighbor not in cluster:
                        cluster.append(neighbor)
    return clusters

# Find all teleported
def getAllTeleporterSorted(board,current_position):
    teleport = [x for x in board.game_objects if (x.type == "TeleportGameObject")]
    
    teleport_groups = {}
    for teleporter in teleport:
        pair_id = teleporter.properties.pair_id
        if pair_id not in teleport_groups:
            teleport_groups[pair_id] = []
        teleport_groups[pair_id].append(teleporter)

    sorted_teleport_groups = {}
    for pair_id, teleporters in teleport_groups.items():
        sorted_teleporters = sorted([(teleporter.position, abs(current_position.x - teleporter.position.x) + abs(current_position.y - teleporter.position.y)) for teleporter in teleporters], key=lambda t: t[1])
        sorted_teleport_groups[pair_id] = sorted_teleporters

    sorted_teleport_groups = dict(sorted(sorted_teleport_groups.items(), key=lambda item: item[1][0][1]))
    return sorted_teleport_groups

# Find the distance between bot and base
def findDistanceByBotAndBase(object,base,current_position):
    x = []
    y = []

    for position in object:
        posX = abs(base.x  - position.position.x)
        posY = abs(base.y - position.position.y)
        distance = (abs(base.x  - position.position.x) + abs(base.y - position.position.y))
        x.append([distance,position.position,[posX,posY],position.properties.points])
        posX = abs(current_position.x  - position.position.x)
        posY = abs(current_position.y - position.position.y)
        distance1 = (abs(current_position.x  - position.position.x) + abs(current_position.y - position.position.y))
        y.append([distance1,position.position,[posX,posY],position.properties.points])
    return x,y
    
class NearestBase(BaseLogic):
    def __init__(self):
        self.directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        self.goal_position: Optional[Position] = None
        self.current_direction = 0
        
    def next_move(self, board_bot: GameObject, board: Board):
        props = board_bot.properties
        current_position = board_bot.position
        base = board_bot.properties.base
        
        board_width = board.width
        board_height = board.height

        # Find all diamonds and red button in board
        all_diamonds = [x for x in board.game_objects if (x.type=="DiamondGameObject")]
        red_button = [x for x in board.game_objects if (x.type=="DiamondButtonGameObject")]
        
        # Find the densest cluster
        cluster = find_densest(all_diamonds)
        densest_cluster = max(cluster, key=len, default=[])
        
        diamond_distance_base , diamond_distance_bot = findDistanceByBotAndBase(all_diamonds,base,current_position)   
        red_button_base , red_button_bot = findDistanceByBotAndBase(red_button,base,current_position)
        diamond_sorted_base = sorted(diamond_distance_base, key=lambda d: d[0])
        diamond_sorted_bot = sorted(diamond_distance_bot, key=lambda d: d[0])
        red_button_sorted_base = sorted(red_button_base, key=lambda d: d[0])
        red_button_sorted_bot = sorted(red_button_bot, key=lambda d: d[0])
        base_distance = count_distance(current_position.x, current_position.y, board_bot.properties.base.x, board_bot.properties.base.y)
        sorted_teleport_groups = getAllTeleporterSorted(board,current_position)

        # Calculate the centroid of the densest cluster
        if densest_cluster:
            centroid_x = sum(d.position.x for d in densest_cluster) / len(densest_cluster)
            centroid_y = sum(d.position.y for d in densest_cluster) / len(densest_cluster)
            densest_centroid = Position(x=int(centroid_x), y=int(centroid_y))
        else:
            densest_centroid = None
        
        # Goals condition
        if props.diamonds >= 4:
            if(diamond_sorted_bot[0][0] <= 2 and props.diamonds + diamond_sorted_bot[0][3] <= 5):
                self.goal_position = diamond_sorted_bot[0][1]
            else:
                base = board_bot.properties.base
                self.goal_position = base
        else:
            if(base_distance == 1 and props.diamonds >= 2):
                self.goal_position = base
            elif(board_bot.properties.milliseconds_left <= 8000 and props.diamonds >= 1):
                if(diamond_sorted_bot[0][0] <= 1 ):
                    self.goal_position = diamond_sorted_bot[0][1]
                else:
                    self.goal_position = base
            elif(diamond_sorted_bot or diamond_sorted_base):
                if(props.diamonds >= 3 and base_distance <= 3):
                    self.goal_position = base
                elif(diamond_sorted_bot[0][0] <= 2) :
                    self.goal_position = diamond_sorted_bot[0][1]
                elif((diamond_sorted_base[0][2][0] < 0.4 * board_width) and  (diamond_sorted_base[0][2][1] <  0.4 * board_height)) :
                    if(diamond_sorted_bot[0][0] <= 2 ):
                        self.goal_position = diamond_sorted_bot[0][1]
                    else:
                        self.goal_position = diamond_sorted_base[0][1]
                elif(densest_centroid):
                    self.goal_position = densest_centroid
                else:
                    if(red_button_sorted_base != []):
                        if((red_button_sorted_base[0][2][0] < 0.4 * board_width) and (red_button_sorted_base[0][2][1] < 0.4 * board_height)):
                            self.goal_position = red_button_sorted_base[0][1]
                        elif(red_button_sorted_bot[0][0] <= 3):
                            self.goal_position = red_button_sorted_bot[0][1]
                        else:
                            self.goal_position = diamond_sorted_bot[0][1]
            else:
                if(props.diamonds >= 3):
                    self.goal_position = base
                else:
                    self.goal_position = red_button

        current_position = board_bot.position
        if self.goal_position:
            shortest_way = count_distance(current_position.x, current_position.y, self.goal_position.x, self.goal_position.y)
            shortest_way_position = self.goal_position

            # Iterate over each pair of teleporters
            for pair_id, teleporters in sorted_teleport_groups.items():
                closest_teleporter, distance_to_closest_teleporter = teleporters[0]
                second_teleporter = teleporters[1][0]

                # Calculate the distance from the second teleporter in the pair to the goal position
                distance_tele2_goal = count_distance(second_teleporter.x, second_teleporter.y, self.goal_position.x, self.goal_position.y)

                # Calculate the total distance if using this teleporter pair
                way1 = distance_to_closest_teleporter + distance_tele2_goal

                # Compare the total distance with the shortest way found so far
                if way1 < shortest_way:
                    shortest_way = way1
                    shortest_way_position = closest_teleporter


            # Update the goal position to the shortest way position
            if(current_position == shortest_way_position):
                delta_x, delta_y = random.choice([(1, 0), (0, 1), (-1, 0), (0, -1)])
            else:
                self.goal_position = shortest_way_position
                delta_x, delta_y = get_direction(
                    current_position.x,
                    current_position.y,
                    self.goal_position.x,
                    self.goal_position.y,
                )
        else:
            # Roam around
            delta = self.directions[self.current_direction]
            delta_x = delta[0]
            delta_y = delta[1]
            
            if random.random() > 0.6:
                self.current_direction = (self.current_direction + 1) % len(
                    self.directions
                )

        # When bot stuck
        if(delta_x == 0 and delta_y == 0) :
            delta_x, delta_y = random.choice([(1, 0), (0, 1), (-1, 0), (0, -1)])
        return delta_x, delta_y