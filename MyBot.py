#!/usr/bin/env python3
# Python 3.6

# Import the Halite SDK, which will let you interact with the game.
import hlt
from hlt import constants
from hlt.positionals import Direction
import random
import logging

""" <<<Game Begin>>> """

# This game object contains the initial game state.
game = hlt.Game()
# At this point "game" variable is populated with initial map data.
# This is a good place to do computationally expensive start-up pre-processing.
# As soon as you call "ready" function below, the 2 second per turn timer will start.
game.ready("MyPythonBot")

# Now that your bot is initialized, save a message to yourself in the log file with some important information.
#   Here, you log here your id, which you can always fetch from the game object by using my_id.
logging.info("Successfully created bot! My Player ID is {}.".format(game.my_id))

ship_states = {}

while True:
    # This loop handles each turn of the game. The game object changes every turn, and you refresh that state by
    #   running update_frame().
    game.update_frame()
    # You extract player metadata and the updated map metadata here for convenience.
    me = game.me
    game_map = game.game_map

    # A command queue holds all the commands you will run this turn. You build this list up and submit it at the
    #   end of the turn.
    command_queue = []

    direction_order = [Direction.North, Direction.South, Direction.East, Direction.West, Direction.Still]

    position_choices = []
    for ship in me.get_ships():
        if ship.id not in ship_states:
            ship_states[ship.id] = "collecting"

        position_options = ship.position.get_surrounding_cardinals() + [ship.position]

        position_dict = {}

        halite_dict = {}

        for n, direction in enumerate(direction_order):
            position_dict[direction] = position_options[n]

        for direction in position_dict:
            position = position_dict[direction]
            halite_amount = game_map[position].halite_amount
            if position_dict[direction] not in position_choices:
                if direction == Direction.Still:
                    halite_dict[direction] = halite_amount*3
                else:
                    halite_dict[direction] = halite_amount
            else:
                logging.info("attempting to move to same spot\n")

        # For each of your ships, move randomly if the ship is on a low halite location or the ship is full.
        #   Else, collect halite.
        if ship_states[ship.id] == "depositing":
            move = game_map.naive_navigate(ship, me.shipyard.position)
            position_choices.append(position_dict[move])
            command_queue.append(ship.move(move))
            if move == Direction.Still:
                ship_states[ship.id] = "collecting"

        elif ship_states[ship.id] == "collecting":
            directional_choice = max(halite_dict, key=halite_dict.get)
            position_choices.append(position_dict[directional_choice])
            command_queue.append(ship.move(directional_choice))

            if ship.halite_amount > constants.MAX_HALITE * 0.6:
                ship_states[ship.id] = "depositing"



    # If the game is in the first 200 turns and you have enough halite, spawn a ship.
    # Don't spawn a ship if you currently have a ship at port, though - the ships will collide.
    constants.MAX_TURNS
    if game.turn_number <= 400 and me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied and len(me.get_ships()) < 6:
        command_queue.append(me.shipyard.spawn())

    # Send your moves back to the game environment, ending this turn.
    game.end_turn(command_queue)

