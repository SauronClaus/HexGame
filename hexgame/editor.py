import pygame
from menupopups import SaveMenuPopup
from menupopups import StructureMenuPopup
from menupopups import UnitMenuPopup
from menupopups import LoadScreenPopup
from structure import CityStructure
from GameUnits import Phalanx
import Globals


class Editor:
    def __init__(self, in_game_screen):
        self.game_screen = in_game_screen
        self.selected_structure_type = CityStructure
        self.selected_unit_type = Phalanx

    def handle_edit_key_down(self, instance, keyboard, keycode, text, modifiers):
        # print("editor key down")
        screen = self.game_screen
        terrain_dictionary = {'f': "Forest", 'g': "Grasslands", 'h': "Hills", 'm': "Mountains", 'w': "Water"}
        new_terrain = terrain_dictionary.get(text, "")
        if new_terrain != "":
            # Remove the hex's widget and add the new one; that should be all.
            change_hex = screen.hex_map.find_hex_at_position(screen.scroll_view.last_touch_x, screen.scroll_view.last_touch_y)
            screen.hex_map.update_hex_terrain(new_terrain, screen.scroll_view.last_touch_x, screen.scroll_view.last_touch_y)
            return True
        elif text == 'p':
            new_unit = screen.hex_map.add_unit(self.selected_unit_type, screen.currently_selected_hex,
                                             Globals.CURRENT_TURN)
            return True
        elif text == 'c':
            # print("Received C!")
            sound = pygame.mixer.Sound("content/sounds/Construction.wav")
            # Play the sound
            sound.play()
            screen.place_structure(self.selected_structure_type)
            return True
        elif text == 'r':
            screen.hex_map.update_road(screen.currently_selected_hex)
            return True
        elif text == 'b':
            print("blank")
            screen.hex_map.clear_hex(screen.scroll_view.last_touch_x, screen.scroll_view.last_touch_y)
            return True
        elif (text == '1') or (text == '2') or (text == '3') or (text == '4') or (text == '5') or (text == '0'):
            screen.hex_map.update_river(screen.scroll_view.last_touch_x, screen.scroll_view.last_touch_y, int(text))
            return True
        elif text == 's':
            popup = SaveMenuPopup(self.game_screen)
            popup.open()
            return True
        elif text == 'q':
            structure_types = screen.hex_map.structure_types
            popup = StructureMenuPopup(structure_types, screen, Globals.CURRENT_TURN, structure_pos_x=screen.scroll_view.last_touch_x,
                                       structure_pos_y=screen.scroll_view.last_touch_y)
            popup.open()
            return True
        elif text == "o":
            unit_types = screen.hex_map.unit_types
            popup = UnitMenuPopup(unit_types, screen, Globals.CURRENT_TURN, unit_pos_x=screen.scroll_view.last_touch_x,
                                  unit_pos_y=screen.scroll_view.last_touch_y)
            popup.open()
            return True
        elif text == 'l':
            popup = LoadScreenPopup(screen)
            popup.open()
            return True
        elif text == "[":
            Globals.CURRENT_TURN = 0
            screen.game_overlay.update(screen)
            return True
        elif text == "]":
            Globals.CURRENT_TURN = 1
            screen.game_overlay.update(screen)
            return True
        return False
