import pygame

from MovableUnit import MovableUnit
from hexmap import Hexagon
from structure import RoadStructure
import Globals


class GameRules():
    def __init__(self, in_game_screen):
        self.game_screen = in_game_screen
        self.cities_captured = [0, 0]
        self.player_gold = [0, 0]

    def init_turn(self):
        print("Initing turn")
        gold_gained = 0
        for column in self.game_screen.hex_map.hex_grid:
            for hexagon in column:
                if hexagon.structure is not None:
                    if hexagon.structure.player_owner == Globals.CURRENT_TURN:
                        if hexagon.structure.remaining_build_time > 0:
                            hexagon.structure.remaining_build_time -= 1
                            opacity = float(hexagon.structure.build_time - hexagon.structure.remaining_build_time) / (hexagon.structure.build_time + 1.0)
                            hexagon.structure_image.color = [1, 1, 1, opacity]
                            if hexagon.structure.remaining_build_time == 0:
                                garrison = hexagon.structure.construction_completed(self.game_screen.hex_map)
                                if hexagon == self.game_screen.currently_selected_hex:
                                    self.game_screen.current_hex_construction_completed(garrison)
                        else:
                            hexagon.structure_image.color = [1, 1, 1, 1]
                            gold_gained += hexagon.structure.gold_per_turn
                            print(f"Player {Globals.CURRENT_TURN} gained {hexagon.structure.gold_per_turn} from {hexagon.structure}.")
        print(f"Setting gold for {Globals.CURRENT_TURN}; {self.player_gold}")
        self.player_gold[Globals.CURRENT_TURN] += gold_gained
        print(f"{gold_gained} gold gained for {Globals.CURRENT_TURN}! to {self.player_gold[Globals.CURRENT_TURN]}")
        print(f"Set gold for {Globals.CURRENT_TURN}; {self.player_gold}")

        # find all game units and initialize them for new turn
        for column in self.game_screen.hex_map.hex_grid:
            for hexagon in column:
                for game_unit in hexagon.game_units:
                    if game_unit.player_owner == Globals.CURRENT_TURN:
                        game_unit.remaining_moves = game_unit.movement_speed

    # returns true if road_builder can build road on this hex
    def can_build_road(self, road_builder):
        return (road_builder is not None) and road_builder.is_ready() and (self.player_gold[Globals.CURRENT_TURN] >= 10)

    def construct_road(self, road_builder, start_hex, new_hex):
        print("Creating road!")
        if self.game_screen.hex_map.update_road(start_hex, new_hex):
            self.player_gold[Globals.CURRENT_TURN] -= RoadStructure(0, None).cost
            road_builder.remaining_moves = 0
            return True
        return False

    def launch_ai_attack(self, from_hex, new_hex):
        self.game_screen.pending_attack = True
        for unit in from_hex.game_units:
            unit.group_moves = 0
            unit.remaining_moves = 0
        # bring up battle overlay, which gives choice whether to launch or cancel attack
        self.game_screen.add_widget(self.game_screen.battle_overlay)
        self.game_screen.battle_overlay.create_battle_layout(from_hex, new_hex)
        self.game_screen.battle_overlay.on_attack_button_press(None)

    def is_pending_attack(self, source_hex, destination_hex):
        # can only initiate attacks to adjacent hexes
        if not destination_hex.is_adjacent_to(source_hex):
            return False
        # check whether needs to be attack
        for unit in source_hex.game_units:
            if destination_hex.is_blocked_by_enemy_to(unit) and unit.player_owner == Globals.CURRENT_TURN:
                return True

    def initiate_attack(self, source_hex, destination_hex, in_hex_map):
        if self.is_pending_attack(source_hex, destination_hex):
            sound = pygame.mixer.Sound("content/sounds/battle.wav")
            sound.play()
            self.launch_attack_to(source_hex, destination_hex, in_hex_map)
            return True
        return False

    def launch_attack_to(self, source_hex, target_hex, hex_map):
        print("ATTACK!")
        # @TODO military units have attack and defense values, with enemy type, structure, and terrain modifications
        # TEMP attack always wins
        for hex_unit in target_hex.game_units:
            hex_unit.killed(hex_map)
        target_hex.game_units.clear()

    def entered_hex(self, hexagon, unit):
        if unit.cpu_controller is not None:
            unit.cpu_controller.entered_hex(hexagon, unit)
        if (hexagon.structure is not None) and hexagon.structure.container_structure:
            if unit.player_owner != hexagon.structure.player_owner:
                hexagon.structure.player_owner = unit.player_owner
                hexagon.structure.image_path = hexagon.structure.team_image[unit.player_owner]
                hexagon.structure_image.source = hexagon.structure.image_path
                # structure captured!
                print(f"Player {unit.player_owner} captured {hexagon.structure.name}")
                if hexagon.structure.name == 'City':
                    self.cities_captured[unit.player_owner] += 1
                    if self.cities_captured[unit.player_owner] == 2:
                        print("WINS THE MATCH")
                        self.game_screen.display_victory(unit.player_owner)
                    elif unit.player_owner == 0:
                        sound = pygame.mixer.Sound("content/sounds/City_Captured.wav")
                        sound.play()
                    else:
                        sound = pygame.mixer.Sound("content/sounds/City_Lost.wav")
                        sound.play()
                elif hexagon.structure.name == 'Fortress':
                    if unit.player_owner == 0:
                        sound = pygame.mixer.Sound("content/sounds/Fort_Captured.wav")
                        sound.play()
                    else:
                        sound = pygame.mixer.Sound("content/sounds/Fort_lost.wav")
                        sound.play()

