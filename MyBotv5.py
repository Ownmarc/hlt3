#!/usr/bin/env python3
# Python 3.6
import hlt
from hlt import constants
from hlt.positionals import Direction
import random
import logging

# This game object contains the initial game state.
game = hlt.Game()
# At this point "game" variable is populated with initial map data.
# This is a good place to do computationally expensive start-up pre-processing.
# As soon as you call "ready" function below, the 2 second per turn timer will start.
game.ready("MyBotv5")

# Here, you log here your id, which you can always fetch from the game object by using my_id.
logging.info("Successfully created bot! My Player ID is {}.".format(game.my_id))

ship_States = {}
CURRENT_ROUND = 0

while True:
    CURRENT_ROUND += 1
    # This loop handles each turn of the game. The game object changes every turn, and you refresh that state by
    #   running update_frame().
    game.update_frame()
    # You extract player metadata and the updated map metadata here for convenience.
    me = game.me
    game_map = game.game_map

    # A command queue holds all the commands you will run this turn. You build this list up and submit it at the
    #   end of the turn.
    command_queue = []
    direction_Order = [Direction.North, Direction.South, Direction.East, Direction.West, Direction.Still]
    position_Choices = []

    ship_In_Priority_Order = []
    ship_Priority_1 = []
    ship_Priority_2 = []
    ship_Priority_3 = []
    ship_Priority_4 = []

    #Calculate the distance between all ships and the shipyard
    for ship in me.get_ships():
        distance_from_shipyard = game_map.calculate_distance(ship.position, me.shipyard.position)
        if distance_from_shipyard + 20 > constants.MAX_TURNS - CURRENT_ROUND:
            if random.randint(0, distance_from_shipyard) >= int(distance_from_shipyard*0.75):
                ship_States[ship.id] = "time_to_get_home"
        if distance_from_shipyard + 2 > constants.MAX_TURNS - CURRENT_ROUND:
            ship_States[ship.id] = "time_to_get_home"

    for ship in me.get_ships():
        position_Options = ship.position.get_surrounding_cardinals() + [ship.position]
        position_Dict = {}
        halite_Dict = {}

        if ship.id not in ship_States:
            ship_States[ship.id] = "collecting"

        for n, direction in enumerate(direction_Order):
            position_Dict[direction] = position_Options[n]

        for direction in position_Dict:
            position = position_Dict[direction]
            halite_amount = game_map[position].halite_amount
            if position_Dict[direction] not in position_Choices:
                if direction == Direction.Still:
                    halite_Dict[direction] = halite_amount**1.3
                else:
                    halite_Dict[direction] = halite_amount + 1
            else:
                logging.info("attempting to move to same spot\n")

        if game_map[ship.position].halite_amount * 0.1 > ship.halite_amount:
            ship_States[ship.id] = "pinned"

        if not halite_Dict or ship_States[ship.id] == "pinned":
            ship_Priority_1.append(ship)
        elif ship_States[ship.id] == "depositing":
            ship_Priority_2.append(ship)
        elif ship_States[ship.id] == "collecting":
            ship_Priority_3.append(ship)
        else:
            ship_Priority_4.append(ship)

    for single_ship in ship_Priority_1:
        ship_In_Priority_Order.append(single_ship)
    for single_ship in ship_Priority_2:
        ship_In_Priority_Order.append(single_ship)
    for single_ship in ship_Priority_3:
        ship_In_Priority_Order.append(single_ship)
    for single_ship in ship_Priority_4:
        ship_In_Priority_Order.append(single_ship)

    for ship in ship_In_Priority_Order:
        position_Options = ship.position.get_surrounding_cardinals() + [ship.position]
        position_Dict = {}
        halite_Dict = {}

        for n, direction in enumerate(direction_Order):
            position_Dict[direction] = position_Options[n]

        for direction in position_Dict:
            position = position_Dict[direction]
            halite_amount = game_map[position].halite_amount
            if position_Dict[direction] not in position_Choices:
                if direction == Direction.Still:
                    halite_Dict[direction] = halite_amount**1.3
                else:
                    halite_Dict[direction] = halite_amount + 1

        if game_map[ship.position].halite_amount * 0.1 > ship.halite_amount:
            move = Direction.Still
            position_Choices.append(position_Dict[move])
            command_queue.append(ship.move(move))
            ship_States[ship.id] = "pinned"

    for ship in ship_In_Priority_Order:

        position_Options = ship.position.get_surrounding_cardinals() + [ship.position]
        position_Dict = {}
        halite_Dict = {}

        for n, direction in enumerate(direction_Order):
            position_Dict[direction] = position_Options[n]

        for direction in position_Dict:
            position = position_Dict[direction]
            halite_amount = game_map[position].halite_amount
            if position_Dict[direction] not in position_Choices:
                if direction == Direction.Still:
                    halite_Dict[direction] = halite_amount**1.3
                else:
                    halite_Dict[direction] = halite_amount + 1

        if ship_States[ship.id] == "time_to_get_home" and game_map.calculate_distance(ship.position, me.shipyard.position) > 1:
            smarter_naive_navigate_moves = game_map.smarter_naive_navigate_2(ship, me.shipyard.position, position_Choices)
            logging.info(f"smarter_naive_navigate_moves = {smarter_naive_navigate_moves}\n")
            logging.info(f"check len = {len(smarter_naive_navigate_moves)}\n")
            if len(smarter_naive_navigate_moves) == 1:
                smarter_naive_navigate_move_0 = smarter_naive_navigate_moves[0]
                smarter_naive_navigate_move_1 = smarter_naive_navigate_moves[0]
            elif len(smarter_naive_navigate_moves) == 2:
                smarter_naive_navigate_move_0 = smarter_naive_navigate_moves[0]
                smarter_naive_navigate_move_1 = smarter_naive_navigate_moves[1]

            #logging.info(f"smarter_naive_navigate_move = {smarter_naive_navigate_move}\n")

            if not halite_Dict:
                #accept collision (no where to go), should be changed later on
                move = (0, 0)
                position_Choices.append(position_Dict[move])
                command_queue.append(ship.move(move))
            elif position_Dict[smarter_naive_navigate_move_0] not in position_Choices:
                position_Choices.append(position_Dict[smarter_naive_navigate_move_0])
                command_queue.append(ship.move(smarter_naive_navigate_move_0))
            elif position_Dict[smarter_naive_navigate_move_1] not in position_Choices:
                position_Choices.append(position_Dict[smarter_naive_navigate_move_1])
                command_queue.append(ship.move(smarter_naive_navigate_move_1))
            else:
                move = list(halite_Dict)[0]
                position_Choices.append(position_Dict[move])
                command_queue.append(ship.move(move))

        if ship_States[ship.id] == "time_to_get_home" and game_map.calculate_distance(ship.position, me.shipyard.position) == 1:
            move = game_map.suicide_in_base(ship, me.shipyard.position)
            command_queue.append(ship.move(move))

        if ship_States[ship.id] == "time_to_get_home" and game_map.calculate_distance(ship.position, me.shipyard.position) == 0:
            command_queue.append(ship.move((0, 0)))




    for ship in ship_In_Priority_Order:

        position_Options = ship.position.get_surrounding_cardinals() + [ship.position]
        position_Dict = {}
        halite_Dict = {}

        for n, direction in enumerate(direction_Order):
            position_Dict[direction] = position_Options[n]

        for direction in position_Dict:
            position = position_Dict[direction]
            halite_amount = game_map[position].halite_amount
            if position_Dict[direction] not in position_Choices:
                if direction == Direction.Still:
                    halite_Dict[direction] = halite_amount**1.3
                else:
                    halite_Dict[direction] = halite_amount + 1


        if ship_States[ship.id] == "depositing" and ship.position != me.shipyard.position:
            smarter_naive_navigate_moves = game_map.smarter_naive_navigate_2(ship, me.shipyard.position, position_Choices)
            if len(smarter_naive_navigate_moves) == 1:
                smarter_naive_navigate_move_0 = smarter_naive_navigate_moves[0]
                smarter_naive_navigate_move_1 = smarter_naive_navigate_moves[0]
            elif len(smarter_naive_navigate_moves) == 2:
                smarter_naive_navigate_move_0 = smarter_naive_navigate_moves[0]
                smarter_naive_navigate_move_1 = smarter_naive_navigate_moves[1]
            if not halite_Dict:
                #accept collision (no where to go), should be changed later on
                move = (0, 0)
                position_Choices.append(position_Dict[move])
                command_queue.append(ship.move(move))
            elif position_Dict[smarter_naive_navigate_move_0] not in position_Choices:
                position_Choices.append(position_Dict[smarter_naive_navigate_move_0])
                command_queue.append(ship.move(smarter_naive_navigate_move_0))
            elif position_Dict[smarter_naive_navigate_move_1] not in position_Choices:
                position_Choices.append(position_Dict[smarter_naive_navigate_move_1])
                command_queue.append(ship.move(smarter_naive_navigate_move_1))
            else:
                move = list(halite_Dict)[0]
                position_Choices.append(position_Dict[move])
                command_queue.append(ship.move(move))

            
        elif ship_States[ship.id] == "depositing" and ship.position == me.shipyard.position:
                ship_States[ship.id] = "collecting"


    for ship in ship_In_Priority_Order:
        position_Options = ship.position.get_surrounding_cardinals() + [ship.position]
        position_Dict = {}
        halite_Dict = {}

        for n, direction in enumerate(direction_Order):
            position_Dict[direction] = position_Options[n]

        for direction in position_Dict:
            position = position_Dict[direction]
            halite_amount = game_map[position].halite_amount
            if position_Dict[direction] not in position_Choices:
                if direction == Direction.Still:
                    halite_Dict[direction] = halite_amount**1.3
                else:
                    halite_Dict[direction] = halite_amount + 1

        if ship_States[ship.id] == "collecting":
            if not halite_Dict:
                #accept collision (no where to go), should be changed later on
                move = Direction.Still
            elif max(halite_Dict, key=halite_Dict.get) == 0:
                move = halite_Dict[Direction.North]
            else:
                move = max(halite_Dict, key=halite_Dict.get)

            position_Choices.append(position_Dict[move])
            command_queue.append(ship.move(move))

            if ship.halite_amount > constants.MAX_HALITE * (0.4+(CURRENT_ROUND/(constants.MAX_TURNS)*0.6)):
                ship_States[ship.id] = "depositing"

        if ship_States[ship.id] == "pinned":
            ship_States[ship.id] = "collecting"


    if game.turn_number <= int(constants.MAX_TURNS*0.42) and me.halite_amount >= constants.SHIP_COST and game_map[me.shipyard].position not in position_Choices:
        command_queue.append(me.shipyard.spawn())

    # Send your moves back to the game environment, ending this turn.
    game.end_turn(command_queue)

