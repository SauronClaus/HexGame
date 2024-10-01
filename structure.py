from GameUnits import Phalanx, Archer, Cavalry, Garrison, Trireme
import pygame

class StructureType:
    def __init__(self, player_owner, in_hex):
        self.player_owner = player_owner
        self.hex_position = in_hex
        self.name = "Default Structure"
        self.image_path = "[Error]"
        self.team_image = ["[Error]", "[Error]"]
        self.image_scale = 1.0
        self.view_distance = 1
        self.blocks_enemy = False
        self.gold_per_turn = 0
        self.defense_bonus = 0.0
        self.cost = 0
        self.has_garrison = False
        self.remaining_build_time = 1
        self.build_time = 1
        self.container_structure = False
        self.in_build_menu = True
        self.recruitable_units = []
        self.construction_complete_sound = ""

    def construction_completed(self, hex_map):
        # play completed sound
        if self.construction_complete_sound != "":
            sound = pygame.mixer.Sound(self.construction_complete_sound)
            sound.play()
        # add garrison
        garrison = None
        if self.has_garrison:
            garrison = self.hex_position.add_unit(Garrison, self.player_owner)
        return garrison


class CityStructure(StructureType):
    def __init__(self, player_owner, in_hex):
        super().__init__(player_owner, in_hex)
        self.name = "City"
        self.team_image = ["content/Greek_City_2_shadow.png", "content/Greek_City_2_Green_shadow.png"]
        self.image_path = self.team_image[player_owner]
        self.view_distance = 2
        self.gold_per_turn = 10
        self.defense_bonus = 1.0
        self.cost = 100
        self.remaining_build_time = 2
        self.build_time = 4
        self.has_garrison = True
        self.container_structure = True
        self.recruitable_units = [Phalanx, Cavalry, Archer, Garrison]
        self.construction_complete_sound = "content/sounds/City_Complete.wav"

    def construction_completed(self, hex_map):
        # if city check for adjacent water hex to add port
        port_hex = None
        port_water = 0
        for adj_hex in self.hex_position.adjacent_hexes:
            if (adj_hex is not None) and adj_hex.terrain_type.is_water:
                water_count = 0
                for check_hex in adj_hex.adjacent_hexes:
                    if (check_hex is not None) and check_hex.terrain_type.is_water:
                        water_count += 1
                if (port_hex is None) or (water_count > port_water):
                    port_hex = adj_hex
                    port_water = water_count
        if port_hex is not None:
            hex_map.update_hex_structure(PortStructure, port_hex, self.player_owner, None)

        return super().construction_completed(hex_map)


class FortressStructure(StructureType):
    def __init__(self, player_owner, in_hex):
        super().__init__(player_owner, in_hex)
        self.name = "Fortress"
        self.team_image = ["content/Greek_Fortress_2.png", "content/Greek_Fortress_2_Green.png"]
        self.image_path = self.team_image[player_owner]
        self.image_scale = 0.75
        self.gold_per_turn = -2
        self.defense_bonus = 1.0
        self.cost = 50
        self.remaining_build_time = 2
        self.build_time = 3
        self.has_garrison = True
        self.container_structure = True
        self.construction_complete_sound = "content/sounds/Fortress_Complete.wav"


class FarmStructure(StructureType):
    def __init__(self, player_owner, in_hex):
        super().__init__(player_owner, in_hex)
        self.name = "Farm"
        self.team_image = ["content/Farm_Deco_18.png", "content/Farm_Deco_18.png"]
        self.image_path = self.team_image[player_owner]
        self.image_scale = 0.75
        self.gold_per_turn = 1
        self.cost = 10
        self.remaining_build_time = 9
        self.build_time = 1
        self.blocks_enemy = False
        self.construction_complete_sound = "content/sounds/Farm_Complete.wav"

class RoadStructure(StructureType):
    def __init__(self, player_owner, in_hex):
        super().__init__(player_owner, in_hex)
        self.name = "Road"
        self.image_path = "content/road.png"
        self.image_scale = 0.75
        self.gold_per_turn = 0
        self.cost = 10
        self.remaining_build_time = 1
        self.build_time = 1


# Port is not placed directly, auto-placed in water next to coastal city
class PortStructure(StructureType):
    def __init__(self, player_owner, in_hex):
        super().__init__(player_owner, in_hex)
        self.name = "Port"
        self.image_path = "content/Anchor.png"
        self.view_distance = 1
        self.gold_per_turn = 1
        self.defense_bonus = 1.0
        self.cost = 100
        self.remaining_build_time = 0
        self.build_time = 0
        self.has_garrison = False
        self.container_structure = False
        self.in_build_menu = False
        self.recruitable_units = [Trireme]