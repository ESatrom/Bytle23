from typing import Tuple
from game.client.user_client import UserClient
from game.common.cook import Cook
from game.common.game_board import GameBoard
from game.common.action import Action
from game.common.cook import Cook
from typing import Tuple
from game.common.enums import *

# Different states for state machine
class State:
    WAITING_FOR_DOUGH = 0
    HAS_DOUGH = 1
    HAS_ROLLED = 2

# Main client class
class Client(UserClient):
    def __init__(self):
        """
        Variables and info you want to save between turns go here
        """
        super().__init__()
        self.state = State.WAITING_FOR_DOUGH
        # What side and x and y bounds are we using (set in start)
        self.is_left_side = None
        self.x_min = None
        self.y_min = 1
        self.x_max = None
        self.y_max = 5

    def team_name(self):
        """
        Return your team name for the engine

        :returns:       Your team name
        """
        return 'Papa Rivard\'s Pizza Professional™'

    def start(self, action: Action, world: GameBoard, cook: Cook):
        """
        Run on the first turn by the take_turn() function

        :param actions:     This is the actions object that you will add effort allocations or decrees to.
        :param world:       Generic world information
        """
        self.check_side(cook)

    def interact_at(self, cook: Cook, targ_pos: Tuple[int, int]) -> ActionType:
        if targ_pos==None:
            return ActionType.none
        man_dist = self.manhattan_distance(cook.position, targ_pos)
        if man_dist > 1:
            return self.move_action(cook.position, targ_pos)
        else:
            return ActionType.interact

    def holding_cooked_pizza(self, cook):
        return True
    def holding_topped_pizza(self, cook):
        return True
    def holding_cooked_pizza(self, cook):
        return True
    def holding_topping(self, cook, type, cut):
        return True
    def holding_sauced_pizza(self, cook):
        return True
    def holding_rolled_pizza(self, cook):
        return True
    def get_donest_pizza(self, world, cook):
        return (0,0)
    def get_combined_pizza(self, world):
        return (0,0)
    def get_combining_pizza(self, world):
        return (0,0)
    def get_dispenser(self, world, cook, ingredient):
        return (0,0)

    def take_turn(self, turn: int, action: Action, world: GameBoard, cook: Cook):
        """
        This is where your bot will decide what to do.

        :param turn:        The current turn of the game.
        :param actions:     This is the actions object that you will add effort allocations or decrees to.
        :param world:       Generic world information
        """
        # Run the start function on turn 1
        if turn == 1:
            self.start(action, world, cook)
        # Check state machine
        if self.holding_cooked_pizza(cook):
            action.chosen_action = self.interact_at(cook, self.scan_board(world, ObjectType.delivery))

        elif self.get_donest_pizza()!=None and self.holding_air():
            action.chosen_action = self.interact_at(cook, self.get_donest_pizza())

        elif self.holding_topped_pizza():
            action.chosen_action = self.interact_at(cook, self.closest_open_oven())

        elif self.get_combined_pizza()!=None:
            action.chosen_action = self.interact_at(cook, self.scan_board(world, ObjectType.combiner))

        elif self.holding_topping(ToppingType.cheese, True):
            action.chosen_action = self.interact_at(cook, self.scan_board(world, ObjectType.combiner))

        elif self.holding_topping(ToppingType.cheese, False):
            action.chosen_action = self.interact_at(cook, self.scan_board(world, ObjectType.cutter))

        elif self.get_combining_pizza()!=None and self.get_dispenser(world, cook, ToppingType.cheese):
            action.chosen_action = self.interact_at(cook, self.get_dispenser(world, cook, ToppingType.cheese))

        elif self.holding_sauced_pizza():
            action.chosen_action = self.interact_at(cook, self.scan_board(world, ObjectType.combiner))

        elif self.holding_rolled_pizza():
            action.chosen_action = self.interact_at(cook, self.scan_board(world, ObjectType.sauce))

        elif self.holding_topping(ToppingType.dough, False):
            action.chosen_action = self.interact_at(cook, self.scan_board(world, ObjectType.roller))

        elif self.get_dispenser(world, cook, ToppingType.dough)!=None:
            action.chosen_action = self.interact_at(cook, self.get_dispenser(world, cook, ToppingType.dough))

        else:
            action.chosen_action = self.move_action(cook.position, self.scan_board(world, ObjectType.delivery))

    def check_side(self, cook):
        """
        Check which side the cook is on and set bounds and is_left_side

        :param cook:        Pass your cook for its position
        """
        if self.is_left_side != None:
            return
        if cook.position[1] < 6:
            self.is_left_side = True
            self.x_min = 1
            self.x_max = 5
        else:
            self.is_left_side = False
            self.x_min = 7
            self.x_max = 11

    def move_action(self, cook_position: Tuple[int, int], target_location: Tuple[int, int]) -> ActionType.Move:
        """
        Determines which direction to move, and returns that ActionType

        :param cook_position:       The cook position in [y, x]
        :param target_location:     The target position in [y, x]
        :returns ActionType.Move:   Will return the correct action type to move towards the bounded target position
        """
        dist_tup = self.move_difference(cook_position, target_location)
        direction_to_move = self.decide_move(dist_tup)
        return direction_to_move

    def scan_board(self, world: GameBoard, station_type: ObjectType, eval_func=None) -> Tuple[int, int]:
        """
        Scans every tile on your clients half of the gameboard for a station that matches station_type and the eval_func

        :param world:               GameBoard to search
        :param station_type:        ObjectType to filter stations by
        :param eval_func:           Lambda function to filter by, will be ignored if None
        :returns Tuple[int, int]:   Will return the y,x position of what you were searching for
        """
        # For each tile on your side
        for y in range(self.y_min-1, self.y_max+2):
            for x in range(self.x_min-1, self.x_max+2):
                # Filter out things not of object type
                station = world.game_map[y][x].occupied_by
                if station != None and station.object_type == station_type:
                    item = station.item
                    # If not eval function, return the station
                    if eval_func == None:
                        return (y, x)
                    # Check eval function on item
                    elif eval_func(station):
                        return (y, x)
        # Didn't find anything that matched our criteria
        return None

    def manhattan_distance(self, int_tuple_one: Tuple[int, int], int_tuple_two: Tuple[int, int]) -> int:
        """
        See https://en.wikipedia.org/wiki/Taxicab_geometry

        :param int_tuple_one:   First y,x position
        :param int_tuple_two:   Second y,x position
        :returns int:           Returns Manhatten Distance of two y,x positions
        """
        return abs(int_tuple_one[0] - int_tuple_two[0]) + abs(int_tuple_one[1] - int_tuple_two[1])

    def move_difference(self, int_tuple_one: Tuple[int, int], int_tuple_two: Tuple[int, int]) -> Tuple[int, int]:
        """
        Returns the difference between a cook position and a bounded position
        The second position is bounded by your side of the game board

        :returns Tuple[int, int]:   Will return the y, x difference of two positions
        """

        # Check for left side bounds
        if self.is_left_side:
            x = max(min(int_tuple_two[1], self.x_max), self.x_min)
        # Check for right side bounds
        else:
            x = min(max(int_tuple_two[1], self.x_min), self.x_max)
        # Y bounds are the same for left and right side
        y = max(min(int_tuple_two[0], self.y_max), self.y_min)

        # Find the difference between them and return it
        y_diff = int_tuple_one[0] - y
        x_diff = int_tuple_one[1] - x
        return (y_diff, x_diff)

    def decide_move(self, tuple_diff: Tuple[int, int]) -> ActionType.Move:
        """
        Decides which direction to move in, based on a tuple difference

        :returns ActionType.Move:   Will return the correct action type to move towards the tuple difference
        """
        if tuple_diff[1] > 0:
            return ActionType.Move.left
        elif tuple_diff[1] < 0:
            return ActionType.Move.right
        elif tuple_diff[0] > 0:
            return ActionType.Move.up
        elif tuple_diff[0] < 0:
            return ActionType.Move.down
