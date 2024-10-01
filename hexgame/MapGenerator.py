import random

from terrain import GrassTerrain
from terrain import ForestTerrain
from terrain import HillsTerrain
from terrain import MountainTerrain
from terrain import WaterTerrain

class MapGenerator():
    def __init__(self):
        hex_map = None

    def generate_map(self, in_hex_map, width, height):
        hex_map = in_hex_map
        hex_map.generate_hex_map(width, height)

        # seed water bodies
        print("generate random map")
        grid_size = hex_map.grid_height * hex_map.grid_width
        num_water_seeds = grid_size / 1500
        while num_water_seeds > 0:
            num_water_seeds -= 1
            hex = hex_map.get_hexagon(random.randint(0, hex_map.grid_width-1), random.randint(0, hex_map.grid_height-1))
            self.generate_water_at(hex, 1.0)

        num_mountain_seeds = grid_size / 150
        while num_mountain_seeds > 0:
            num_mountain_seeds -= 1
            hex = hex_map.get_hexagon(random.randint(0, hex_map.grid_width-1), random.randint(0, hex_map.grid_height-1))
            self.generate_mountain_at(hex, 1.0, random.randint(0, 5))

        num_hill_seeds = grid_size / 100
        while num_hill_seeds > 0:
            num_hill_seeds -= 1
            hex = hex_map.get_hexagon(random.randint(0, hex_map.grid_width-1), random.randint(0, hex_map.grid_height-1))
            self.generate_hill_at(hex, 1.0, random.randint(0, 5))

        num_forest_seeds = grid_size / 60
        while num_forest_seeds > 0:
            num_forest_seeds -= 1
            hex = hex_map.get_hexagon(random.randint(0, hex_map.grid_width-1), random.randint(0, hex_map.grid_height-1))
            self.generate_forest_at(hex, 1.0, random.randint(0, 5))

        # no single hex islands
        for column in hex_map.hex_grid:
            for hexagon in column:
                if not hexagon.terrain_type.is_water:
                    # print(f"check for island at {hexagon.index_x} {hexagon.index_y}")
                    all_water = True
                    for adj_hex in hexagon.adjacent_hexes:
                        if (adj_hex is not None) and not adj_hex.terrain_type.is_water:
                            print(f"not all water {adj_hex.terrain_type}")
                            all_water = False
                            break
                    if all_water:
                        # print(f"found tiny island at {hexagon.index_x} {hexagon.index_y}")
                        # add another hex to island
                        filtered_list = [item for item in hexagon.adjacent_hexes if item is not None]
                        random_hex = random.choice(filtered_list)
                        random_hex.terrain_type = GrassTerrain()

    def generate_water_at(self, hex, probability):
        if (random.random() < probability) and (hex is not None) and (hex.terrain_type.name == "Grasslands"):
            hex.terrain_type = WaterTerrain()
            for adjacent_hex in hex.adjacent_hexes:
                self.generate_water_at(adjacent_hex, probability * 0.97)

    def generate_mountain_at(self, hex, probability, direction):
        if (hex is not None) and (hex.terrain_type.name == "Grasslands"):
            if random.random() < probability:
                hex.terrain_type = MountainTerrain()
                self.generate_mountain_at(hex.adjacent_hexes[direction], 0.7, direction)
                self.generate_mountain_at(hex.adjacent_hexes[(direction - 1) % 6], 0.15, direction)
                self.generate_mountain_at(hex.adjacent_hexes[(direction + 1) % 6], 0.15, direction)
            elif random.random() < 0.5:
                hex.terrain_type = HillsTerrain()

    def generate_hill_at(self, hex, probability, direction):
        if (hex is not None) and (hex.terrain_type.name == "Grasslands"):
            if random.random() < probability:
                hex.terrain_type = HillsTerrain()
                self.generate_hill_at(hex.adjacent_hexes[direction], 0.6, direction)
                self.generate_hill_at(hex.adjacent_hexes[(direction - 1) % 6], 0.25, direction)
                self.generate_hill_at(hex.adjacent_hexes[(direction + 1) % 6], 0.25, direction)

    def generate_forest_at(self, hex, probability, direction):
        if (hex is not None) and (hex.terrain_type.name == "Grasslands"):
            if random.random() < probability:
                hex.terrain_type = ForestTerrain()
                self.generate_forest_at(hex.adjacent_hexes[direction], 0.6, direction)
                self.generate_forest_at(hex.adjacent_hexes[(direction - 1) % 6], 0.2, direction)
                self.generate_forest_at(hex.adjacent_hexes[(direction + 1) % 6], 0.2, direction)
