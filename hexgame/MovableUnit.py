from kivy.uix.image import Image
import pygame
import ini
from Constants import HEX_SIZE
import Globals


class MovableUnit:
    def __init__(self, player_owner, spawn_hex):
        self.player_owner = player_owner
        self.current_hex = spawn_hex

        # rendering
        self.image_path = self.get_image_path()
        self.sprite = self.sprite = Image(source=self.image_path, size_hint=(None, None), size=(0.7*HEX_SIZE, 0.7*HEX_SIZE), pos=(0, 0))
        self.dead_image = None

        # path finding and movement
        self.destination_hex = None
        self.final_destination = None
        self.movement_delay = 0.0
        self.route = []
        self.done_moving = True
        self.remaining_moves = 0
        self.group_moves = 0
        self.movement_speed = 1
        self.blocks_enemy = False
        self.moves_on_water = False
        self.moves_on_land = True

        # game state
        self.view_distance = 1    # how far this unit can see (and remove fog)
        self.name = ""
        self.is_dead = False
        self.vanish_time = 0.5
        self.combat_strength = 0
        self.is_fortified = False
        self.is_grouped = False
        self.battle_role = 'Auxiliary'
        self.battle_image = None
        self.cpu_controller = None

        # sounds
        self.active_sound = None
        self.select_sound = ""
        self.move_sound = ""
        self.build_sound = ""

    def is_ready(self):
        return self.remaining_moves >= self.movement_speed

    def fortify(self, should_fortify_group):
        if self.is_fortified:
            return False
        # cannot fortify in container structures
        if (self.current_hex.structure is not None) and self.current_hex.container_structure:
            return False
        self.remaining_moves = 0
        # fortify unit, and grouped units if grouped
        self.is_fortified = True
        index = 0
        if self.is_grouped and should_fortify_group:
            for unit in self.current_hex.game_units:
                if unit.is_grouped and unit.is_ready():
                    unit.fortify(False)
        return True

    def pillage(self, hex_map):
        # cannot pillage container structures
        if (self.current_hex.structure is None) or (self.current_hex.structure.player_owner == self.player_owner) or self.current_hex.structure.container_structure:
            return False
        self.remaining_moves = 0
        self.current_hex.remove_structure(hex_map)
        return True

    # set icon image based on owner
    def get_image_path(self):
        return ''

    def hex_is_impassable(self, hexagon):
        if hexagon.terrain_type.is_water:
            return not self.moves_on_water
        else:
            return hexagon.terrain_type.is_impassable or not self.moves_on_land

    # returns terrain movement cost for this unit - allows overriding of default terrain cost
    def get_terrain_movement_cost(self, terrain_type):
        if terrain_type.is_water:
            if self.moves_on_water:
                return 1
            else:
                return 1000000
        elif not self.moves_on_land:
            return 1000000
        return terrain_type.movement_cost

    # unit is dead, so remove from hex, add to dead_units for death animation
    def killed(self, hex_map):
        self.is_dead = True
        self.sprite.source = self.dead_image
        if self.battle_image is not None:
            self.battle_image.source = self.dead_image
        hex_map.dead_units.append(self)
        self.current_hex.game_units.remove(self)

    # death animation update, called if unit is in dead_units
    def update_death(self, dt, hex_map):
        self.vanish_time -= dt
        if self.vanish_time > 0.25:
            self.sprite.opacity = 1.0
        else:
            self.sprite.opacity -= 4.0 * dt
        scale_rate = 2.0*dt
        scale_factor = 1.0 + scale_rate
        if self.vanish_time < 0.0:
            hex_map.hex_map_widget.remove_widget(self.sprite)
        if self.battle_image is not None:
            if self.vanish_time > 0.25:
                self.battle_image.opacity = 1.0
            else:
                self.battle_image.opacity -= 4.0 * dt
            original_width, original_height = self.battle_image.size
            self.battle_image.size = (original_width * scale_factor, original_height * scale_factor)
            self.battle_image.x = self.battle_image.x - 0.5 * scale_rate * original_width
            self.battle_image.y = self.battle_image.y - 0.5 * scale_rate * original_height
            if self.vanish_time < 0.0:
                if self.battle_image.parent is not None:
                    self.battle_image.parent.remove_widget(self.battle_image)
                self.battle_image = None
        else:
            original_width, original_height = self.sprite.size
            self.sprite.size = (original_width * scale_factor, original_height * scale_factor)
            self.sprite.x = self.sprite.x - 0.5 * scale_rate * original_width
            self.sprite.y = self.sprite.y - 0.5 * scale_rate * original_height

    # returns true if this unit can still move
    def has_remaining_moves(self):
        if self.is_grouped:
            return self.group_moves > 0
        return self.remaining_moves > 0

    # returns true if the move is visible to the local player, so should be animated and sounds played
    def move_visible_to_local_player(self, destination_hex):
        return (self.current_hex.fog_level[0] == 0) or (destination_hex.fog_level[0] == 0) or ini.AI_DEBUG or ini.NO_FOG

    # PUBLIC INTERFACE - this is how you tell a unit to start moving toward final_destination_hex
    def start_move_to(self, final_destination_hex, hex_map, movement_delay):
        if self.has_remaining_moves():
            self.set_final_destination(final_destination_hex, hex_map, movement_delay)

    def update_position(self, dt, hex_map, selected_hex):
        if (self.destination_hex is not None) and not self.move_visible_to_local_player(self.destination_hex):
            # print(f"moving_units remove {self}")
            hex_map.moving_units.remove(self)
            self.movement_delay = -1.0
            destination_x, destination_y = self.destination_hex.get_unit_position(self)
            self.sprite.x = destination_x
            self.sprite.y = destination_y
            self.update_destination(hex_map, selected_hex)
        elif self.movement_delay > 0.0:
            self.movement_delay -= dt
        elif self.destination_hex is not None:
            # print(f"update position {dt}")
            destination_x, destination_y = self.destination_hex.get_unit_position(self)
            reached_x = False
            dir_x = destination_x - self.sprite.x
            if abs(dir_x) < 100.0*dt:
                reached_x = True
                self.sprite.x = destination_x
            else:
                self.sprite.x += 100.0*dt * dir_x/abs(dir_x)
            dir_y = destination_y - self.sprite.y
            if abs(dir_y) < 100.0*dt:
                self.sprite.y = destination_y
                if reached_x:
                    # print(f"moving_units remove {self}")
                    hex_map.moving_units.remove(self)
                    self.update_destination(hex_map, selected_hex)
            else:
                self.sprite.y += 100.0*dt * dir_y/abs(dir_y)
        else:
            hex_map.moving_units.remove(self)

    # INTERNAL
    def move_to_new_hex(self, new_hex, hex_map):
        hex_map.fog_controller.remove_fog(self.current_hex, self.view_distance, self)
        if self.current_hex is not None:
            self.current_hex.game_units.remove(self)
        new_hex.game_units.append(self)
        self.current_hex = new_hex
        hex_map.game_rules.entered_hex(self.current_hex, self)
        if self.current_hex.mark_visible and ((self.current_hex.fog_level[Globals.LOCAL_PLAYER] == 0) or ini.NO_FOG):
            if self.sprite.parent is None:
                hex_map.hex_map_widget.add_unit_widget(self.sprite)
        elif self.sprite.parent is not None:
            self.sprite.parent.remove_widget(self.sprite)
        hex_map.fog_controller.add_fog_to_location(self.current_hex)

    def update_destination(self, hex_map, selected_hex):
        one_thirteen = hex_map.get_hexagon(1, 13)
        print(f"Updating Destination for {self.current_hex.index_x}, {self.current_hex.index_y}")
        if Globals.CURRENT_TURN == 0:
            print(f"One-Thirteen Views START: {one_thirteen.visible_by_object}")
        if self.current_hex == selected_hex:
            selected_hex.needs_update = True
        self.set_final_destination(self.final_destination, hex_map, 0.0)
        # print(f"Destination Hex: {new_hex.index_x},{new_hex.index_y}")
        if Globals.CURRENT_TURN == 0:
            print(f"One-Thirteen Views END: {one_thirteen.visible_by_object}")
    def end_movement(self):
        self.final_destination = None
        self.destination_hex = None
        if self.active_sound is not None:
            self.active_sound.stop()
            self.active_sound = None
        self.done_moving = True

    def set_final_destination(self, new_final_destination, hex_map, movement_delay):
        self.is_fortified = False
        for next_hex in self.route:
            next_hex.path_outline = False
        self.route.clear()
        if (self.current_hex == new_final_destination) or not self.has_remaining_moves():
            self.end_movement()
            return

        self.movement_delay = movement_delay
        if self in hex_map.moving_units:
            print("ERROR - ADDING ALREADY MOVING UNIT")
        else:
            hex_map.moving_units.append(self)
        self.final_destination = new_final_destination
        self.route = hex_map.path_finder.find_path_to(self, self.current_hex, self.final_destination)
        if self.route:
            self.destination_hex = self.route[0]
        else:
            # couldn't find anywhere to move toward final_destination
            self.destination_hex = None
            self.final_destination = self.current_hex
            self.end_movement()
            return
        # print(f"check cost from {self.current_hex.index_x} {self.current_hex.index_y} to {self.destination_hex.index_x} {self.destination_hex.index_y}")
        move_cost = self.destination_hex.get_movement_cost_from(self.current_hex, self)
        # print(f"move cost {move_cost} remaining moves {self.remaining_moves}")
        moves = self.remaining_moves
        if self.is_grouped:
            moves = self.group_moves
        # don't move onto next hex if impassable or cost is greater than remaining_moves, unless still at full movement potential
        if self.destination_hex.is_impassable_to(self) or self.destination_hex.is_blocked_by_enemy_to(self) or ((move_cost > moves) and (self.remaining_moves < self.movement_speed)):
            self.end_movement()
            self.final_destination = self.current_hex
            for next_hex in self.route:
                next_hex.path_outline = False
            self.route.clear()
        else:
            self.done_moving = False
            self.remaining_moves -= move_cost
            self.group_moves -= move_cost
            if (self.move_visible_to_local_player(self.destination_hex)) and (self.active_sound is None):
                if self.select_sound != "":
                    sound = pygame.mixer.Sound(self.select_sound)
                    sound.play()
                if self.move_sound != "":
                    self.active_sound = pygame.mixer.Sound(self.move_sound)
                    self.active_sound.play()
            self.move_to_new_hex(self.destination_hex, hex_map)
        # for local player, show path
        if ini.AI_DEBUG or (self.player_owner == 0):
            for next_hex in self.route:
                next_hex.path_outline = True
            hex_map.hex_map_widget.place_outline()
