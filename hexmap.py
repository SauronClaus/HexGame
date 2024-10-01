import math
import json
from kivy.uix.image import Image

from terrain import GrassTerrain
from terrain import ForestTerrain
from terrain import HillsTerrain
from terrain import MountainTerrain
from terrain import WaterTerrain
from terrain import TerrainType
from pathfinding import PathFinder
from structure import CityStructure, RoadStructure, FortressStructure, FarmStructure, PortStructure

from GameUnits import Phalanx, Archer, Cavalry, Garrison
from MapGenerator import MapGenerator
from Constants import HEX_SIZE
from Constants import ROOT_3
from Constants import GENERATE_RANDOM_MAP
import Globals
import ini
from FogControl import Fog_Controller
from ai_control import CPU

GRID_WIDTH = 20
GRID_HEIGHT = 20

# Hexagons are the basic unit of the hexmap grid.
class Hexagon:
    def __init__(self, in_x, in_y):
        self.terrain_type = GrassTerrain()
        self.structure = None
        self.index_x = in_x
        self.index_y = in_y
        self.terrain_image = None
        self.structure_image = None
        self.road_connections = []
        self.river_edges = [False, False, False, False, False, False]
        self.should_outline = False
        self.path_outline = False
        self.search_outline = False
        self.river_movement_cost = 2
        self.game_units = []
        self.fog_level = [2, 2]  # 2 is full fog; 1 is darkened; 0 is clear
        self.fog_image = None
        self.white_hex = "content/White_Hex.png"
        self.darken_texture = "content/Black_Hex.png"
        self.terrain_texture = ''
        self.adjacent_hexes = [None, None, None, None, None, None]
        self.visible_by_object = {
            0: [],
            1: []
        }
        self.destination_cost = 0
        self.prev_hex = None
        self.search_id = 0
        self.needs_update = False
        self.mark_visible = False

    # returns a list of the x indices and a list of the y indices of the 6 hexagon vertices
    def get_hex_vertices(self):
        triangle_height = 0.25 * ROOT_3 * HEX_SIZE
        pos_x, pos_y = self.get_hex_center()

        hex_vertex_x = [pos_x - 0.25 * HEX_SIZE, pos_x + 0.25 * HEX_SIZE, pos_x + 0.5 * HEX_SIZE,
                        pos_x + 0.25 * HEX_SIZE, pos_x - 0.25 * HEX_SIZE, pos_x - 0.5 * HEX_SIZE]
        hex_vertex_y = [pos_y + triangle_height, pos_y + triangle_height, pos_y, pos_y - triangle_height,
                        pos_y - triangle_height, pos_y]
        return hex_vertex_x, hex_vertex_y

    # add a MovableUnit of unit_type to the list of units in this hex.  Does not check max stacking limit
    def add_unit(self, unit_type, player_owner):
        # print(f"unit type is {unit_type}")
        new_unit = unit_type(player_owner, self)
        new_unit.sprite.pos = self.get_unit_position(new_unit)
        self.game_units.append(new_unit)
        # print(f"Visible by object: {self.visible_by_object}")
        if new_unit not in self.visible_by_object:
            self.visible_by_object[player_owner].append(new_unit)
        return new_unit

    # do not call directly, call hexmap.update_hex_structure()
    def add_structure(self, structure_type, player_owner, builder_unit, no_construction=False):
        self.structure = structure_type(player_owner, self)
        if no_construction:
            self.structure.remaining_build_time = 0
        # if during gameplay, builder unit passed in - it must spend full movement to build
        if builder_unit is not None:
            builder_unit.remaining_moves = 0
        self.update_structure_image()
        # print(f"Visible by object: {self.visible_by_object}")
        if self.structure not in self.visible_by_object:
            self.visible_by_object[player_owner].append(self.structure)
        return True

    # returns the position to draw this unit, so the stacked units have a small offset
    def get_unit_position(self, unit):
        hex_x, hex_y = self.get_hex_position()
        size_x, size_y = unit.sprite.size
        offset = len(self.game_units) * 3.0
        if unit in self.game_units:
            offset = self.game_units.index(unit) * 3.0
        return hex_x + 0.5*(HEX_SIZE - size_x) + offset, hex_y - size_y - 0.25 * (HEX_SIZE - size_y) + offset

    # whether unit is able to enter this hex because of blocking by enemy unit or structure
    def is_blocked_by_enemy_to(self, unit):
        # does an enemy structure on this hex block the unit
        if (self.structure is not None) and self.structure.blocks_enemy and (self.structure.player_owner != unit.player_owner):
            return True
        # does an enemy on this hex block the unit
        for hex_unit in self.game_units:
            if hex_unit.blocks_enemy and (hex_unit.player_owner != unit.player_owner):
                return True
        return False

    # whether unit is able to enter this hex (due to terrain or stacking limits)
    def is_impassable_to(self, unit):
        if unit.current_hex == self:
            return False
        # check if terrain is impassable to this unit
        if unit.hex_is_impassable(self):
            return True
        # is hex already at max stack height?
        if (len(self.game_units) >= Globals.MAX_UNIT_STACK) and (unit.player_owner == self.game_units[0].player_owner):
            return True
        return False

    # return the defensive strength of this hex based on the units in it, modified by terrain, structure, and fortified bonuses
    def calc_defense_strength(self):
        defense_strength = 0.0
        defense_bonus = 1.0
        if self.terrain_type is not None:
            defense_bonus += self.terrain_type.defense_bonus
        if (self.structure is not None) and (self.structure.remaining_build_time <= 0):
            defense_bonus += self.structure.defense_bonus
        for unit in self.game_units:
            base_unit_defense = 1.0
            if unit.is_fortified:
                base_unit_defense = 1.5
            defense_strength += base_unit_defense * defense_bonus
        return defense_strength

    # return the movement cost for unit to enter this hex from other_hexagon
    # considers terrain cost, whether hex is impassable, and also adds a cost for enemies (for pathing)
    def get_movement_cost_from(self, other_hexagon, unit):
        if not self.is_adjacent_to(other_hexagon) or self.is_impassable_to(unit):
            return 1000000
        cost = self.get_terrain_movement_cost_from(other_hexagon, unit)
        if self.is_blocked_by_enemy_to(unit):
            # add cost based on enemy strength
            cost = cost + 10.0 * self.calc_defense_strength()
            # print(f"move defense cost is {cost}")
        return cost

    # return the terrain only movement cost from other_hexagon to this hex
    def get_terrain_movement_cost_from(self, other_hexagon, unit):
        movement_cost = unit.get_terrain_movement_cost(self.terrain_type)

        # roads are fast
        if other_hexagon in self.road_connections:
            return 1

        # add cost if connecting edge is river edge
        edge_index = self.get_edge_index_to(other_hexagon)
        if (edge_index >= 0) and self.river_edges[edge_index]:
            movement_cost = movement_cost + 1
        return movement_cost

    # returns an index corresponding to the edge of this hexagon that separates it from other_hexagon
    # 0 is the edge at the top of the hexagon, and edge index increments clockwise
    def get_edge_index_to(self, other_hexagon):
        try:
            index = self.adjacent_hexes.index(other_hexagon)
            return index
        except ValueError:
            return -1

    # returns true if other_hexagon is adjacent to this hexagon in the hex grid
    def is_adjacent_to(self, other_hexagon):
        return self.get_edge_index_to(other_hexagon) >= 0

    # add a road connection between this hexagon and other_hexagon
    def add_road_to(self, other_hexagon):
        print("Adding road...")
        if other_hexagon not in self.road_connections:
            self.road_connections.append(other_hexagon)

    # add a river running along the edge specified by edge_index
    def add_river_edge(self, edge_index):
        # edge_index is in the range 0 to 5
        edge_index = edge_index
        if (edge_index < 0) or (edge_index > 5):
            return False
        self.river_edges[edge_index] = True
        return True

    # remove structure from this hexagon
    def remove_structure(self, hex_map):
        if self.structure is not None and self.structure.player_owner == Globals.LOCAL_PLAYER:
            view_level = self.structure.view_distance
            hex_map.fog_controller.remove_fog(self, view_level, self.structure)
        if (self.structure is not None) and self.structure in hex_map.structures:
            hex_map.structures.remove(self.structure)
        self.structure = None
        self.update_structure_image()
        self.needs_update = True

    # returns a position at the top left of the hex (x = the leftmost point of the hexagon, y = the topmost point of the hexagon)
    def get_hex_position(self):
        hex_x = self.index_x * HEX_SIZE
        hex_y = (self.index_y + 1.0) * HEX_SIZE * ROOT_3 * 0.5
        hex_x = hex_x - 0.25 * HEX_SIZE * (math.floor((1 + self.index_x) / 2) + math.floor(self.index_x / 2))

        if self.index_x % 2 == 1:
            hex_y -= HEX_SIZE * ROOT_3 * 0.25
        return hex_x, hex_y

    # returns position at the center of the hex
    def get_hex_center(self):
        hex_x, hex_y = self.get_hex_position()
        hex_x = hex_x + 0.5 * HEX_SIZE
        hex_y = hex_y - 0.25 * ROOT_3 * HEX_SIZE
        return hex_x, hex_y

    # update the terrain display image based on the terrain_type of the hex
    def update_terrain_image(self):
        if self.terrain_image is not None:
            if self.terrain_type is None:
                self.terrain_texture = ''
            else:
                self.terrain_texture = self.terrain_type.image_path
            self.terrain_image.source = self.terrain_texture
        else:
            if self.terrain_type is None:
                self.terrain_image = None
                return
        hex_x, hex_y = self.get_hex_position()
        art_position = hex_x, hex_y - HEX_SIZE
        if self.terrain_type is None:
            self.terrain_image = None
        else:
            # print(f"\tSetting terrain_image to {self.terrain_type} ({self.terrain_type.image_path})")
            self.terrain_texture = self.terrain_type.image_path
            self.terrain_image = Image(source=self.terrain_texture, pos=art_position, size=(HEX_SIZE, HEX_SIZE))

        if self.fog_image is None:
            self.fog_image = Image(source=self.darken_texture, pos=art_position, size=(HEX_SIZE, HEX_SIZE))
            self.fog_image.opacity = 0.0

    # update the structure display image based on the structure in this hexagon
    def update_structure_image(self):
        if self.structure is None:
            if self.structure_image is not None:
                # remove from rendering
                if self.structure_image.parent is not None:
                    self.structure_image.parent.remove_widget(self.structure_image)
                self.structure_image = None
            return
        hex_x, hex_y = self.get_hex_position()
        image_size = self.structure.image_scale * HEX_SIZE / 1.25
        hex_x = hex_x + 0.1 * HEX_SIZE + 0.5 * (1.0 - self.structure.image_scale) * HEX_SIZE / 1.25
        hex_y = hex_y - 0.85 * HEX_SIZE + 0.5 * (1.0 - self.structure.image_scale) * HEX_SIZE / 1.25
        self.structure_image = Image(source=self.structure.image_path, pos=(hex_x, hex_y), size_hint=(None, None), size=(image_size, image_size))


class HexMap:
    def __init__(self, filename):
        self.terrain_types = [GrassTerrain(), ForestTerrain(), HillsTerrain(), MountainTerrain(), WaterTerrain()]
        self.structure_types = [CityStructure, FortressStructure, FarmStructure, RoadStructure, PortStructure]
        self.unit_types = [Phalanx, Cavalry, Archer, Garrison]
        self.grid_width = GRID_WIDTH
        self.grid_height = GRID_HEIGHT
        self.path_finder = PathFinder(self)
        self.hex_grid = []
        self.structures = []
        self.dead_units = []
        self.moving_units = []
        self.last_modified_hex = None
        self.hex_map_widget = None
        self.current_search_id = 0
        self.filename = filename
        self.game_rules = None
        self.initialize_map("")
        self.fog_controller = Fog_Controller(self)
        self.cpu = None

    # update unit animations/position for all dead and current units
    def update_units(self, dt, selected_hex):
        # update dead units (death anim)
        for unit in self.dead_units:
            unit.update_death(dt, self)
            if unit.vanish_time < 0.0:
                self.dead_units.remove(unit)

        # update moving units
        for unit in self.moving_units:
            unit.update_position(dt, self, selected_hex)

    # serialize the hex map (json format)
    def save_hex_map(self):
        hexagon_troops = {}
        hexagon_road_connections = {}
        for column in self.hex_grid:
            for hexagon in column:
                hex_units = []
                hex_roads = []
                for unit in hexagon.game_units:
                    troop = f"{unit.__class__.__name__}|{unit.player_owner}|{unit.remaining_moves}"
                    hex_units.append(troop)
                for road_connection in hexagon.road_connections:
                    hex_roads.append((road_connection.index_x, road_connection.index_y))
                hexagon_troops[hexagon] = hex_units
                hexagon_road_connections[hexagon] = hex_roads
        map_data = {
            'width': self.grid_width,
            'height': self.grid_height,
            'hexes': [
                {
                    'x': x,
                    'y': y,
                    'terrain_type': hexagon.terrain_type.name,
                    'structure_type': f"{hexagon.structure.name}|{hexagon.structure.player_owner}" if not(hexagon.structure is None) else "None",
                    'units': hexagon_troops[hexagon],
                    'fog': hexagon.fog_level,
                    'road_connections': hexagon_road_connections[hexagon]
                } for y, row in enumerate(self.hex_grid) for x, hexagon in enumerate(row)
            ]
        }
        return map_data

    # if a filename is passed in, load the map, otherwise generate a new map
    def initialize_map(self, filename):
        if filename != "":
            self.load_hex_map(filename)
        else:
            self.generate_map(GRID_WIDTH, GRID_HEIGHT)

    # generate a new map, either blank or with terrain formations if GENERATE_RANDOM_MAP
    def generate_map(self, width, height):
        print("GENERATE MAP")
        if GENERATE_RANDOM_MAP:
            gen = MapGenerator()
            gen.generate_map(self, width, height)
        else:
            self.generate_hex_map(GRID_WIDTH, GRID_HEIGHT)
        self.init_for_map()

    # initialize hex_map for the newly created/loaded map
    def init_for_map(self):
        # hex_map_widget is none when map is loaded at initialization - GameScreen will call update_canvas() in that case
        if self.hex_map_widget is not None:
            self.hex_map_widget.update_canvas()
        self.path_finder = PathFinder(self)
        # GameScreen will give me one
        self.cpu = None

    # generate a grid of hexes of the desired extent
    def generate_hex_map(self, width, height):
        self.grid_width = width
        self.grid_height = height
        self.hex_grid = []
        index_x = 0
        index_y = 0
        for _ in range(self.grid_height):
            column = []
            for _ in range(self.grid_width):
                column.append(Hexagon(index_x, index_y))
                index_x = index_x + 1
            self.hex_grid.append(column)
            index_x = 0
            index_y = index_y + 1
        # self.hex_grid[column_num][row_num]

        for column in self.hex_grid:
            for hexagon in column:
                self.set_adjacent_hexes(hexagon)

    # load a map from a file specified by filename.  map is serialized with json format.
    def load_hex_map(self, filename):
        filename = "Maps\\" + filename + ".json"
        # load saved map data
        if filename != "":
            try:
                with open(filename, 'r') as file:
                    map_data = json.load(file)
                width = map_data["width"]
                height = map_data["height"]
                self.generate_hex_map(width, height)

                for hex_data in map_data['hexes']:
                    new_terrain_name = hex_data['terrain_type']
                    if new_terrain_name != "Grass":
                        # print(f"place {new_terrain_name} at {hex_data['x']} {hex_data['y']}")
                        for terrain_type in self.terrain_types:
                            if new_terrain_name == terrain_type.name:
                                row = self.hex_grid[hex_data['y']]
                                hexagon = row[hex_data['x']]
                                hexagon.terrain_type = terrain_type
                                break

                    structure_info = hex_data['structure_type']
                    if structure_info != "None":
                        structure_name, structure_owner = structure_info.split("|")
                        print(f"place {structure_name} at {hex_data['x']} {hex_data['y']}")
                        for structure in self.structure_types:
                            if (structure_name + 'Structure' == structure.__name__) or (structure_name == structure.__name__):
                                # print(f" Updating {structure.name}!")
                                row = self.hex_grid[hex_data['y']]
                                hexagon = row[hex_data['x']]
                                hexagon.add_structure(structure, int(structure_owner), None, no_construction=True)
                                self.structures.append(hexagon.structure)
                                break
                            else:
                                print(f" Not {structure.__name__}!")


                    road_connections = hex_data['road_connections']
                    for hex_coords in road_connections:
                        selected_hex_x = hex_coords[0]
                        selected_hex_y = hex_coords[1]
                        selected_hex = self.get_hexagon(selected_hex_x, selected_hex_y)
                        row = self.hex_grid[hex_data['y']]
                        hexagon = row[hex_data['x']]
                        self.update_road(selected_hex, hexagon)

                    game_units = hex_data['units']
                    if game_units != {}:
                        for unit_info in game_units:
                            unit_name, unit_owner, remaining_steps = unit_info.split("|")

                            # print(f"place {unit_info} x {game_units[unit_info]} at {hex_data['x']} {hex_data['y']}")
                            # print(f"\tunit types: {self.unit_types}")
                            for unit_type in self.unit_types:
                                if unit_name == unit_type.__name__:
                                    row = self.hex_grid[hex_data['y']]
                                    hexagon = row[hex_data['x']]
                                    new_unit = hexagon.add_unit(unit_type, int(unit_owner))
                                    new_unit.remaining_moves = remaining_steps

                    fog_level = hex_data['fog']
                    for index in range(len(fog_level)):
                        if fog_level[index] != 2:
                            # print(f"place {fog_level[index]} at {hex_data['x']} {hex_data['y']}")
                            row = self.hex_grid[hex_data['y']]
                            hexagon = row[hex_data['x']]
                            hexagon.fog_level[index] = fog_level[index]
            except FileNotFoundError:
                print(f"The file {filename} was not found. Generating a new map.")
            except json.JSONDecodeError:
                print("Error decoding JSON. Generating a new map.")

        self.init_for_map()

    # return the hexagon that encompasses the point at pos_x, pos_y
    def find_hex_at_position(self, pos_x, pos_y):
        # split hexagons in half, so we have repeating (offset by row) sets of line segments to analyze /- \_
        half_row_index = math.floor(pos_y / (HEX_SIZE * ROOT_3 * 0.25))
        # figure out which segment we are in
        column_index = math.floor(pos_x / (HEX_SIZE * 0.75))
        if column_index < 0 or column_index >= self.grid_width:
            return None
        # print(f"half row index {half_row_index} from {pos_y}  column index {column_index} from {pos_x}")
        # calculate x and y offsets from the start of that segment
        x_offset = (0.75 * HEX_SIZE) * (pos_x / (0.75 * HEX_SIZE) - math.floor(pos_x / (0.75 * HEX_SIZE)))
        y_offset = pos_y - half_row_index * HEX_SIZE * ROOT_3 * 0.25
        # print(f"x offset {x_offset} y offset {y_offset}")
        # triangle to possibly adjust which hexagon is in first part of segment
        if x_offset < 0.25 * HEX_SIZE:
            # print("in triangle")
            if (half_row_index % 2 == 1) == (column_index % 2 == 0):
                # maybe need to go up a row, depending on which column we are in
                if y_offset > x_offset * ROOT_3:
                    # print(f" add one because even column, point above {x_offset}")
                    half_row_index = half_row_index + 1
                    column_index = column_index - 1
            else:
                # odd column, subtract one if below
                if y_offset < (HEX_SIZE * 0.25 - x_offset) * ROOT_3:
                    # print(f" add one because odd column, point below {x_offset}")
                    column_index = column_index - 1
                else:
                    half_row_index = half_row_index + 1
        elif column_index % 2 == 1:
            half_row_index = half_row_index + 1
        row_index = math.floor(half_row_index / 2.0)
        if row_index < 0 or row_index >= self.grid_height:
            return None
        column_index = max(column_index, 0)
        # print(f"{self} {pos_x} {pos_y} becomes row {row_index} column {column_index} out of {len(self.hex_grid)}")
        row = self.hex_grid[row_index]
        hexagon = row[math.floor(column_index)]
        if (hexagon.index_x != column_index) or (hexagon.index_y != row_index):
            print(f"{self} click {pos_x} {pos_y} becomes {hexagon.index_x} {hexagon.index_y} mismatch with {column_index} {row_index}")
        return hexagon

    # change the terrain type of the hex encompassing pos_x, pos_y to the new terrain type corresponding to in_terrain_type
    def update_hex_terrain(self, in_terrain_name, pos_x, pos_y):
        for terrain_type in self.terrain_types:
            if terrain_type.name == in_terrain_name:
                hexagon = self.find_hex_at_position(pos_x, pos_y)
                if hexagon.terrain_type == terrain_type:
                    return False
                hexagon.terrain_type = terrain_type
                hexagon.update_terrain_image()
                return True
        return False

    # add unit or type unit_class to hexagon, and update rendering
    def add_unit(self, unit_class, hexagon, player_owner):
        new_unit = hexagon.add_unit(unit_class, player_owner)
        if (new_unit is not None) and (new_unit.sprite is not None) and hexagon.mark_visible and ((hexagon.fog_level[Globals.LOCAL_PLAYER] == 0) or ini.NO_FOG):
            self.hex_map_widget.add_unit_widget(new_unit.sprite)
        return new_unit

    # structure being built during gameplay
    def update_hex_structure(self, structure_class, hexagon, player_owner, builder_unit):
        old_structure = hexagon.structure
        if hexagon.add_structure(structure_class, player_owner, builder_unit):
            if old_structure is not None:
                self.structures.remove(old_structure)
            self.structures.append(hexagon.structure)
            if (hexagon.structure_image is not None) and hexagon.mark_visible:
                self.hex_map_widget.add_structure_widget(hexagon.structure_image, hexagon.structure)
                return True
        return False

    # get the hexagon at offset index_x, index_y in the hex grid
    def get_hexagon(self, index_x, index_y):
        if (index_y < 0) or (index_y >= self.grid_height) or (index_x < 0) or (index_x >= self.grid_width):
            return None
        row = self.hex_grid[index_y]
        return row[index_x]

    # set the adjacent hexes array for current_hex, sorted so index 0 in the the adjacent hex on top of current hex and continuing clockwise
    def set_adjacent_hexes(self, current_hex):
        index_x = current_hex.index_x
        index_y = current_hex.index_y
        if (index_x < 0) or (index_y < 0) or (index_x >= self.grid_width) or (index_x >= self.grid_height):
            print(f"bad index passed into set_adjacent_hexes() {index_x} {index_y}")

        if index_x % 2 == 0:
            # Even columns
            if index_y < self.grid_height - 1:
                current_hex.adjacent_hexes[0] = self.get_hexagon(index_x, index_y+1)  # x,y+1
                if index_x > 0:
                    current_hex.adjacent_hexes[5] = self.get_hexagon(index_x-1, index_y+1)  # x-1,y+1
                if index_x < self.grid_width - 1:
                    current_hex.adjacent_hexes[1] = self.get_hexagon(index_x+1, index_y+1)  # x+1,y+1
            if index_y > 0:
                if index_x < self.grid_width - 1:
                    current_hex.adjacent_hexes[2] = self.get_hexagon(index_x+1, index_y)  # x+1,y
                current_hex.adjacent_hexes[3] = self.get_hexagon(index_x, index_y-1)  # x,y-1
                if index_x > 0:
                    current_hex.adjacent_hexes[4] = self.get_hexagon(index_x-1, index_y)  # x-1,y
            elif index_x == 0:
                current_hex.adjacent_hexes[2] = self.get_hexagon(index_x + 1, index_y)  # x+1,y
        else:
            # Odd columns
            if index_x > 0:
                current_hex.adjacent_hexes[5] = self.get_hexagon(index_x - 1, index_y)  # x-1,y
            if index_x < self.grid_width - 1:
                current_hex.adjacent_hexes[1] = self.get_hexagon(index_x + 1, index_y)  # x+1,y
            if index_y < self.grid_height - 1:
                current_hex.adjacent_hexes[0] = self.get_hexagon(index_x, index_y + 1)  # x,y+1
            if index_y > 0:
                if index_x < self.grid_width - 1:
                    current_hex.adjacent_hexes[2] = self.get_hexagon(index_x + 1, index_y-1)  # x+1,y-1
                current_hex.adjacent_hexes[3] = self.get_hexagon(index_x, index_y - 1)  # x,y-1
                if index_x > 0:
                    current_hex.adjacent_hexes[4] = self.get_hexagon(index_x - 1, index_y-1)  # x-1,y-1

    # add a road between pending_road _hex and hexagon, if adjacent
    def update_road(self, start_hex, hexagon):
        if (start_hex is not None) and hexagon.is_adjacent_to(start_hex) and hexagon not in start_hex.road_connections:
            start_hex.add_road_to(hexagon)
            hexagon.add_road_to(start_hex)
            self.hex_map_widget.draw_road(hexagon, start_hex)
            self.last_modified_hex = hexagon
            return True
        self.last_modified_hex = hexagon
        return False

    # add a river to the hexagon encompassing pos_x, pos_y, at the edge specified by edge
    def update_river(self, pos_x, pos_y, edge):
        hexagon = self.find_hex_at_position(pos_x, pos_y)
        hexagon.add_river_edge(edge)
        self.last_modified_hex = hexagon
        hex_vertex_x, hex_vertex_y = hexagon.get_hex_vertices()
        self.hex_map_widget.draw_river_edge(hexagon, edge, hex_vertex_x, hex_vertex_y)
        return True

    # clear terrain and other modifications from hexagon encompassing pos_x, pos_y
    def clear_hex(self, pos_x, pos_y):
        self.last_modified_hex = None
        hexagon = self.find_hex_at_position(pos_x, pos_y)

        # remove roads
        for other_hexagon in hexagon.road_connections:
            other_hexagon.road_connections.remove(hexagon)
        hexagon.road_connections.clear()

        # remove rivers
        for index in range(len(hexagon.river_edges)):
            hexagon.river_edges[index] = False

        hexagon.terrain_type = GrassTerrain()
        hexagon.update_terrain_image()
        if hexagon.mark_visible:
            self.hex_map_widget.remove_hex_widgets(hexagon)
        hexagon.remove_structure(self)
        for unit in hexagon.game_units:
            hexagon.game_units.remove(unit)
        return True
