#!/usr/bin/env python3
# Python 3.6
import hlt
from hlt import constants
from hlt.positionals import Direction, Position
import random
import logging
import time
import math

# This game object contains the initial game state.
game = hlt.Game()
# At this point "game" variable is populated with initial map data.
# This is a good place to do computationally expensive start-up pre-processing.
# As soon as you call "ready" function below, the 2 second per turn timer will start.
game.ready("MyBotv8")

# Here, you log here your id, which you can always fetch from the game object by using my_id.
logging.info("Successfully created bot! My Player ID is {}.".format(game.my_id))

ignore_Halite = 75
still_Multiplier = 2

ship_States = {}
ship_safety = {}
ship_in_dead_zone = {}

game_phase = 'gathering'

CURRENT_ROUND = 0
TOTAL_HALITE_START = 0

map_Settings = {400: 32,
                425: 40,
                450: 48,
                475: 56,
                500: 64
}

direction_Order = [Direction.North, Direction.South, Direction.East, Direction.West, Direction.Still]

me = game.me
game_map = game.game_map

NUMBER_OF_PLAYERS = 0

ZONE_OF_INTEREST = []
min_halite_to_be_interesting = 1000

for y in range(map_Settings[constants.MAX_TURNS]):
    for x in range(map_Settings[constants.MAX_TURNS]):
        TOTAL_HALITE_START += game_map[Position(x,y)].halite_amount

#for row in ZONE_OF_INTEREST:
#    temp_row_string = ''
#    for cell in row:
#        temp_row_string += f'{cell},'
#    logging.info(temp_row_string)      


logging.info(f"TOTAL_HALITE_START = {TOTAL_HALITE_START}.")
NUMBER_OF_PLAYERS = len(game.players)
logging.info(f"NUMBER_OF_PLAYERS = {NUMBER_OF_PLAYERS}.")

while True:
    ship_stuck = {}
    ship_killing_possibility = {}

    me = game.me
    p0 = game.players[0]
    p1 = game.players[1]

    if NUMBER_OF_PLAYERS == 4:
        p2 = game.players[2]
        p3 = game.players[3]

    game_map = game.game_map
    game.update_frame()
    CURRENT_ROUND += 1
    interesting_coords = []
    start_time_turn = time.time()

    ship_positions = [s.position for s in list(me.get_ships())] 

    current_total_halite = 0
    if game_phase == 'gathering':
        for y in range(map_Settings[constants.MAX_TURNS]):
            for x in range(map_Settings[constants.MAX_TURNS]):
                current_total_halite += game_map[Position(x,y)].halite_amount

    if current_total_halite / NUMBER_OF_PLAYERS < 15000 and game_phase == 'gathering':
        game_phase = 'secure_halite'

    window = 1
    direction_of_interest = {}
    
    if game_phase == 'gathering':
        for y in range(map_Settings[constants.MAX_TURNS]):
            temp_row = []
            for x in range(map_Settings[constants.MAX_TURNS]):
                temp_sum = 0    
                for yy in range(-1*window + y, y + window+1):
                    for xx in range(-1*window + x, x + window+1):
                        temp_sum += game_map[Position(xx,yy)].halite_amount

                        if temp_sum > min_halite_to_be_interesting:
                            interesting_coords.append([x,y])
        if len(interesting_coords) > 1500:
            min_halite_to_be_interesting *= 1.2
        elif len(interesting_coords) < 600:
            min_halite_to_be_interesting /= 1.2


    ignore_Halite = ((TOTAL_HALITE_START/(NUMBER_OF_PLAYERS*1.2))/(map_Settings[constants.MAX_TURNS]**2)) * (1 - CURRENT_ROUND / (constants.MAX_TURNS))
    logging.info(f"ignore halite = {ignore_Halite}.")

    command_queue = []
    position_Choices = []

    ship_In_Priority_Order = []
    ship_Priority_0 = []
    ship_Priority_1 = []
    ship_Priority_2 = []
    ship_Priority_3 = []
    ship_Priority_4 = []
    ship_Priority_5 = []
    ship_Priority_6 = []
    ship_Priority_7 = []

    # Calculate the distance between all ships and the shipyard
    # and check if ship should pass in safety mode
    if CURRENT_ROUND / constants.MAX_TURNS > 0.85:
        for ship in me.get_ships():
            distance_from_shipyard = game_map.calculate_distance(ship.position, me.shipyard.position)
            if distance_from_shipyard + 16 > constants.MAX_TURNS - CURRENT_ROUND:
                if random.randint(0, distance_from_shipyard) >= int(distance_from_shipyard*0.75):
                    ship_States[ship.id] = "time_to_get_home"
            if distance_from_shipyard + 2 > constants.MAX_TURNS - CURRENT_ROUND:  
                ship_States[ship.id] = "time_to_get_home"

    for ship in me.get_ships():
        position_Options = ship.position.get_surrounding_cardinals() + [ship.position]
        position_Dict = {}
        halite_Dict = {}

        if ship.halite_amount > 800 * (1 - (0.7 * constants.MAX_TURNS / CURRENT_ROUND)) and NUMBER_OF_PLAYERS == 4:
            ship_safety[ship.id] = True
        elif ship.halite_amount > 1000 * (1 - (0.7 * constants.MAX_TURNS / CURRENT_ROUND)) and NUMBER_OF_PLAYERS == 2:
            ship_safety[ship.id] = True
        else:
            ship_safety[ship.id] = False

        if ship.id not in ship_States:
            ship_States[ship.id] = "collecting"

        for n, direction in enumerate(direction_Order):
            position_Dict[direction] = position_Options[n]

        for direction in position_Dict:
            position = game_map.normalize(position_Dict[direction])
            halite_amount = game_map[position].halite_amount
            if game_map.normalize(position_Dict[direction]) not in position_Choices:
                if direction == Direction.Still:
                    halite_Dict[direction] = max(0, halite_amount - ignore_Halite) ** still_Multiplier
                else:
                    halite_Dict[direction] = max(0, halite_amount - ignore_Halite)
            else:
                logging.info("attempting to move to same spot\n")

        if (ship.position + Position(0, 1) in ship_positions) and (ship.position + Position(0, -1) in ship_positions) and (ship.position + Position(1, 0) in ship_positions) and (ship.position + Position(-1, 0) in ship_positions):
            ship_stuck[ship.id] = True
            logging.info('ship stuck')
        else:
            ship_stuck[ship.id] = False

        if NUMBER_OF_PLAYERS == 2:
            ship_killing_possibility[ship.id] = (99, 99) 
            if ship.halite_amount < 100:
                if game_map[ship.position + Position(0, 1)].ship != None:
                    check_for_ennemy_ship = game_map[ship.position + Position(0, 1)].ship
                    if check_for_ennemy_ship.position not in ship_positions:
                        if check_for_ennemy_ship.halite_amount > ship.halite_amount:
                            ship_killing_possibility[ship.id] = (0, 1)
                elif game_map[ship.position + Position(0, -1)].ship != None:
                    check_for_ennemy_ship = game_map[ship.position + Position(0, -1)].ship
                    if check_for_ennemy_ship.position not in ship_positions:
                        if check_for_ennemy_ship.halite_amount > ship.halite_amount:
                            ship_killing_possibility[ship.id] = (0, -1)
                elif game_map[ship.position + Position(1, 0)].ship != None:
                    check_for_ennemy_ship = game_map[ship.position + Position(1, 0)].ship
                    if check_for_ennemy_ship.position not in ship_positions:
                        if check_for_ennemy_ship.halite_amount > ship.halite_amount:
                            ship_killing_possibility[ship.id] = (1, 0)
                elif game_map[ship.position + Position(-1, 0)].ship != None:
                    check_for_ennemy_ship = game_map[ship.position + Position(-1, 0)].ship
                    if check_for_ennemy_ship.position not in ship_positions:
                        if check_for_ennemy_ship.halite_amount > ship.halite_amount:
                            ship_killing_possibility[ship.id] = (-1, 0)
        else:
            ship_killing_possibility[ship.id] = (99, 99) 
            if ship.halite_amount < 100:
                if game_map[ship.position + Position(0, 1)].ship != None:
                    check_for_ennemy_ship = game_map[ship.position + Position(0, 1)].ship
                    if check_for_ennemy_ship.position not in ship_positions:
                        if check_for_ennemy_ship.halite_amount > ship.halite_amount+200:
                            ship_killing_possibility[ship.id] = (0, 1)
                elif game_map[ship.position + Position(0, -1)].ship != None:
                    check_for_ennemy_ship = game_map[ship.position + Position(0, -1)].ship
                    if check_for_ennemy_ship.position not in ship_positions:
                        if check_for_ennemy_ship.halite_amount > ship.halite_amount+200:
                            ship_killing_possibility[ship.id] = (0, -1)
                elif game_map[ship.position + Position(1, 0)].ship != None:
                    check_for_ennemy_ship = game_map[ship.position + Position(1, 0)].ship
                    if check_for_ennemy_ship.position not in ship_positions:
                        if check_for_ennemy_ship.halite_amount > ship.halite_amount+200:
                            ship_killing_possibility[ship.id] = (1, 0)
                elif game_map[ship.position + Position(-1, 0)].ship != None:
                    check_for_ennemy_ship = game_map[ship.position + Position(-1, 0)].ship
                    if check_for_ennemy_ship.position not in ship_positions:
                        if check_for_ennemy_ship.halite_amount > ship.halite_amount+200:
                            ship_killing_possibility[ship.id] = (-1, 0)



        # see if ship needs guidance
        
        if halite_Dict[max(halite_Dict, key=halite_Dict.get)] < 10:
            ship_in_dead_zone[ship.id] = True
            logging.info(f"Ship {ship.id} max halite dict = {halite_Dict[max(halite_Dict, key=halite_Dict.get)]} so its True")
        else:
            ship_in_dead_zone[ship.id] = False
            logging.info(f"Ship {ship.id} max halite dict = {halite_Dict[max(halite_Dict, key=halite_Dict.get)]} so its False")

        if math.ceil(game_map[ship.position].halite_amount * 0.1) > ship.halite_amount:
            ship_States[ship.id] = "pinned"

        if ship_States[ship.id] == "pinned":
            ship_Priority_0.append(ship)
        elif ship_stuck[ship.id] and ship_States[ship.id] != "pinned":
            ship_Priority_1.append(ship)
        elif ship_States[ship.id] == "depositing" and ship_safety[ship.id] and not ship_stuck[ship.id]:
            ship_Priority_2.append(ship)
        elif ship_States[ship.id] == "depositing" and not ship_stuck[ship.id]:
            ship_Priority_3.append(ship)
        elif ship_States[ship.id] == "collecting" and ship_safety[ship.id] and not ship_stuck[ship.id]:
            ship_Priority_4.append(ship)
        elif ship_States[ship.id] == "collecting" and not ship_stuck[ship.id]:
            ship_Priority_5.append(ship)
        else:
            ship_Priority_6.append(ship)

    for single_ship in ship_Priority_0:
        ship_In_Priority_Order.append(single_ship)
    for single_ship in ship_Priority_1:
        ship_In_Priority_Order.append(single_ship)
    for single_ship in ship_Priority_2:
        ship_In_Priority_Order.append(single_ship)
    for single_ship in ship_Priority_3:
        ship_In_Priority_Order.append(single_ship)
    for single_ship in ship_Priority_4:
        ship_In_Priority_Order.append(single_ship)
    for single_ship in ship_Priority_5:
        ship_In_Priority_Order.append(single_ship)
    for single_ship in ship_Priority_6:
        ship_In_Priority_Order.append(single_ship)

    for ship in ship_In_Priority_Order:
        position_Options = ship.position.get_surrounding_cardinals() + [ship.position]
        position_Dict = {}
        halite_Dict = {}
        surroundings = []
        dangerous_positions = []
        ship_positions = [s.position for s in list(me.get_ships())] 
        sight = 2

        for y in range(-1*sight, sight+1):
            row = []
            for x in range(-1*sight, sight+1):
                current_cell = game_map[ship.position + Position(x,y)]

                if game_map.normalize(current_cell.position) not in ship_positions and current_cell.ship and ship_safety[ship.id]:
                    row.append(1)
                else:
                    row.append(0)
            surroundings.append(row)


        for n, direction in enumerate(direction_Order):
            position_Dict[direction] = position_Options[n]

        for direction in position_Dict:
            position = game_map.normalize(position_Dict[direction])
            halite_amount = game_map[position].halite_amount

            if direction == Direction.Still:
                if surroundings[2][1] == 1:
                    dangerous_positions.append((0, 0))
                    dangerous_positions.append((-1, 0))
                if surroundings[3][2] == 1:
                    dangerous_positions.append((0, 0))
                    dangerous_positions.append((0, 1))
                if surroundings[2][3] == 1:
                    dangerous_positions.append((0, 0))
                    dangerous_positions.append((1, 0))
                if surroundings[1][2] == 1:
                    dangerous_positions.append((0, 0))
                    dangerous_positions.append((0, -1))
            elif direction == Direction.East:
                if surroundings[1][3] == 1:
                    dangerous_positions.append((1, 0))
                if surroundings[2][3] == 1:
                    dangerous_positions.append((1, 0))
                if surroundings[3][3] == 1:
                    dangerous_positions.append((1, 0))
                if surroundings[2][4] == 1:
                    dangerous_positions.append((1, 0))
            elif direction == Direction.West:
                if surroundings[1][1] == 1:
                    dangerous_positions.append((-1, 0))
                if surroundings[2][1] == 1:
                    dangerous_positions.append((-1, 0))
                if surroundings[3][1] == 1:
                    dangerous_positions.append((-1, 0))
                if surroundings[2][0] == 1:
                    dangerous_positions.append((-1, 0))
            elif direction == Direction.North:
                if surroundings[1][1] == 1:
                    dangerous_positions.append((0, -1))
                if surroundings[1][2] == 1:
                    dangerous_positions.append((0, -1))
                if surroundings[1][3] == 1:
                    dangerous_positions.append((0, -1))
                if surroundings[0][2] == 1:
                    dangerous_positions.append((0, -1))
            elif direction == Direction.South:
                if surroundings[3][1] == 1:
                    dangerous_positions.append((0, 1))
                if surroundings[3][2] == 1:
                    dangerous_positions.append((0, 1))
                if surroundings[3][3] == 1:
                    dangerous_positions.append((0, 1))
                if surroundings[4][2] == 1:
                    dangerous_positions.append((0, 1))

            if game_map.normalize(position_Dict[direction]) not in position_Choices:

                if direction == Direction.Still:
                    halite_Dict[direction] = max(0, halite_amount - ignore_Halite) ** still_Multiplier
                else:
                    halite_Dict[direction] = max(0, halite_amount - ignore_Halite) + 0.001 * halite_amount
                
        #logging.info(f"ship {ship.id} has those dangerous moves:")
        #for each_dangerous_move in dangerous_positions:
            #logging.info(f"move {each_dangerous_move[0]}, {each_dangerous_move[1]} ")

        if game_map[ship.position].halite_amount * 0.1 > ship.halite_amount:
            move = (0, 0)
            position_Choices.append(game_map.normalize(position_Dict[move]))
            command_queue.append(ship.move(move))
            ship_States[ship.id] = "pinned"

        if ship_States[ship.id] == "time_to_get_home" and game_map.calculate_distance(ship.position, me.shipyard.position) > 1:
            smarter_naive_navigate_moves = game_map.smarter_naive_navigate_2(ship, me.shipyard.position, position_Choices)
            if len(smarter_naive_navigate_moves) == 1:
                smarter_naive_navigate_move_0 = smarter_naive_navigate_moves[0]
                smarter_naive_navigate_move_1 = smarter_naive_navigate_moves[0]
            elif len(smarter_naive_navigate_moves) == 2:
                smarter_naive_navigate_move_0 = smarter_naive_navigate_moves[0]
                smarter_naive_navigate_move_1 = smarter_naive_navigate_moves[1]

            try:
                halite_Dict_move_0_exist = halite_Dict[smarter_naive_navigate_move_0]
                halite_Dict_move_0_exist = True
            except KeyError:
                halite_Dict_move_0_exist = False
            try:
                halite_Dict_move_1_exist = halite_Dict[smarter_naive_navigate_move_1]
                halite_Dict_move_1_exist = True
            except KeyError:
                halite_Dict_move_1_exist = False

            if not halite_Dict:
                #accept collision (no where to go), should be changed later on
                move = Direction.Still
            elif smarter_naive_navigate_move_0 == (0, 0):
                if game_map.normalize(position_Dict[smarter_naive_navigate_move_0]) not in position_Choices:
                    move = smarter_naive_navigate_move_0
                else:
                    if (0, 0) not in dangerous_positions and game_map.normalize(position_Dict[(0, 0)]) not in position_Choices:
                        move = Direction.Still
                    elif (0, 1) not in dangerous_positions and game_map.normalize(position_Dict[(0, 1)]) not in position_Choices:
                        move = Direction.South
                    elif (1, 0) not in dangerous_positions and game_map.normalize(position_Dict[(1, 0)]) not in position_Choices:
                        move = Direction.East
                    elif (-1, 0) not in dangerous_positions and game_map.normalize(position_Dict[(-1, 0)]) not in position_Choices:
                        move = Direction.West
                    elif (0, -1) not in dangerous_positions and game_map.normalize(position_Dict[(0, -1)]) not in position_Choices:
                        move = Direction.North
                    elif game_map.normalize(position_Dict[(0, 1)]) not in position_Choices:
                        move = Direction.South
                    elif game_map.normalize(position_Dict[(1, 0)]) not in position_Choices:
                        move = Direction.East
                    elif game_map.normalize(position_Dict[(-1, 0)]) not in position_Choices:
                        move = Direction.West
                    elif game_map.normalize(position_Dict[(0, -1)]) not in position_Choices:
                        move = Direction.North
                    elif game_map.normalize(position_Dict[(0, 0)]) not in position_Choices:
                        move = Direction.Still
                    else:
                        move = Direction.Still
            elif halite_Dict_move_0_exist and halite_Dict_move_1_exist:
                if halite_Dict[smarter_naive_navigate_move_0] <= halite_Dict[smarter_naive_navigate_move_1] and game_map.normalize(position_Dict[smarter_naive_navigate_move_0]) not in position_Choices and smarter_naive_navigate_move_0 not in dangerous_positions:
                    move = smarter_naive_navigate_move_0
                elif game_map.normalize(position_Dict[smarter_naive_navigate_move_1]) not in position_Choices and smarter_naive_navigate_move_1 not in dangerous_positions:
                    move = smarter_naive_navigate_move_1
                else:
                    if (0, 0) not in dangerous_positions and game_map.normalize(position_Dict[(0, 0)]) not in position_Choices:
                        move = Direction.Still
                    elif (0, 1) not in dangerous_positions and game_map.normalize(position_Dict[(0, 1)]) not in position_Choices:
                        move = Direction.South
                    elif (1, 0) not in dangerous_positions and game_map.normalize(position_Dict[(1, 0)]) not in position_Choices:
                        move = Direction.East
                    elif (-1, 0) not in dangerous_positions and game_map.normalize(position_Dict[(-1, 0)]) not in position_Choices:
                        move = Direction.West
                    elif (0, -1) not in dangerous_positions and game_map.normalize(position_Dict[(0, -1)]) not in position_Choices:
                        move = Direction.North
                    elif game_map.normalize(position_Dict[(0, 1)]) not in position_Choices:
                        move = Direction.South
                    elif game_map.normalize(position_Dict[(1, 0)]) not in position_Choices:
                        move = Direction.East
                    elif game_map.normalize(position_Dict[(-1, 0)]) not in position_Choices:
                        move = Direction.West
                    elif game_map.normalize(position_Dict[(0, -1)]) not in position_Choices:
                        move = Direction.North
                    elif game_map.normalize(position_Dict[(0, 0)]) not in position_Choices:
                        move = Direction.Still
                    else:
                        move = Direction.Still
            elif halite_Dict_move_1_exist:
                if game_map.normalize(position_Dict[smarter_naive_navigate_move_1]) not in position_Choices and smarter_naive_navigate_move_1 not in dangerous_positions:
                    move = smarter_naive_navigate_move_1
                else:
                    if (0, 0) not in dangerous_positions and game_map.normalize(position_Dict[(0, 0)]) not in position_Choices:
                        move = Direction.Still
                    elif (0, 1) not in dangerous_positions and game_map.normalize(position_Dict[(0, 1)]) not in position_Choices:
                        move = Direction.South
                    elif (1, 0) not in dangerous_positions and game_map.normalize(position_Dict[(1, 0)]) not in position_Choices:
                        move = Direction.East
                    elif (-1, 0) not in dangerous_positions and game_map.normalize(position_Dict[(-1, 0)]) not in position_Choices:
                        move = Direction.West
                    elif (0, -1) not in dangerous_positions and game_map.normalize(position_Dict[(0, -1)]) not in position_Choices:
                        move = Direction.North
                    elif game_map.normalize(position_Dict[(0, 1)]) not in position_Choices:
                        move = Direction.South
                    elif game_map.normalize(position_Dict[(1, 0)]) not in position_Choices:
                        move = Direction.East
                    elif game_map.normalize(position_Dict[(-1, 0)]) not in position_Choices:
                        move = Direction.West
                    elif game_map.normalize(position_Dict[(0, -1)]) not in position_Choices:
                        move = Direction.North
                    elif game_map.normalize(position_Dict[(0, 0)]) not in position_Choices:
                        move = Direction.Still
                    else:
                        move = Direction.Still
            else:
                if (0, 0) not in dangerous_positions and game_map.normalize(position_Dict[(0, 0)]) not in position_Choices:
                    move = Direction.Still
                elif (0, 1) not in dangerous_positions and game_map.normalize(position_Dict[(0, 1)]) not in position_Choices:
                    move = Direction.South
                elif (1, 0) not in dangerous_positions and game_map.normalize(position_Dict[(1, 0)]) not in position_Choices:
                        move = Direction.East
                elif (-1, 0) not in dangerous_positions and game_map.normalize(position_Dict[(-1, 0)]) not in position_Choices:
                    move = Direction.West
                elif (0, -1) not in dangerous_positions and game_map.normalize(position_Dict[(0, -1)]) not in position_Choices:
                        move = Direction.North
                elif game_map.normalize(position_Dict[(0, 1)]) not in position_Choices:
                        move = Direction.South
                elif game_map.normalize(position_Dict[(1, 0)]) not in position_Choices:
                    move = Direction.East
                elif game_map.normalize(position_Dict[(-1, 0)]) not in position_Choices:
                    move = Direction.West
                elif game_map.normalize(position_Dict[(0, -1)]) not in position_Choices:
                    move = Direction.North
                elif game_map.normalize(position_Dict[(0, 0)]) not in position_Choices:
                    move = Direction.Still
                else:
                    move = Direction.Still
                    
            position_Choices.append(game_map.normalize(position_Dict[move]))
            command_queue.append(ship.move(move))

        if ship_States[ship.id] == "time_to_get_home" and game_map.calculate_distance(ship.position, me.shipyard.position) == 1:
            move = game_map.suicide_in_base(ship, me.shipyard.position)
            command_queue.append(ship.move(move))
        elif ship_States[ship.id] == "time_to_get_home" and game_map.calculate_distance(ship.position, me.shipyard.position) == 0:
            command_queue.append(ship.move((0, 0)))

        if ship_States[ship.id] == "depositing" and ship.position != me.shipyard.position:
            smarter_naive_navigate_moves = game_map.smarter_naive_navigate_2(ship, me.shipyard.position, position_Choices)
            if len(smarter_naive_navigate_moves) == 1:
                smarter_naive_navigate_move_0 = smarter_naive_navigate_moves[0]
                smarter_naive_navigate_move_1 = smarter_naive_navigate_moves[0]
            elif len(smarter_naive_navigate_moves) == 2:
                smarter_naive_navigate_move_0 = smarter_naive_navigate_moves[0]
                smarter_naive_navigate_move_1 = smarter_naive_navigate_moves[1]

            try:
                halite_Dict_move_0_exist = halite_Dict[smarter_naive_navigate_move_0]
                halite_Dict_move_0_exist = True
            except KeyError:
                halite_Dict_move_0_exist = False
            try:
                halite_Dict_move_1_exist = halite_Dict[smarter_naive_navigate_move_1]
                halite_Dict_move_1_exist = True
            except KeyError:
                halite_Dict_move_1_exist = False

            if not halite_Dict:
                #accept collision (no where to go), should be changed later on
                move = Direction.Still
            elif smarter_naive_navigate_move_0 == (0, 0):
                if game_map.normalize(position_Dict[smarter_naive_navigate_move_0]) not in position_Choices:
                    move = smarter_naive_navigate_move_0
                else:
                    if (0, 0) not in dangerous_positions and game_map.normalize(position_Dict[(0, 0)]) not in position_Choices:
                        move = Direction.Still
                    elif (0, 1) not in dangerous_positions and game_map.normalize(position_Dict[(0, 1)]) not in position_Choices:
                        move = Direction.South
                    elif (1, 0) not in dangerous_positions and game_map.normalize(position_Dict[(1, 0)]) not in position_Choices:
                        move = Direction.East
                    elif (-1, 0) not in dangerous_positions and game_map.normalize(position_Dict[(-1, 0)]) not in position_Choices:
                        move = Direction.West
                    elif (0, -1) not in dangerous_positions and game_map.normalize(position_Dict[(0, -1)]) not in position_Choices:
                        move = Direction.North
                    elif game_map.normalize(position_Dict[(0, 1)]) not in position_Choices:
                        move = Direction.South
                    elif game_map.normalize(position_Dict[(1, 0)]) not in position_Choices:
                        move = Direction.East
                    elif game_map.normalize(position_Dict[(-1, 0)]) not in position_Choices:
                        move = Direction.West
                    elif game_map.normalize(position_Dict[(0, -1)]) not in position_Choices:
                        move = Direction.North
                    elif game_map.normalize(position_Dict[(0, 0)]) not in position_Choices:
                        move = Direction.Still
                    else:
                        move = Direction.Still
            elif halite_Dict_move_0_exist and halite_Dict_move_1_exist:
                if halite_Dict[smarter_naive_navigate_move_0] <= halite_Dict[smarter_naive_navigate_move_1] and game_map.normalize(position_Dict[smarter_naive_navigate_move_0]) not in position_Choices and smarter_naive_navigate_move_0 not in dangerous_positions:
                    move = smarter_naive_navigate_move_0
                elif game_map.normalize(position_Dict[smarter_naive_navigate_move_1]) not in position_Choices and smarter_naive_navigate_move_1 not in dangerous_positions:
                    move = smarter_naive_navigate_move_1
                else:
                    if (0, 0) not in dangerous_positions and game_map.normalize(position_Dict[(0, 0)]) not in position_Choices:
                        move = Direction.Still
                    elif (0, 1) not in dangerous_positions and game_map.normalize(position_Dict[(0, 1)]) not in position_Choices:
                        move = Direction.South
                    elif (1, 0) not in dangerous_positions and game_map.normalize(position_Dict[(1, 0)]) not in position_Choices:
                        move = Direction.East
                    elif (-1, 0) not in dangerous_positions and game_map.normalize(position_Dict[(-1, 0)]) not in position_Choices:
                        move = Direction.West
                    elif (0, -1) not in dangerous_positions and game_map.normalize(position_Dict[(0, -1)]) not in position_Choices:
                        move = Direction.North
                    elif game_map.normalize(position_Dict[(0, 1)]) not in position_Choices:
                        move = Direction.South
                    elif game_map.normalize(position_Dict[(1, 0)]) not in position_Choices:
                        move = Direction.East
                    elif game_map.normalize(position_Dict[(-1, 0)]) not in position_Choices:
                        move = Direction.West
                    elif game_map.normalize(position_Dict[(0, -1)]) not in position_Choices:
                        move = Direction.North
                    elif game_map.normalize(position_Dict[(0, 0)]) not in position_Choices:
                        move = Direction.Still
                    else:
                        move = Direction.Still
            elif halite_Dict_move_1_exist:
                if game_map.normalize(position_Dict[smarter_naive_navigate_move_1]) not in position_Choices and smarter_naive_navigate_move_1 not in dangerous_positions:
                    move = smarter_naive_navigate_move_1
                else:
                    if (0, 0) not in dangerous_positions and game_map.normalize(position_Dict[(0, 0)]) not in position_Choices:
                        move = Direction.Still
                    elif (0, 1) not in dangerous_positions and game_map.normalize(position_Dict[(0, 1)]) not in position_Choices:
                        move = Direction.South
                    elif (1, 0) not in dangerous_positions and game_map.normalize(position_Dict[(1, 0)]) not in position_Choices:
                        move = Direction.East
                    elif (-1, 0) not in dangerous_positions and game_map.normalize(position_Dict[(-1, 0)]) not in position_Choices:
                        move = Direction.West
                    elif (0, -1) not in dangerous_positions and game_map.normalize(position_Dict[(0, -1)]) not in position_Choices:
                        move = Direction.North
                    elif game_map.normalize(position_Dict[(0, 1)]) not in position_Choices:
                        move = Direction.South
                    elif game_map.normalize(position_Dict[(1, 0)]) not in position_Choices:
                        move = Direction.East
                    elif game_map.normalize(position_Dict[(-1, 0)]) not in position_Choices:
                        move = Direction.West
                    elif game_map.normalize(position_Dict[(0, -1)]) not in position_Choices:
                        move = Direction.North
                    elif game_map.normalize(position_Dict[(0, 0)]) not in position_Choices:
                        move = Direction.Still
                    else:
                        move = Direction.Still
            else:
                if (0, 0) not in dangerous_positions and game_map.normalize(position_Dict[(0, 0)]) not in position_Choices:
                    move = Direction.Still
                elif (0, 1) not in dangerous_positions and game_map.normalize(position_Dict[(0, 1)]) not in position_Choices:
                    move = Direction.South
                elif (1, 0) not in dangerous_positions and game_map.normalize(position_Dict[(1, 0)]) not in position_Choices:
                    move = Direction.East
                elif (-1, 0) not in dangerous_positions and game_map.normalize(position_Dict[(-1, 0)]) not in position_Choices:
                    move = Direction.West
                elif (0, -1) not in dangerous_positions and game_map.normalize(position_Dict[(0, -1)]) not in position_Choices:
                    move = Direction.North
                elif game_map.normalize(position_Dict[(0, 1)]) not in position_Choices:
                    move = Direction.South
                elif game_map.normalize(position_Dict[(1, 0)]) not in position_Choices:
                    move = Direction.East
                elif game_map.normalize(position_Dict[(-1, 0)]) not in position_Choices:
                    move = Direction.West
                elif game_map.normalize(position_Dict[(0, -1)]) not in position_Choices:
                    move = Direction.North
                elif game_map.normalize(position_Dict[(0, 0)]) not in position_Choices:
                    move = Direction.Still
                else:
                    move = Direction.Still

            position_Choices.append(game_map.normalize(position_Dict[move]))
            command_queue.append(ship.move(move))
                 
        elif ship_States[ship.id] == "depositing" and ship.position == me.shipyard.position:
                ship_States[ship.id] = "collecting"

        if ship_States[ship.id] == "collecting":
            
            if ship_killing_possibility[ship.id] != (99, 99):
                try:
                    if game_map.normalize(position_Dict[ship_killing_possibility[ship.id]]) not in position_Choices:
                        killing_move_is_available = True
                    else:
                        killing_move_is_available = False
                except KeyError:
                    killing_move_is_available = False
            else:
                killing_move_is_available = False

            if not halite_Dict:
                #accept collision (no where to go), should be changed later on
                move = Direction.Still
            elif killing_move_is_available:
                move = ship_killing_possibility[ship.id]
                logging.info('trying to kill')
            elif ship_in_dead_zone[ship.id] and game_phase == 'gathering' :

                max_halite_zone = 0
                if ship.id not in direction_of_interest:
                    for each_interesting_coord in interesting_coords:
                        temp_sum = 0    
                        for yy in range(-1*window + each_interesting_coord[1], each_interesting_coord[1] + window+1):
                            for xx in range(-1*window + each_interesting_coord[0], each_interesting_coord[0] + window+1):
                                temp_sum += game_map[Position(xx,yy)].halite_amount * (1 - (game_map.calculate_distance(Position(each_interesting_coord[0],each_interesting_coord[1]), ship.position ) / (map_Settings[constants.MAX_TURNS]*1.5)))
                        #temp_row.append(int(temp_sum))
                        if temp_sum > max_halite_zone:
                            max_halite_zone = temp_sum
                            direction_of_interest[ship.id] = game_map.normalize(Position(each_interesting_coord[0],each_interesting_coord[1]))
                    ZONE_OF_INTEREST.append(direction_of_interest[ship.id])

                smarter_naive_navigate_moves = game_map.smarter_naive_navigate_2(ship, direction_of_interest[ship.id], position_Choices)
                if len(smarter_naive_navigate_moves) == 1:
                    smarter_naive_navigate_move_0 = smarter_naive_navigate_moves[0]
                    smarter_naive_navigate_move_1 = smarter_naive_navigate_moves[0]
                elif len(smarter_naive_navigate_moves) == 2:
                    smarter_naive_navigate_move_0 = smarter_naive_navigate_moves[0]
                    smarter_naive_navigate_move_1 = smarter_naive_navigate_moves[1]

                try:
                    halite_Dict_move_0_exist = halite_Dict[smarter_naive_navigate_move_0]
                    halite_Dict_move_0_exist = True
                except KeyError:
                    halite_Dict_move_0_exist = False
                try:
                    halite_Dict_move_1_exist = halite_Dict[smarter_naive_navigate_move_1]
                    halite_Dict_move_1_exist = True
                except KeyError:
                    halite_Dict_move_1_exist = False

                if not halite_Dict:
                    #accept collision (no where to go), should be changed later on
                    move = Direction.Still
                elif smarter_naive_navigate_move_0 == (0, 0):
                    if game_map.normalize(position_Dict[smarter_naive_navigate_move_0]) not in position_Choices:
                        move = smarter_naive_navigate_move_0
                    else:
                        if (0, 0) not in dangerous_positions and game_map.normalize(position_Dict[(0, 0)]) not in position_Choices:
                            move = Direction.Still
                        elif (0, 1) not in dangerous_positions and game_map.normalize(position_Dict[(0, 1)]) not in position_Choices:
                            move = Direction.South
                        elif (1, 0) not in dangerous_positions and game_map.normalize(position_Dict[(1, 0)]) not in position_Choices:
                            move = Direction.East
                        elif (-1, 0) not in dangerous_positions and game_map.normalize(position_Dict[(-1, 0)]) not in position_Choices:
                            move = Direction.West
                        elif (0, -1) not in dangerous_positions and game_map.normalize(position_Dict[(0, -1)]) not in position_Choices:
                            move = Direction.North
                        elif game_map.normalize(position_Dict[(0, 1)]) not in position_Choices:
                            move = Direction.South
                        elif game_map.normalize(position_Dict[(1, 0)]) not in position_Choices:
                            move = Direction.East
                        elif game_map.normalize(position_Dict[(-1, 0)]) not in position_Choices:
                            move = Direction.West
                        elif game_map.normalize(position_Dict[(0, -1)]) not in position_Choices:
                            move = Direction.North
                        elif game_map.normalize(position_Dict[(0, 0)]) not in position_Choices:
                            move = Direction.Still
                        else:
                            move = Direction.Still
                elif halite_Dict_move_0_exist and halite_Dict_move_1_exist:
                    if halite_Dict[smarter_naive_navigate_move_0] <= halite_Dict[smarter_naive_navigate_move_1] and game_map.normalize(position_Dict[smarter_naive_navigate_move_0]) not in position_Choices and smarter_naive_navigate_move_0 not in dangerous_positions:
                        move = smarter_naive_navigate_move_0
                    elif game_map.normalize(position_Dict[smarter_naive_navigate_move_1]) not in position_Choices and smarter_naive_navigate_move_1 not in dangerous_positions:
                        move = smarter_naive_navigate_move_1
                    else:
                        if (0, 0) not in dangerous_positions and game_map.normalize(position_Dict[(0, 0)]) not in position_Choices:
                            move = Direction.Still
                        elif (0, 1) not in dangerous_positions and game_map.normalize(position_Dict[(0, 1)]) not in position_Choices:
                            move = Direction.South
                        elif (1, 0) not in dangerous_positions and game_map.normalize(position_Dict[(1, 0)]) not in position_Choices:
                            move = Direction.East
                        elif (-1, 0) not in dangerous_positions and game_map.normalize(position_Dict[(-1, 0)]) not in position_Choices:
                            move = Direction.West
                        elif (0, -1) not in dangerous_positions and game_map.normalize(position_Dict[(0, -1)]) not in position_Choices:
                            move = Direction.North
                        elif game_map.normalize(position_Dict[(0, 1)]) not in position_Choices:
                            move = Direction.South
                        elif game_map.normalize(position_Dict[(1, 0)]) not in position_Choices:
                            move = Direction.East
                        elif game_map.normalize(position_Dict[(-1, 0)]) not in position_Choices:
                            move = Direction.West
                        elif game_map.normalize(position_Dict[(0, -1)]) not in position_Choices:
                            move = Direction.North
                        elif game_map.normalize(position_Dict[(0, 0)]) not in position_Choices:
                            move = Direction.Still
                        else:
                            move = Direction.Still
                elif halite_Dict_move_1_exist:
                    if game_map.normalize(position_Dict[smarter_naive_navigate_move_1]) not in position_Choices and smarter_naive_navigate_move_1 not in dangerous_positions:
                        move = smarter_naive_navigate_move_1
                    else:
                        if (0, 0) not in dangerous_positions and game_map.normalize(position_Dict[(0, 0)]) not in position_Choices:
                            move = Direction.Still
                        elif (0, 1) not in dangerous_positions and game_map.normalize(position_Dict[(0, 1)]) not in position_Choices:
                            move = Direction.South
                        elif (1, 0) not in dangerous_positions and game_map.normalize(position_Dict[(1, 0)]) not in position_Choices:
                            move = Direction.East
                        elif (-1, 0) not in dangerous_positions and game_map.normalize(position_Dict[(-1, 0)]) not in position_Choices:
                            move = Direction.West
                        elif (0, -1) not in dangerous_positions and game_map.normalize(position_Dict[(0, -1)]) not in position_Choices:
                            move = Direction.North
                        elif game_map.normalize(position_Dict[(0, 1)]) not in position_Choices:
                            move = Direction.South
                        elif game_map.normalize(position_Dict[(1, 0)]) not in position_Choices:
                            move = Direction.East
                        elif game_map.normalize(position_Dict[(-1, 0)]) not in position_Choices:
                            move = Direction.West
                        elif game_map.normalize(position_Dict[(0, -1)]) not in position_Choices:
                            move = Direction.North
                        elif game_map.normalize(position_Dict[(0, 0)]) not in position_Choices:
                            move = Direction.Still
                        else:
                            move = Direction.Still
                else:
                    if (0, 0) not in dangerous_positions and game_map.normalize(position_Dict[(0, 0)]) not in position_Choices:
                        move = Direction.Still
                    elif (0, 1) not in dangerous_positions and game_map.normalize(position_Dict[(0, 1)]) not in position_Choices:
                        move = Direction.South
                    elif (1, 0) not in dangerous_positions and game_map.normalize(position_Dict[(1, 0)]) not in position_Choices:
                            move = Direction.East
                    elif (-1, 0) not in dangerous_positions and game_map.normalize(position_Dict[(-1, 0)]) not in position_Choices:
                        move = Direction.West
                    elif (0, -1) not in dangerous_positions and game_map.normalize(position_Dict[(0, -1)]) not in position_Choices:
                            move = Direction.North
                    elif game_map.normalize(position_Dict[(0, 1)]) not in position_Choices:
                        move = Direction.South
                    elif game_map.normalize(position_Dict[(1, 0)]) not in position_Choices:
                        move = Direction.East
                    elif game_map.normalize(position_Dict[(-1, 0)]) not in position_Choices:
                        move = Direction.West
                    elif game_map.normalize(position_Dict[(0, -1)]) not in position_Choices:
                        move = Direction.North
                    elif game_map.normalize(position_Dict[(0, 0)]) not in position_Choices:
                        move = Direction.Still
                    else:
                        move = Direction.Still
            else:
                if ship.id in direction_of_interest:
                    remove_position = direction_of_interest.pop('key', None)
                    if remove_position != None:
                        ZONE_OF_INTEREST.remove(remove_position)

                if max(halite_Dict, key=halite_Dict.get) not in dangerous_positions and game_map.normalize(position_Dict[max(halite_Dict, key=halite_Dict.get)]) not in position_Choices:
                    move = max(halite_Dict, key=halite_Dict.get)
                elif min(halite_Dict, key=halite_Dict.get) not in dangerous_positions and game_map.normalize(position_Dict[max(halite_Dict, key=halite_Dict.get)]) not in position_Choices:
                    move = min(halite_Dict, key=halite_Dict.get)
                elif (0, -1) not in dangerous_positions and game_map.normalize(position_Dict[(0, -1)]) not in position_Choices:
                    move = Direction.North
                elif (0, 1) not in dangerous_positions and game_map.normalize(position_Dict[(0, 1)]) not in position_Choices:
                    move = Direction.South
                elif (1, 0) not in dangerous_positions and game_map.normalize(position_Dict[(1, 0)]) not in position_Choices:
                    move = Direction.East
                elif (-1, 0) not in dangerous_positions and game_map.normalize(position_Dict[(-1, 0)]) not in position_Choices:
                    move = Direction.West
                elif game_map.normalize(position_Dict[(0, 1)]) not in position_Choices:
                    move = Direction.South
                elif game_map.normalize(position_Dict[(1, 0)]) not in position_Choices:
                    move = Direction.East
                elif game_map.normalize(position_Dict[(-1, 0)]) not in position_Choices:
                    move = Direction.West
                elif game_map.normalize(position_Dict[(0, -1)]) not in position_Choices:
                    move = Direction.North
                elif game_map.normalize(position_Dict[(0, 0)]) not in position_Choices:
                    move = Direction.Still
                else:
                    move = Direction.Still

            position_Choices.append(game_map.normalize(position_Dict[move]))
            command_queue.append(ship.move(move))

            if ship.halite_amount > constants.MAX_HALITE * 0.9 and game_phase == 'gathering' :
                ship_States[ship.id] = "depositing"
                if ship.id in direction_of_interest:
                    remove_position = direction_of_interest.pop('key', None)
                    if remove_position != None:
                        ZONE_OF_INTEREST.remove(remove_position)
            elif ship.halite_amount > constants.MAX_HALITE * 0.5 and game_phase == 'secure_halite' :
                ship_States[ship.id] = "depositing"
                if ship.id in direction_of_interest:
                    remove_position = direction_of_interest.pop('key', None)
                    if remove_position != None:
                        ZONE_OF_INTEREST.remove(remove_position)

        if ship_States[ship.id] == "pinned":
            ship_States[ship.id] = "collecting"

    if NUMBER_OF_PLAYERS == 2:
        if game.turn_number <= int(constants.MAX_TURNS*0.75):
            if game_map[me.shipyard].position not in position_Choices:  
                if me.halite_amount >= constants.SHIP_COST and ((current_total_halite / NUMBER_OF_PLAYERS > 50000) or (len(me.get_ships())*1.1 <= (len(p0.get_ships()) + len(p1.get_ships()))/2)):
                        command_queue.append(me.shipyard.spawn())
    else:
        if game.turn_number <= int(constants.MAX_TURNS*0.75):
            if game_map[me.shipyard].position not in position_Choices:  
                if me.halite_amount >= constants.SHIP_COST and ((current_total_halite / NUMBER_OF_PLAYERS > 50000) or (len(me.get_ships()) <= (len(p0.get_ships()) + len(p1.get_ships())+ len(p2.get_ships()) + len(p3.get_ships()) )/4)):
                        command_queue.append(me.shipyard.spawn())

    logging.info(f"Turn {CURRENT_ROUND} took {time.time()-start_time_turn} seconds to compute. We had {len(me.get_ships())} ships .")

    # Send your moves back to the game environment, ending this turn.
    game.end_turn(command_queue)

