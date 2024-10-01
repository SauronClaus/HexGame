import json
import os

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.graphics import Color, Rectangle
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.properties import NumericProperty
from kivy.properties import ObjectProperty
from kivy.clock import Clock

import ini
from hexmap import HexMap
from GameRules import GameRules
from maprendering import HexMapWidget
from menupopups import LoadScreenPopup, PauseMenuPopup
from HUD import HexagonInfoOverlay
from HUD import GameInfoOverlay, EditorInfoOverlay
from HUD import BattleInfoOverlay
from HUD import VictoryInfoOverlay
from menu import MenuScreen

from editor import Editor

from Constants import SERVER_HOST
from Constants import SERVER_PORT
import Globals
import pygame
import socket
from Globals import LOCAL_PLAYER, CURRENT_TURN
from ai_control import CPU
from tutorial import TutorialScreen


class CustomScrollView(ScrollView):
    # Properties to store the last touch positions within the content
    last_touch_x = NumericProperty(0)
    last_touch_y = NumericProperty(0)
    game_screen = ObjectProperty(None)

    def on_touch_down(self, touch):
        # Continue with the regular touch handling of ScrollView
        super(CustomScrollView, self).on_touch_down(touch)

        # Check if the touch is within the bounds of the ScrollView
        if self.collide_point(*touch.pos):
            # Convert window touch position to local scrollView position
            local_x = touch.x - self.x
            local_y = touch.y - self.y

            # Calculate the content's current position based on scroll
            # print(f" touch {touch.x} {touch.y}")
            # print(f" scroll {self.scroll_x} {self.scroll_y}")
            # print(f" dim {self.width} {self.height}")
            # print(f" local {local_x} {local_y}")
            # print(f" view port size {self.viewport_size[0]} {self.viewport_size[1]}")
            content_x = self.scroll_x * (self.viewport_size[0] - self.width) + local_x
            content_y = self.scroll_y * (self.viewport_size[1] - self.height) + local_y

            # Update the properties
            self.last_touch_x = content_x
            self.last_touch_y = content_y
            self.game_screen.touch_location_updated(touch, self.last_touch_x, self.last_touch_y)
            # print(f"Touch within ScrollView at: ({content_x}, {content_y})")
            # print(f"Stored properties: ({self.last_touch_x}, {self.last_touch_y})")
            return True
        return False


# Define game screen
class GameScreen(Screen):
    def __init__(self, **kwargs):
        super(GameScreen, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.currently_selected_hex = None
        self.currently_selected_unit = None

        # ScrollView setup
        self.scroll_view = CustomScrollView(do_scroll_x=True, do_scroll_y=True, size_hint=(1, 1), width=1920, height=1080)
        self.scroll_view.game_screen = self

        self.current_map = ini.DEFAULT_MAP
        self.hex_map = HexMap(ini.DEFAULT_MAP)
        self.game_rules = GameRules(self)
        self.hex_map.game_rules = self.game_rules
        self.hex_map_widget = HexMapWidget(self.hex_map, self)
        self.hex_map_widget.size_hint = (None, None)
        self.hex_map_widget.size = self.hex_map_widget.minimum_size()
        self.scroll_view.add_widget(self.hex_map_widget)
        self.hex_map.hex_map_widget = self.hex_map_widget
        self.hex_map_widget.update_canvas()
        self.add_widget(self.scroll_view)
        self.battle_overlay = BattleInfoOverlay(self, size_hint=(0.5, 0.5), pos_hint={'right': 0.75, 'top': 0.75})
        self.victory_overlay = VictoryInfoOverlay(size_hint=(0.5, 0.5), pos_hint={'right': 0.75, 'top': 0.75})
        self.hex_overlay = HexagonInfoOverlay(self, size_hint=(0.4, 0.15), pos_hint={"x": 0.3, "y": 0.01})
        self.add_widget(self.hex_overlay)

        self.game_overlay = GameInfoOverlay(size_hint=(0.125, 0.125), pos_hint={'right': 1, 'top': 1})
        self.add_widget(self.game_overlay)

        self.game_over = False
        self.editor = None

        self.menuMode = False
        self.move_active = False
        self.build_road = False
        self.pending_attack = False
        self.pending_road_hex = None

        self.select_hex_sound = "content/sounds/hex_select.wav"
        # Bind keyboard input
        Window.bind(on_key_down=self.on_key_down)

        with self.canvas.before:
            Color(0.75, 0.75, 0.64, 1)  # tan color
            self.rect = Rectangle(size=self.size, pos=self.pos)

        self.scroll_view.bind(size=self._update_rect, pos=self._update_rect)
        Window.bind(on_key_down=self.on_key_down)

        Clock.schedule_interval(self.check_scroll_movement, 0.01)  # check every 0.1 seconds

        # Update units every 0.025 seconds
        Clock.schedule_interval(self.update_units, 0.025)

        game_id_file = open("game_id.txt", "r")
        Globals.GAME_ID = int(game_id_file.read())
        game_id_file.close()
        if self.current_map == "New Blank Map":
            print("Selected a blank map.")
            self.reset_map()
            self.current_map = ""
        else:
            self.load_map(self.current_map)
            self.current_map = self.current_map

    def check_scroll_movement(self, dt):
        self.hex_map_widget.update_visible_widgets()

    def init_selected(self):
        # pick a friendly city as initially selected hex
        self.currently_selected_hex = None
        for column in self.hex_map.hex_grid:
            for hexagon in column:
                if (hexagon.structure is not None) and (hexagon.structure.player_owner == 0) and (hexagon.structure.name == 'City'):
                    self.currently_selected_hex = hexagon
                    break

        # fallback is central hex
        if self.currently_selected_hex is None:
            self.currently_selected_hex = self.hex_map.find_hex_at_position(self.hex_map_widget.visible_x_left + 0.5 * self.scroll_view.width, self.hex_map_widget.visible_y_bottom + 0.5 * self.scroll_view.height)

        self.select_unit()
        self.currently_selected_hex.should_outline = True
        print(f"{self.currently_selected_hex.index_x}, {self.currently_selected_hex.index_y} now outlined.")
        self.hex_map_widget.place_outline()
        self.hex_overlay.update_hex(self.currently_selected_hex, self.currently_selected_unit)

    def open_loadscreen_popup(self, dt):
        print("Opening Loadscreen")
        popup = LoadScreenPopup(self)
        popup.auto_dismiss = False
        popup.open()

    def update_units(self, dt):
        self.hex_map.update_units(dt, self.currently_selected_hex)
        if self.pending_attack:
            self.battle_overlay.update_battle(dt)
        if (self.currently_selected_hex is not None) and self.currently_selected_hex.needs_update:
            self.currently_selected_hex.needs_update = False
            if self.currently_selected_unit is None:
                self.select_unit()
            self.hex_overlay.update_hex(self.currently_selected_hex, self.currently_selected_unit)

    def on_key_down(self, instance, keyboard, keycode, text, modifiers):
        print("key down " + str(text))
        if self.menuMode:
            return False
        else:
            if text == 'e' and Globals.EDIT_ALLOWED:
                print("Starting edit mode")
                self.toggle_edit_mode()
                return True  # Indicate that the key was handled
            elif keycode == 41:
                pause_menu = PauseMenuPopup(self)
                pause_menu.open()
            elif text == 'i' and not ini.RELEASE:
                selected_hex = self.currently_selected_hex
                print(f"User Gold: {self.game_rules.player_gold}")
                print(f"Hex at ({selected_hex.index_x},{selected_hex.index_y}): Fog Level {selected_hex.fog_level[Globals.LOCAL_PLAYER]}")
                print(f"\t{selected_hex.visible_by_object}")
                print(f"Units: {selected_hex.game_units}")
                if selected_hex.visible_by_object[0]:
                    print("True")
                return True
            elif text == '[' and not ini.RELEASE:
                print("Switching to player 0 fog")
                Globals.LOCAL_PLAYER = 0
                self.hex_map.fog_controller.place_fog_war()
                self.hex_map.fog_controller.render_fog_war()
            elif text == ']' and not ini.RELEASE:
                print("Switching to player 1 fog")
                Globals.LOCAL_PLAYER = 1
                self.hex_map.fog_controller.place_fog_war()
                self.hex_map.fog_controller.render_fog_war()
            elif Globals.EDIT_MODE:
                print("edit mode active")
                if self.editor is None:
                    self.editor = Editor(self)
                return self.editor.handle_edit_key_down(instance, keyboard, keycode, text, modifiers)


        print(f"Instance: {instance}, keycode: {keycode}, text: {text}, modifiers: {modifiers}")
        return False

    def toggle_edit_mode(self, override=None):
        if override is not None:
            Globals.EDIT_MODE = override
            self.hex_map_widget.edit_mode = override
        else:
            Globals.EDIT_MODE = not Globals.EDIT_MODE  # Toggle edit mode
            self.hex_map_widget.edit_mode = Globals.EDIT_MODE
        self.remove_widget(self.game_overlay)
        if Globals.EDIT_MODE:
            self.game_overlay = EditorInfoOverlay(size_hint=(0.125, 0.4), pos_hint={'right': 1, 'top': 1})
        else:
            self.game_overlay = GameInfoOverlay(size_hint=(0.125, 0.125), pos_hint={'right': 1, 'top': 1})
        self.add_widget(self.game_overlay)

        # update fog when edit mode is toggled
        for column in self.hex_map.hex_grid:
            for hexagon in column:
                hexagon.fog_level[Globals.LOCAL_PLAYER] = 2
        self.hex_map.fog_controller.place_fog_war()
        self.hex_map.fog_controller.render_fog_war()
        self.game_overlay.update_year()
        self.hex_overlay.update_hex(self.currently_selected_hex, self.currently_selected_unit)
        print("Edit mode active " + str(Globals.EDIT_MODE))
        print("Current Player " + str(Globals.LOCAL_PLAYER))

    # @TODO FIXMESTEVE both sides could be AI!
    def is_AI_turn(self):
        return Globals.CURRENT_TURN == 1

    def construct_road(self, road_builder, start_hex, new_hex):
        action_sound = "content/sounds/Click_Fail.wav"
        if self.game_rules.construct_road(road_builder, start_hex, new_hex):
            action_sound = "content/sounds/Construction.wav"
            if not self.is_AI_turn():
                self.game_overlay.update(self)
        if not self.is_AI_turn():
            sound = pygame.mixer.Sound(action_sound)
            sound.play()

    def display_victory(self, victorious_player):
        self.add_widget(self.victory_overlay)
        self.victory_overlay.create_victory_layout(victorious_player)
        self.game_over = True
        if victorious_player == 0:
            sound = pygame.mixer.Sound("content/sounds/Victory.wav")
            sound.play()
        else:
            sound = pygame.mixer.Sound("content/sounds/Defeat.wav")
            sound.play()

    def move_or_attack(self, from_hex, new_hex):
        # move units in old hex
        self.pending_attack = self.game_rules.is_pending_attack(from_hex, new_hex)
        if self.pending_attack:
            print("pending attack")
            self.move_active = False
            # bring up battle overlay, which gives choice whether to launch or cancel attack
            self.add_widget(self.battle_overlay)
            self.battle_overlay.create_battle_layout(from_hex, new_hex)
        else:
            if (self.currently_selected_unit is not None) and not self.currently_selected_unit.is_grouped:
                self.currently_selected_unit.start_move_to(new_hex, self.hex_map, 0.0)
            else:
                # units share the minimum remaining moves
                min_group_moves = 99
                for unit in from_hex.game_units:
                    min_group_moves = min(min_group_moves, unit.remaining_moves)
                for unit in from_hex.game_units:
                    unit.group_moves = min_group_moves
                # move units as a group
                movement_delay = 0.0
                i = 0
                temp_iter = []
                for unit in from_hex.game_units:
                    if unit.player_owner == Globals.CURRENT_TURN:
                        temp_iter.append(unit)
                for unit in temp_iter:
                    #print(f"Move unit {i}/{from_hex.game_units}.")
                    unit.start_move_to(new_hex, self.hex_map, movement_delay)
                    movement_delay += 0.1
                    i+=1
                    #print(f"{from_hex.game_units}")

    def touch_location_updated(self, touch, last_touch_x, last_touch_y):
        if self.battle_overlay.parent is not None or self.game_over:
            return
        if self.hex_overlay.handle_touch(touch):
            return
        new_hex = self.hex_map.find_hex_at_position(last_touch_x, last_touch_y)
        if new_hex is None:
            return
        if new_hex != self.currently_selected_hex:
            if self.currently_selected_hex is not None:
                # print(f"Across edge {new_hex.get_edge_index_to(self.currently_selected_hex)}")
                self.currently_selected_hex.should_outline = False
                # Make sure not in edit mode and that it's the player's turn
                if not self.pending_attack and not Globals.EDIT_MODE and (Globals.LOCAL_PLAYER == Globals.CURRENT_TURN) and (self.currently_selected_unit is not None) and (self.currently_selected_unit.player_owner == Globals.CURRENT_TURN):
                    if self.build_road:
                        self.construct_road(self.currently_selected_unit, self.pending_road_hex, new_hex)
                        self.pending_road_hex = new_hex
                    elif self.move_active:
                        self.move_or_attack(self.currently_selected_hex, new_hex)
            self.move_active = False
            self.build_road = False
            if not self.pending_attack:
                self.currently_selected_hex = new_hex
                sound = pygame.mixer.Sound(self.select_hex_sound)
                sound.play()
                self.select_unit()
                new_hex.should_outline = True
                # print(f"{new_hex.index_x}, {new_hex.index_y} now outlined.")
                self.hex_map_widget.place_outline()
                self.hex_overlay.update_hex(new_hex, self.currently_selected_unit)

    def start_building_road(self, road_builder):
        if self.game_rules.can_build_road(road_builder):
            # look for road destination input
            self.build_road = True
            self.pending_road_hex = self.currently_selected_hex
            self.hex_overlay.update_hex(self.currently_selected_hex, self.currently_selected_unit)

    def AI_build_road(self, road_builder, start_hex, end_hex):
        if self.game_rules.can_build_road(road_builder):
            self.construct_road(road_builder, start_hex, end_hex)

    def select_unit(self):
        self.currently_selected_unit = None
        best_index = 9999
        # pick the unit with the highest render order, because it will be the one drawn on top
        for next_unit in self.currently_selected_hex.game_units:
            new_index = 9999
            if next_unit.sprite in self.hex_map_widget.unit_layout.children:
                new_index = self.hex_map_widget.unit_layout.children.index(next_unit.sprite)
            if (self.currently_selected_unit is None) or (new_index < best_index):
                self.currently_selected_unit = next_unit
                best_index = new_index

    def place_structure(self, structure_class):
        opacity = 1.0
        if self.hex_map.update_hex_structure(structure_class, self.currently_selected_hex, Globals.CURRENT_TURN, self.currently_selected_unit):
            if not Globals.EDIT_MODE:
                print(f"Purchasing structure for {Globals.CURRENT_TURN} cost {structure_class.cost}")
                self.game_rules.player_gold[Globals.CURRENT_TURN] -= structure_class.cost
                opacity = 1.0/(structure_class.build_time + 1)
            else:
                self.currently_selected_hex.structure.remaining_build_time = 0
                self.currently_selected_hex.structure.construction_completed(self.hex_map)
            self.currently_selected_hex.structure_image.color = [1, 1, 1, opacity]
            self.game_overlay.update(self)
            self.hex_overlay.update_hex(self.currently_selected_hex, self.currently_selected_unit)
            if self.editor is not None:
                self.editor.selected_structure_type = structure_class

    def place_unit(self, unit_type):
        if unit_type is not None:
            new_unit = self.hex_map.add_unit(unit_type, self.currently_selected_hex, Globals.CURRENT_TURN)
            self.hex_overlay.update_hex(self.currently_selected_hex, new_unit)
            self.currently_selected_unit = new_unit
            if new_unit.build_sound != "":
                sound = pygame.mixer.Sound(new_unit.build_sound)
                sound.play()
            if not Globals.EDIT_MODE:
                print(f"Purchasing Unit for {Globals.CURRENT_TURN}")
                self.game_rules.player_gold[Globals.CURRENT_TURN] -= new_unit.cost
                self.game_overlay.update(self)

    def init_turn(self):
        self.game_rules.init_turn()
        self.game_overlay.update(self)
        # update hex overlay information
        if self.currently_selected_hex is not None:
            self.hex_overlay.update_hex(self.currently_selected_hex, self.currently_selected_unit)

    def current_hex_construction_completed(self, garrison):
        if self.currently_selected_unit is None:
            self.currently_selected_unit = garrison
        self.hex_overlay.update_hex(self.currently_selected_hex, self.currently_selected_unit)

    def pass_turn(self):
        print(f"pass turn from {Globals.CURRENT_TURN}")
        Globals.DATE -= 2
        Globals.CURRENT_TURN = (Globals.CURRENT_TURN + 1) % 2
        sound = pygame.mixer.Sound("content/sounds/end_turn.wav")
        sound.play()
        self.build_road = False
        self.init_turn()
        self.hex_overlay.update_buttons()
        print("Saving Map (end of player turn)")
        self.save_map(self.current_map)

        if Globals.AI_ACTIVE and Globals.CURRENT_TURN == 1:
            print(f"Starting AI... Gold: {self.game_rules.player_gold[1]}")
            if self.hex_map.cpu is None:
                self.hex_map.cpu = CPU(self, self.hex_map)
            return_gold = self.hex_map.cpu.seb_ai_turn(self.game_rules.player_gold[1])
            self.game_rules.player_gold[1] -= return_gold
            print("Saving Map (end of AI turn)")
            self.save_map(self.current_map)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def _update_menu_rect(self, instance, value):
        self.menu.rect.pos = instance.pos
        self.menu.rect.size = instance.size

    def load_map(self, map_name):
        self.load_from_file(map_name)
        print("load map)")
        self.init_turn()
        self.init_selected()
        Globals.GAME_ID += 1
        game_file = open("game_id.txt", "w")
        game_file.write(str(Globals.GAME_ID))
        game_file.close()

    def save_map(self, filename):
        if not ini.AI_TRAINING_MODE:
            print("Save hex map (Not Training Mode)")
            map_data = self.hex_map.save_hex_map()
            map_data["player_gold"] = self.game_rules.player_gold
            map_data["current_turn"] = Globals.CURRENT_TURN
            with open(f"Maps\\{filename}{Globals.GAME_ID}.json", 'w') as file:
                json.dump(map_data, file, indent=4)
            print("Saved hex map!")
        else:
            print(f"Save hex map (Training Mode)\tTurn: {Globals.CURRENT_TURN}")
            map_data = self.hex_map.save_hex_map()
            map_data["player_gold"] = self.game_rules.player_gold
            map_data["current_turn"] = Globals.CURRENT_TURN
            if not os.path.exists(f"Maps\\{filename}{Globals.GAME_ID}"):
                os.makedirs(f"Maps\\{filename}{Globals.GAME_ID}")
            with open(f"Maps\\{filename}{Globals.GAME_ID}\\snapshot{ini.SNAPSHOT_NUM}.json", 'w') as file:
                json.dump(map_data, file, indent=4)
            print("Saved hex map!")
            ini.SNAPSHOT_NUM += 1

    def load_from_file(self, filename):
        with open("Maps\\" + filename + ".json", 'r') as file:
            map_data = json.load(file)
        self.game_rules.player_gold = map_data["player_gold"]
        self.hex_map.load_hex_map(filename)

    def reset_map(self):
        self.hex_map.initialize_map("")
        print("reset map")

    def find_parent_app(self):
        app = App.get_running_app()
        print(f"The parent app is {app}")
        return app


# Define game app
class GameApp(App):
    def build(self):
        Window.size = ini.WINDOW_SIZE
        Window.fullscreen = ini.RELEASE
        Window.bind(on_keyboard=self.on_key_press)
        self.screen_manager = ScreenManager()
        self.menu_screen = MenuScreen(name='menu')
        self.game_screen = GameScreen(name='game')
        self.tutorial_screen = TutorialScreen(name='tutorial')
        self.screen_manager.add_widget(self.menu_screen)
        self.screen_manager.add_widget(self.game_screen)
        self.screen_manager.add_widget(self.tutorial_screen)
        return self.screen_manager

    def on_key_press(self, window, key, scancode, codepoint, modifier):
        return True  # to accept the key press, otherwise return False


if __name__ == '__main__':
    pygame.mixer.init()
#    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#    server_socket.bind((SERVER_HOST, SERVER_PORT))
#    server_socket.listen(1)
#    print(f'Server listening on {SERVER_HOST}:{SERVER_PORT}')

#    client_socket, client_address = server_socket.accept()
#    print(f'Connection from {client_address}')
    GameApp().run()
