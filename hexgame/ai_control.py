from kivy.clock import Clock
from kivy.uix.label import Label

import pygame
import Globals
import random

import hexmap
from pathfinding import PathFinder


class CPU:
    def __init__(self, in_game_screen, hex_map):
        self.hex_map = hex_map
        self.game_screen = in_game_screen
        self.troops = []
        self.remaining_move_troops = []
        self.move_time = 0.0
        for column in hex_map.hex_grid:
            for hexagon in column:
                for game_unit in hexagon.game_units:
                    # print(f"{game_unit.player_owner} owns {game_unit}")
                    if game_unit.player_owner == 1:
                        # print("Added to troops!")
                        game_unit.cpu_controller = self
                        self.troops.append(game_unit)
        print(f"\tTROOPS: {self.troops}")

    def seb_ai_turn(self, ai_gold):
        budget = self.ai_gold_gain(ai_gold)
        print(f"Budget: {budget}")
        Clock.schedule_interval(self.check_units_moved, 0.5)
        Clock.schedule_once(self.start_move, 0.02)
        return budget

    def start_move(self, dt):
        self.move_time = 0.0
        self.move_units()

    def check_units_moved(self, dt):
        self.move_time += 0.5
        if self.remaining_move_troops:
            # print(f"remaining move {len(self.remaining_move_troops)}")
            self.move_remaining_units()
        elif not self.hex_map.moving_units:
            print(f"pass turn from {Globals.CURRENT_TURN}")
            Globals.CURRENT_TURN = (Globals.CURRENT_TURN + 1) % 2
            sound = pygame.mixer.Sound("content/sounds/end_turn.wav")
            sound.play()
            self.game_screen.build_road = False
            self.game_screen.hex_overlay.update_buttons()
            self.game_screen.game_overlay.update(self.game_screen)
            self.game_screen.init_turn()
            return False  # Stop the Clock.schedule_interval
        # else:
            # print(f"moving units {len(self.hex_map.moving_units)}")
            # if (self.move_time > 7.0):
            #    print(f"{self.hex_map.moving_units}")
        return True

    def move_units(self):
        # print(f"Moving units... {self.troops}")
        # for enemy in self.troops:
        #     print(f"\t{enemy} has {enemy.remaining_moves} left")
        # create list of units that still need to be moved
        for game_unit in self.troops:
            if game_unit.is_dead or game_unit.player_owner != 1:
                self.troops.remove(game_unit)
            else:
                self.remaining_move_troops.append(game_unit)
        # print(f"TOTAL to move {len(self.remaining_move_troops)}")
        self.move_remaining_units()

    def move_remaining_units(self):
        if self.game_screen.pending_attack:
            # print("pending attack")
            return

        for game_unit in self.remaining_move_troops:
            hexagon = game_unit.current_hex
            best_objective, best_route = self.hex_map.path_finder.find_nearest_objective(game_unit.current_hex, game_unit, self.eval_for_structure)
            if best_objective is not None:
                # print(f"route from {game_unit.current_hex} to {best_objective}")
                # print(f"{best_route}")
                if best_route and best_route[0].is_blocked_by_enemy_to(game_unit):
                    # start attack
                    for unit in hexagon.game_units:
                        if unit in self.remaining_move_troops:
                            self.remaining_move_troops.remove(unit)
                    self.hex_map.game_rules.launch_ai_attack(game_unit.current_hex, best_route[0])
                    return

                # units share the minimum remaining moves
                min_group_moves = 99
                for unit in hexagon.game_units:
                    min_group_moves = min(min_group_moves, unit.remaining_moves)
                for unit in hexagon.game_units:
                    unit.group_moves = min_group_moves
                # move units as a group
                movement_delay = 0.0
                # print(f"Units present: {hexagon.game_units}")
                for unit in hexagon.game_units:
                    if unit in self.remaining_move_troops:
                        can_move = True
                        if (hexagon.structure is not None) and hexagon.structure.has_garrison:
                            # make sure this unit leaving won't leave the structure undefended
                            can_move = False
                            for garrison_unit in hexagon.game_units:
                                if (garrison_unit != unit) and garrison_unit.done_moving:
                                    can_move = True
                                    break
                        if can_move:
                            # move unit if it doesn't need to stay as garrison
                            unit.start_move_to(best_objective, self.hex_map, movement_delay)
                            movement_delay += 0.1
                        self.remaining_move_troops.remove(unit)
            else:
                print("No City found!")
                RNG_x = random.randint(0, hexmap.GRID_WIDTH-1)
                RNG_y = random.randint(0, hexmap.GRID_HEIGHT-1)
                best_objective, best_route = self.hex_map.path_finder.find_nearest_objective(game_unit.current_hex, game_unit, self.eval_for_exploration)
                if best_route and best_route[0].is_blocked_by_enemy_to(game_unit):
                    # start attack
                    for unit in hexagon.game_units:
                        if unit in self.remaining_move_troops:
                            self.remaining_move_troops.remove(unit)
                    self.hex_map.game_rules.launch_ai_attack(game_unit.current_hex, best_route[0])
                    return

                movement_delay = 0.0
                # units share the minimum remaining moves
                min_group_moves = 99
                for unit in hexagon.game_units:
                    min_group_moves = min(min_group_moves, unit.remaining_moves)
                for unit in hexagon.game_units:
                    unit.group_moves = min_group_moves

                if game_unit in self.remaining_move_troops:
                    can_move = True
                    if (hexagon.structure is not None) and hexagon.structure.has_garrison:
                        # make sure this unit leaving won't leave the structure undefended
                        can_move = False
                        for garrison_unit in hexagon.game_units:
                            if (garrison_unit != game_unit) and garrison_unit.done_moving:
                                can_move = True
                                break
                    if can_move:
                        # move unit if it doesn't need to stay as garrison
                        game_unit.start_move_to(best_objective, self.hex_map, movement_delay)
                        movement_delay += 0.1
                    self.remaining_move_troops.remove(game_unit)

                #self.remaining_move_troops.remove(game_unit)

    def eval_for_structure(self, eval_hex):
        return (eval_hex.structure is not None) and (eval_hex.structure.has_garrison or eval_hex.structure.name == "Farm") and (eval_hex.structure.player_owner == 0) and (eval_hex.fog_level[1] <= 1)

    def eval_for_exploration(self, eval_hex):
        return eval_hex.fog_level[1] == 2
    def ai_gold_gain(self, ai_gold):
        budget = 0
        for structure in self.hex_map.structures:
            if structure.recruitable_units and structure.player_owner == 1:
                unit_selection = structure.recruitable_units[random.randint(0, len(structure.recruitable_units) - 1)]
                # print(f"Remaining Gold: {ai_gold}")
                # print(f"Unit cost: {unit_selection.cost}")
                # @TODO FIXMESTEVE - need unit cost here, but not instantiated.
                unit_cost = 40
                if unit_cost <= ai_gold:
                    new_unit = structure.hex_position.add_unit(unit_selection, 1)
                    budget += new_unit.cost
                    ai_gold -= new_unit.cost
                    new_unit.cpu_controller = self
                    self.troops.append(new_unit)
                    if ai_gold <= 0:
                        return budget
        return budget

    def entered_hex(self, hexagon, unit):
        if hexagon.structure is not None:
            if hexagon.structure.name == "Farm" and hexagon.structure.player_owner != 1:
                # print("PILLAGE")
                hexagon.remove_structure(self.game_screen.hex_map)
                sound = pygame.mixer.Sound("content/sounds/Pillage_Farm.wav")
                sound.play()

    def fortify(self, unit, hexagon):
        if (hexagon.structure is not None) and hexagon.structure.container_structure:
            return
        if unit.is_fortified() or unit.player_owner != 1:
            return
        if unit.remaining_moves != unit.movement_speed:
            return
        unit.remaining_moves = 0.0
        sound = pygame.mixer.Sound("content/sounds/Select.wav")
        sound.play()

        # fortify unit, and grouped units if grouped
        unit.is_fortified = True
        index = 0
        for game_unit in hexagon.game_units:
            if unit == game_unit:
                # self.unit_forts[index].opacity = 1.0
                break
            index += 1

        # self.fortified_label.opacity = 1.0

        sound = pygame.mixer.Sound("content/sounds/Fortify.wav")
        sound.play()
