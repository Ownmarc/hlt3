import random
import copy
from itertools import product

how_Big = 11 
center_Pos = 5 #how_Big must be even

def make_Map():
	game_Map = [[random.randint(100,500) for i in range(how_Big)] for x in range(how_Big)]
	game_Map[center_Pos][center_Pos] = 0
	print("Here is the map:")
	for y in range(how_Big):
		print(game_Map[y])
	return game_Map

def calculate_Move_Set(moves, tgame_Map):
	move_Dict = {
	"up": [-1, 0],
	"down": [1, 0],
	"right": [0, 1],
	"left": [0, -1],
	"still": [0, 0],
	}

	cargo = 0
	position = [center_Pos, center_Pos]

	for move in moves:
		if move == "still":
			ressources_Collected = round(tgame_Map[position[0]][position[1]] * 0.25)
			cargo = cargo + ressources_Collected
			tgame_Map[position[0]][position[1]] = tgame_Map[position[0]][position[1]] - ressources_Collected
		else:
			ressources_Used = round(tgame_Map[position[0]][position[1]] * 0.10)
			cargo = cargo - ressources_Used
			position = [position[0] + move_Dict[move][0], position[1] + move_Dict[move][1]]
	return cargo

def check_If_Valid(moves):
	ups = moves.count("up")
	downs = moves.count("down")
	rights = moves.count("right")
	lefts = moves.count("left")

	if ups + downs + rights + lefts == 0:
		return False
	elif (ups - downs) == 0 and (rights - lefts) == 0:
		return True
	else:
		return False

def evaluate_All_Paths(max_Moves):
	possible_Moves = ["up", "down", "right", "left", "still"]
	all_valids = []
	to_get_max = []
	to_get_max_ratio = []

	for x in range(0, max_Moves):
		comb = product(possible_Moves, repeat=x)
		for i in comb:
			if "still" not in i:
				continue
			validity = check_If_Valid(i)	
			if validity:
				ress_Collected = calculate_Move_Set(i, copy.deepcopy(game_Map))
				all_valids.append([validity, i, ress_Collected, ress_Collected/len(i)])
				to_get_max.append(ress_Collected)
				to_get_max_ratio.append(ress_Collected/len(i))

	return all_valids, to_get_max, to_get_max_ratio

if __name__ == "__main__":

	game_Map = make_Map()
	array, array_to_find_index, array_to_find_index_ratio = evaluate_All_Paths(11)

	max_index = array_to_find_index.index(max(array_to_find_index))
	print(max_index, array[max_index])

	max_ratio_index = array_to_find_index_ratio.index(max(array_to_find_index_ratio))
	print(max_ratio_index, array[max_ratio_index])






 




