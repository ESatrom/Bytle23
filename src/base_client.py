from game.client.user_client import UserClient
from game.common.cook import Cook
from game.common.game_board import GameBoard
from game.common.action import Action
from typing import Tuple
from typing import List
from game.common.enums import *

# Main client class
class Client(UserClient):
    def __init__(self):
        """
        Variables and info you want to save between turns go here
        """
        super().__init__()
        # What side and x and y bounds are we using (set in start)
        self.is_left_side = None
        self.x_min = None
        self.y_min = 1
        self.x_max = None
        self.y_max = 5

    def team_data(self):
        """
        Return your team name for the engine

        :returns:       Your team name
        """
        return ('Papa Rivard\'s Pizza Professional™', 'john')

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
        return cook.held_item!=None and cook.held_item.object_type==ObjectType.pizza and cook.held_item.state==PizzaState.baked
    def holding_air(self, cook):
        return cook.held_item==None or (cook.held_item.topping_type==ToppingType.none if cook.held_item.object_type==ObjectType.topping else cook.held_item.state==PizzaState.none)
    def holding_topped_pizza(self, cook):
        return cook.held_item!=None and cook.held_item.object_type==ObjectType.pizza and len(cook.held_item.toppings)>0
    def holding_topping(self, cook, type, cut):
        return cook.held_item!=None and cook.held_item.object_type==ObjectType.topping and (cook.held_item.topping_type==type or (type==None and cook.held_item.topping_type!=ToppingType.dough)) and cook.held_item.is_cut==cut
    def holding_sauced_pizza(self, cook):
        return cook.held_item!=None and cook.held_item.object_type==ObjectType.pizza and cook.held_item.state==PizzaState.sauced and len(cook.held_item.toppings)==0
    def holding_rolled_pizza(self, cook):
        return cook.held_item!=None and cook.held_item.object_type==ObjectType.pizza and cook.held_item.state==PizzaState.rolled
    def most_expensive_dispenser(self, world: GameBoard):
        things=self.scan_all(world, ObjectType.dispenser)
        return sorted(things, key=lambda dispenser: (1 if world.game_map[dispenser[0]][dispenser[1]].occupied_by.item.worth == 60 else (0 if world.game_map[dispenser[0]][dispenser[1]].occupied_by.item.worth==50 else world.game_map[dispenser[0]][dispenser[1]].occupied_by.item.worth)) if world.game_map[dispenser[0]][dispenser[1]].occupied_by.item!=None else 0)[-1]
    def get_donest_pizza(self, world, cook) -> Tuple[int, int]:
        ovens = self.scan_all(world, ObjectType.oven, lambda oven: oven.is_active)
        ovens = list(zip(list(map(lambda oven: world.game_map[oven[0]][oven[1]].occupied_by.timer-self.manhattan_distance(cook.position, oven), ovens)), ovens))
        ovens = sorted(list(filter(lambda oven: oven[0]>0 and oven[0]<=20, ovens)), key=lambda oven: oven[0])
        if len(ovens)==0:return None
        return ovens[0][1]
    def scan_all(self, world: GameBoard, station_type: ObjectType, eval_func=None) -> List[Tuple[int, int]]:
        """
        Scans every tile on your clients half of the gameboard for a station that matches station_type and the eval_func

        :param world:               GameBoard to search
        :param station_type:        ObjectType to filter stations by
        :param eval_func:           Lambda function to filter by, will be ignored if None
        :returns Tuple[int, int]:   Will return the y,x position of what you were searching for
        """
        hits=[]
        # For each tile on your side
        for y in range(self.y_min-1, self.y_max+2):
            for x in range(self.x_min-1, self.x_max+2):
                # Filter out things not of object type
                station = world.game_map[y][x].occupied_by
                if station != None and station.object_type == station_type:
                    item = station.item
                    # If not eval function, return the station
                    if eval_func == None:
                        hits+=[(y, x)]
                    # Check eval function on item
                    elif eval_func(station):
                        hits+=[(y, x)]
        # Didn't find anything that matched our criteria
        return hits
    def closest_available_oven(self, world, cook):
        ovens = self.scan_all(world, ObjectType.oven, lambda oven: (not oven.is_active) and oven.is_powered)
        if len(ovens)==0:
            return None
        return sorted(ovens, key=lambda oven:self.manhattan_distance(cook.position, oven))[0]
    def get_combined_pizza(self, world):
        return self.scan_board(world, ObjectType.combiner, lambda combiner: combiner.item!=None and len(combiner.item.toppings)>0)
    def get_combining_pizza(self, world):
        return self.scan_board(world, ObjectType.combiner, lambda combiner: combiner.item!=None and len(combiner.item.toppings)<3)
    def is_combiner_available(self, world):
        return self.scan_board(world, ObjectType.combiner, lambda combiner: combiner.item==None or combiner.item.state==PizzaState.none)
    def get_dispenser(self, world, cook, ingredient):
        hits =  self.scan_all(world, ObjectType.dispenser, lambda dispenser: dispenser.item!=None and dispenser.item.topping_type==ingredient)
        if len(hits)==0:return None
        return sorted(hits, key=lambda dispenser: self.manhattan_distance(cook.position, dispenser))[0]
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
        elif self.get_donest_pizza(world, cook)!=None and self.holding_air(cook):
            action.chosen_action = self.interact_at(cook, self.get_donest_pizza(world, cook))
        elif self.holding_topped_pizza(cook):
            action.chosen_action = self.interact_at(cook, self.closest_available_oven(world, cook))
        elif self.get_combined_pizza(world)!=None and not self.holding_air(cook):
            com_pos=self.scan_board(world, ObjectType.combiner)
            if len(world.game_map[com_pos[0]][com_pos[1]].occupied_by.item.toppings)==1 and turn<450:
                action.chosen_action = self.interact_at(cook, self.most_expensive_dispenser(world))
            else:
                action.chosen_action = self.interact_at(cook, self.scan_board(world, ObjectType.combiner))
        elif self.holding_topping(cook, None, True):
            action.chosen_action = self.interact_at(cook, self.scan_board(world, ObjectType.combiner))
        elif self.holding_topping(cook, None, False):
            action.chosen_action = self.interact_at(cook, self.scan_board(world, ObjectType.cutter))
        elif self.get_combining_pizza(world)!=None and self.get_dispenser(world, cook, ToppingType.cheese):
            action.chosen_action = self.interact_at(cook, self.get_dispenser(world, cook, ToppingType.cheese))
        elif self.holding_sauced_pizza(cook):
            action.chosen_action = self.interact_at(cook, self.scan_board(world, ObjectType.combiner))
        elif self.holding_rolled_pizza(cook):
            action.chosen_action = self.interact_at(cook, self.scan_board(world, ObjectType.sauce))
        elif self.holding_topping(cook, ToppingType.dough, False):
            action.chosen_action = self.interact_at(cook, self.scan_board(world, ObjectType.roller))
        elif self.get_dispenser(world, cook, ToppingType.dough)!=None and self.is_combiner_available(world):
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

    # class node:
    #     def __init__(self, dataval=None):
    #         self.dataval = dataval
    #         self.nextval[] = [None]
    
    # def pathFind(self, cook_position: Tuple[int, int], target_location: Tuple[int, int]) -> List[Direction]:
    #     # // build graph
    #     # // make directional connections
    #     # // traverse graph
    #     [[],[]]

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
