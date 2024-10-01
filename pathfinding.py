import bisect


def index(a, x, key=lambda x: x):
    # 'Locate the leftmost value exactly equal to x'
    i = bisect.bisect_left(a, x, key=key)
    if i != len(a) and a[i] == x:
        return i
    raise ValueError


def insertion_index(sorted_list, new_object, key=lambda x: x.value):
    # Find the position where the new object should be inserted.
    low, high = 0, len(sorted_list)
    while low < high:
        mid = (low + high) // 2
        if key(sorted_list[mid]) < key(new_object):
            low = mid + 1
        else:
            high = mid
    return low


class PathFinder:
    def __init__(self, in_hex_map):
        self.hex_map = in_hex_map
        self.sorted_hex_list = []

    # PUBLIC INTERFACE
    # find_nearest_objective does search through the hex_map for the nearest by movement cost hex that satisfies evaluation_func
    # the function you pass in should return True if the hex passed to it satisfies your search criteria
    # returns the winning hex and the cost held in its destination_cost property to move to it if successful, None if not
    # todo also return the path to this hex!
    def find_nearest_objective(self, start_hex, unit, evaluation_func):
        # holds a list of hexes to evaluate, sorted by cost to move to them
        self.sorted_hex_list.clear()
        self.hex_map.current_search_id += 1
        self.add_sorted_hexes_from(start_hex, unit)
        # don't search through start hex
        start_hex.destination_cost = 0
        start_hex.search_id = self.hex_map.current_search_id
        best_route = []

        # print(f"{self.sorted_hex_list}")
        while self.sorted_hex_list:
            # print(f"\t{self.sorted_hex_list}")
            eval_hex = self.sorted_hex_list.pop(0)
            # print(eval_hex)
            # first check if this hex satisfies search criteria
            if evaluation_func(eval_hex):
                best_route = self.reverse_discover_route(start_hex, eval_hex)
                return eval_hex, best_route
            # print(f"{eval_hex}: {eval_hex.adjacent_hexes}")
            self.add_sorted_hexes_from(eval_hex, unit)
        return None, best_route

    # helper for find_nearest_objective()
    def add_sorted_hexes_from(self, start_hex, unit):
        current_id = self.hex_map.current_search_id
        for new_hex in start_hex.adjacent_hexes:
            if (new_hex is not None) and not new_hex.is_impassable_to(unit):
                cost = new_hex.get_terrain_movement_cost_from(start_hex, unit)
                # if total cost is improved, move or add to sorted hexes
                total_cost = start_hex.destination_cost + cost
                if (new_hex.search_id != current_id) or (new_hex.destination_cost > total_cost):
                    new_hex.search_id = current_id
                    new_hex.destination_cost = total_cost
                    new_hex.prev_hex = start_hex
                    # insert or move in sorted list
                    if new_hex in self.sorted_hex_list:
                        self.sorted_hex_list.remove(new_hex)
                    # Insert the new object into the list at the correct position
                    pos = insertion_index(self.sorted_hex_list, new_hex, key=lambda x: x.destination_cost)
                    self.sorted_hex_list.insert(pos, new_hex)

    # PUBLIC INTERFACE
    # find_path_to finds path for unit from current_hex to destination_hex
    # it sets the unit's destination_hex to the next hex on the route, and also sets the unit's route[]
    # @TODO check currently cached best route - if still valid, start with that
    def find_path_to(self, unit, current_hex, destination_hex):
        self.hex_map.current_search_id += 1
        straight_route = []
        self.direct_route_toward(unit, current_hex, destination_hex, straight_route, 0)
        # remove end of route that is impassable
        best_route = []
        prev_hex = current_hex
        for next_hex in straight_route:
            if next_hex.is_impassable_to(unit):
                # print(f"impassable to{unit} has {next_hex.game_units} structure {next_hex.structure}")
                destination_hex.destination_cost = 10000000
                break
            else:
                next_hex.prev_hex = prev_hex
                prev_hex = next_hex
                best_route.append(next_hex)

        # print(f"DIRECT ROUTE {len(straight_route)} best route {len(best_route)} cost is {destination_hex.destination_cost}")

        # assume movement cost between hexes can't be less than 1
        best_cost = destination_hex.destination_cost
        if best_cost > len(straight_route):
            search_route, search_cost = self.search_route_toward(unit, current_hex, destination_hex, best_route)
            if search_cost < best_cost:
                best_route = search_route
        # print("FINAL ROUTE")
        # for hex in best_route:
        #    print(f"{hex.index_x} {hex.index_y}")
        return best_route

    def search_route_toward(self, unit, current_hex, destination_hex, current_best_route):
        # initial search area is the linear route from current_hex to destination_hex
        num_checked = len(current_best_route)
        best_route = []
        check_hexes = []
        # include current hex as part of search area
        search_id = self.hex_map.current_search_id
        current_hex.destination_cost = 0
        current_hex.search_id = search_id
        check_hexes.append(current_hex)
        found_route = False
        found_cost = 100000
        for next_hex in current_best_route:
            best_route.append(next_hex)
            check_hexes.append(next_hex)
        # determine cost to hexes adjacent to current search area
        for check_hex in check_hexes:
            for next_hex in check_hex.adjacent_hexes:
                if (next_hex is not None) and not next_hex.is_impassable_to(unit):
                    new_cost = check_hex.destination_cost + next_hex.get_movement_cost_from(check_hex, unit)
                    if (next_hex.search_id != search_id) or (new_cost < next_hex.destination_cost):
                        # update next_hex route values
                        num_checked += 1
                        next_hex.search_id = search_id
                        next_hex.prev_hex = check_hex
                        next_hex.destination_cost = new_cost
                        if new_cost <= destination_hex.destination_cost:
                            # next_hex.search_outline = True
                            # a potential path, since lower cost than current best route, so add to search area for future searches
                            check_hexes.append(next_hex)
                            next_hex.search_outline = False
                            if next_hex == destination_hex:
                                found_route = True
                                found_cost = new_cost
                            if (found_cost < num_checked):
                                # found a good enough route
                                break
        if found_route:
            best_route = self.reverse_discover_route(current_hex, destination_hex)
        return best_route, destination_hex.destination_cost

    def reverse_discover_route(self, current_hex, destination_hex):
        # starting from destination_hex, use prev_hex to discover the path from current_hex
        best_route = []
        prev_hex = destination_hex
        while prev_hex != current_hex:
            best_route.insert(0, prev_hex)
            prev_hex = prev_hex.prev_hex
        return best_route

    # fills straight_route a straight line path from current_hex to destination_hex. This sets the minimum bar for pathfinding,
    # and provides a seed route for the search for faster paths
    def direct_route_toward(self, unit, current_hex, destination_hex, straight_route, current_cost):
        current_hex.search_id = self.hex_map.current_search_id
        current_hex.destination_cost = current_cost

        if destination_hex.is_adjacent_to(current_hex):
            straight_route.append(destination_hex)
            destination_hex.destination_cost = current_cost + destination_hex.get_movement_cost_from(current_hex, unit)
            return

        if destination_hex.index_x == current_hex.index_x:
            if destination_hex.index_y > current_hex.index_y:
                next_hex = current_hex.adjacent_hexes[0]
            else:
                next_hex = current_hex.adjacent_hexes[3]
        elif destination_hex.index_x > current_hex.index_x:
            if (destination_hex.index_y > current_hex.index_y) and (current_hex.adjacent_hexes[1] is not None):
                next_hex = current_hex.adjacent_hexes[1]
            else:
                next_hex = current_hex.adjacent_hexes[2]
        else:
            if (destination_hex.index_y > current_hex.index_y) and (current_hex.adjacent_hexes[5] is not None):
                next_hex = current_hex.adjacent_hexes[5]
            else:
                next_hex = current_hex.adjacent_hexes[4]
        # failsafe checks at map edges
        if next_hex is None:
            if destination_hex.index_y > current_hex.index_y:
                next_hex = current_hex.adjacent_hexes[0]
            else:
                next_hex = current_hex.adjacent_hexes[3]
            if next_hex is None:
                next_hex = current_hex.adjacent_hexes[0]
            if next_hex is None:
                next_hex = current_hex.adjacent_hexes[3]

        current_cost = current_cost + next_hex.get_movement_cost_from(current_hex, unit)
        straight_route.append(next_hex)
        self.direct_route_toward(unit, next_hex, destination_hex, straight_route, current_cost)
