from kivy.uix.floatlayout import FloatLayout

import Globals
import ini
from Constants import HEX_SIZE, ROOT_3

class Fog_Controller:
    def __init__(self, in_hex_map):
        self.hex_map = in_hex_map
        hint = (1.33 / self.hex_map.grid_width, 1.33 / self.hex_map.grid_height)
        self.size = (0.75 * HEX_SIZE * self.hex_map.grid_width, 0.5 * ROOT_3 * HEX_SIZE * self.hex_map.grid_height)
        layout_pos = (0.0, 0.0)

        self.layout = FloatLayout(size_hint=hint, size=self.size, pos=layout_pos)

    def reset_layout(self):
        hint = (1.33 / self.hex_map.grid_width, 1.33 / self.hex_map.grid_height)
        layout_pos = (0.0, 0.0)

        self.layout = FloatLayout(size_hint=hint, size=self.size, pos=layout_pos)

    # Places the fog of war across the map.
    def place_fog_war(self):
        print(f"place fog of war for {Globals.LOCAL_PLAYER}")
        num = 0
        if ini.NO_FOG:
            return
        rendered_again_x = []
        rendered_again_y = []

        for y, column in enumerate(self.hex_map.hex_grid):
            for x, hexagon in enumerate(column):
                # print(f"Hexagon: {hexagon.fog_level}")
                if hexagon.structure is not None and hexagon.structure.player_owner == Globals.LOCAL_PLAYER:
                    view_level = hexagon.structure.view_distance
                    # print(f"View Level: {view_level}")
                    adj_hexes = [hexagon]
                    for index in range(view_level):
                        temp_array = [hexagon]
                        # print(f"index: {index}")
                        for modify_hex in adj_hexes:
                            # print("Modifying hexagon")
                            modify_hex.fog_level[Globals.LOCAL_PLAYER] = 0
                            if hexagon.structure not in modify_hex.visible_by_object[Globals.LOCAL_PLAYER]:
                                modify_hex.visible_by_object[Globals.LOCAL_PLAYER].append(hexagon.structure)
                            rendered_again_x.append(modify_hex.index_x)
                            rendered_again_y.append(modify_hex.index_y)

                            adjacent_hexes = modify_hex.adjacent_hexes
                            # print(f"Original Hex: {modify_hex.index_x},{modify_hex.index_y}")
                            for visible_hex in adjacent_hexes:
                                if visible_hex is not None:
                                    # print(f"\tVisible hex; changing {visible_hex.index_x},{visible_hex.index_y} to fog level 0")
                                    temp_array.append(visible_hex)
                                    visible_hex.fog_level[Globals.LOCAL_PLAYER] = 0
                                    rendered_again_x.append(visible_hex.index_x)
                                    rendered_again_y.append(visible_hex.index_y)
                                    if hexagon.structure not in visible_hex.visible_by_object[Globals.LOCAL_PLAYER]:
                                        visible_hex.visible_by_object[Globals.LOCAL_PLAYER].append(hexagon.structure)
                        adj_hexes = temp_array
                if hexagon.game_units:
                    rendered_troops_hexes = self.add_fog_to_location(hexagon)
                    for troop_hex in rendered_troops_hexes:
                        # print("Added troop_hex")
                        rendered_again_x.append(troop_hex.index_x)
                        rendered_again_y.append(troop_hex.index_y)
        # print(rendered_again_x, rendered_again_y)
        for y, column in enumerate(self.hex_map.hex_grid):
            for x, hexagon in enumerate(column):
                if hexagon.fog_level[Globals.LOCAL_PLAYER] == 0 and not (
                        hexagon.index_x in rendered_again_x and hexagon.index_y in rendered_again_y) and not hexagon.visible_by_object[Globals.LOCAL_PLAYER]:
                    # print(f"{hexagon.index_x},{hexagon.index_y}: Fog Level {hexagon.fog_level[Globals.LOCAL_PLAYER]}")
                    # print(f"\t{hexagon.visible_by_object[Globals.LOCAL_PLAYER]}")
                    hexagon.fog_level[Globals.LOCAL_PLAYER] = 1
        return num

    # Renders the fog of war sprites onto the map.
    def render_fog_war(self):
        player = Globals.LOCAL_PLAYER
        # print(f"Rendering fog of war for {Globals.LOCAL_PLAYER}")
        if not Globals.EDIT_MODE:
            opacity_level = [0.0, 0.5, 1.0]
            for column in self.hex_map.hex_grid:
                for hexagon in column:
                    if hexagon.fog_image is not None:
                        # print(f"Rendering {hexagon.index_x},{hexagon.index_y} at fog level {hexagon.fog_level[Globals.LOCAL_PLAYER]}")
                        hexagon.fog_image.opacity = opacity_level[hexagon.fog_level[player]]
                        if hexagon.mark_visible:
                            for unit in hexagon.game_units:
                                if (hexagon.fog_level[player] == 0) or ini.NO_FOG:
                                    if unit.sprite.parent is None:
                                        self.hex_map.hex_map_widget.add_unit_widget(unit.sprite)
                                elif unit.sprite.parent is not None:
                                    unit.sprite.parent.remove_widget(unit.sprite)
        else:
            for column in self.hex_map.hex_grid:
                for hexagon in column:
                    hexagon.fog_image.opacity = 0.0

    # Adds units to who can see this space. NOTE: this lowers fog levels.
    def add_fog_to_location(self, hexagon):
        # print("Setting the unit fog-")
        # print(f"{hexagon.game_units}")
        troop_hexes = []
        update_later = []
        # print(f"Hexagon Units: {hexagon.game_units}")
        one_thirteen = self.hex_map.get_hexagon(1, 13)
        #print(f"1 13! {one_thirteen.visible_by_object}")
        if hexagon.game_units:
            #print("The hex has a unit!")
            #print(f"On coords {hexagon.index_x},{hexagon.index_y} there are these units: {hexagon.game_units}")
            view_level = -1
            view_level_per_unit = {}
            for game_unit in hexagon.game_units:
                for index in range(game_unit.view_distance):
                    view_level_per_unit.setdefault(index, []).append(game_unit)
                if game_unit.view_distance > view_level and game_unit.player_owner == Globals.LOCAL_PLAYER:
                    view_level = game_unit.view_distance

            adj_hexes = [hexagon]
            game_units_eyes = []
            # print(f"View Level: {view_level}")
            for index in range(view_level):
                temp_array = [hexagon]
                # print(f"index: {index}")
                # print(f"{adj_hexes}")
                for modify_hex in adj_hexes:
                    # print("Modifying hexagon")
                    if view_level >= -1:
                        for unit in view_level_per_unit[index]:
                            game_units_eyes.append(unit)
                            # print("Loop #1")
                        for unit in game_units_eyes:
                            if unit not in modify_hex.visible_by_object[Globals.LOCAL_PLAYER]:
                                #print(f"\tModify Hex {modify_hex.index_x},{modify_hex.index_y} visible by {unit} for player {Globals.LOCAL_PLAYER}")
                                modify_hex.visible_by_object[Globals.LOCAL_PLAYER].append(unit)
                            # print("Loop #2")
                        modify_hex.fog_level[Globals.LOCAL_PLAYER] = 0
                    troop_hexes.append(modify_hex)
                    update_later.append(modify_hex)
                    # print(f"\tAppended! {update_later}")

                    adjacent_hexes = modify_hex.adjacent_hexes
                    for hexagon in modify_hex.adjacent_hexes:
                        # print(f"\tUpdating later {hexagon}")
                        update_later.append(hexagon)
                    # print(f"Modify Hex: {modify_hex.fog_level[Globals.LOCAL_PLAYER]}")
                    for visible_hex in adjacent_hexes:
                        if visible_hex is not None:
                            # print(f"\tVisible hex; changing {visible_hex.index_x},{visible_hex.index_y} to fog level 0")
                            temp_array.append(visible_hex)
                            visible_hex.fog_level[Globals.LOCAL_PLAYER] = 0
                            for unit in game_units_eyes:
                                if unit not in visible_hex.visible_by_object[Globals.LOCAL_PLAYER]:
                                    #print(f"\tVisible Hex {modify_hex.index_x},{modify_hex.index_y} visible by {unit} for player {Globals.LOCAL_PLAYER}")
                                    visible_hex.visible_by_object[Globals.LOCAL_PLAYER].append(unit)
                                    update_later.append(visible_hex)
                                # print("Loop #3")
                                troop_hexes.append(visible_hex)
                            # else:
                            # print(f"\tVisible Hex is None!")
                adj_hexes = temp_array
        else:
            print("Skipping that part")
        # print(f"Troop Hexes: {update_later}")
        for hexagon in update_later:
            if not Globals.EDIT_MODE and hexagon is not None:
                if hexagon.fog_image is not None:
                    opacity_level = [0.0, 0.5, 1.0]
                    # print(f"Rendering {hexagon.index_x},{hexagon.index_y} at fog level {hexagon.fog_level[Globals.LOCAL_PLAYER]}")
                    hexagon.fog_image.opacity = opacity_level[hexagon.fog_level[Globals.LOCAL_PLAYER]]
                    if hexagon.mark_visible:
                        for unit in hexagon.game_units:
                            if (hexagon.fog_level[Globals.LOCAL_PLAYER] == 0) or ini.NO_FOG:
                                if unit.sprite.parent is None:
                                    self.hex_map.hex_map_widget.add_unit_widget(unit.sprite)
                            elif unit.sprite.parent is not None:
                                unit.sprite.parent.remove_widget(unit.sprite)
        #print(f"1 13! {one_thirteen.visible_by_object}")
        return troop_hexes

    # Removes a unit from the list of who can see this space. NOTE: this raises fog levels.
    def remove_fog(self, current_hex, view_distance, to_remove):
        print(f"\tREMOVEING FOG CENTERED AROUND {current_hex.index_x}, {current_hex.index_y}, with a radius of {view_distance}")
        # print(f"\t{current_hex.visible_by_object}")
        # print(f"Removeable: {to_remove}")
        update_later = []
        adj_hexes = [current_hex]
        for index in range(view_distance):
            temp_array = [current_hex]
            #print(f"index: {index}")
            error_count = 0
            for modify_hex in adj_hexes:
                print(f"\tModifying the hex around {modify_hex.index_x},{modify_hex.index_y}")
                #print("Modifying hexagon")
                # print(f"{modify_hex.visible_by_object} / {to_remove}")
                if to_remove in modify_hex.visible_by_object[0]:
                    modify_hex.visible_by_object[0].remove(to_remove)
                if to_remove in modify_hex.visible_by_object[1]:
                    modify_hex.visible_by_object[1].remove(to_remove)
                # print(modify_hex.visible_by_object)
                if not modify_hex.visible_by_object[Globals.CURRENT_TURN]:
                    modify_hex.fog_level[Globals.CURRENT_TURN] = 1
                update_later.append(modify_hex)
                if not modify_hex.visible_by_object[Globals.LOCAL_PLAYER] and modify_hex.fog_level[Globals.LOCAL_PLAYER] == 0:
                    modify_hex.fog_level[Globals.LOCAL_PLAYER] = 1
                adjacent_hexes = modify_hex.adjacent_hexes
                # print(f"Modify Hex: {modify_hex.fog_level[self.player_owner]}")
                for visible_hex in adjacent_hexes:
                    if visible_hex is not None:
                        print(f"\tVisiblying the hex around {visible_hex.index_x},{visible_hex.index_y}")
                        update_later.append(visible_hex)
                        # print(f"\tVisible hex; changing {visible_hex.index_x},{visible_hex.index_y} to fog level 0")
                        temp_array.append(visible_hex)
                        if visible_hex.index_x == 1 and visible_hex.index_y == 13:
                            print(f"{visible_hex.visible_by_object}")
                            print(f"{to_remove}")

                        if to_remove in visible_hex.visible_by_object[0]:
                            visible_hex.visible_by_object[0].remove(to_remove)
                        if to_remove in visible_hex.visible_by_object[1]:
                            visible_hex.visible_by_object[1].remove(to_remove)

                        if visible_hex.index_x == 1 and visible_hex.index_y == 13:
                            print(f"{visible_hex.visible_by_object}")
                            print(f"{to_remove}")
                        if not visible_hex.visible_by_object[Globals.CURRENT_TURN]:
                            # print(f"No sight in {visible_hex.visible_by_object} for {visible_hex.index_x},{visible_hex.index_y}")
                            visible_hex.fog_level[Globals.CURRENT_TURN] = 1
                    # else:
                    #    print(f"\tVisible Hex is None!")
                        if not visible_hex.visible_by_object[Globals.LOCAL_PLAYER] and visible_hex.fog_level[Globals.LOCAL_PLAYER] == 0:
                            visible_hex.fog_level[Globals.LOCAL_PLAYER] = 1
            adj_hexes = temp_array

        # print(f"Remove_fog {update_later}")
        for hexagon in update_later:
            if not Globals.EDIT_MODE:
                if hexagon.fog_image is not None:
                    opacity_level = [0.0, 0.5, 1.0]
                    # print(f"Rendering {hexagon.index_x},{hexagon.index_y} at fog level {hexagon.fog_level[Globals.LOCAL_PLAYER]}")
                    hexagon.fog_image.opacity = opacity_level[hexagon.fog_level[Globals.LOCAL_PLAYER]]
                    if hexagon.mark_visible:
                        for unit in hexagon.game_units:
                            if (hexagon.fog_level[Globals.LOCAL_PLAYER] == 0) or ini.NO_FOG:
                                if unit.sprite.parent is None:
                                    self.hex_map.hex_map_widget.add_unit_widget(unit.sprite)
                            elif unit.sprite.parent is not None:
                                unit.sprite.parent.remove_widget(unit.sprite)
        #print(f"\tREMOEVED FOG CENTERED AROUND {current_hex.index_x}, {current_hex.index_y}")
        #print(f"\t{current_hex.visible_by_object}")

    def add_fog_widget(self, new_widget):
        if not ini.NO_FOG:
            self.layout.add_widget(new_widget)
