from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle, Line
from kivy.metrics import dp
import random
from hexmap import Hexagon
from terrain import TerrainType
import Globals
import ini
import Constants
import pygame
from menupopups import StructureMenuPopup
from menupopups import UnitMenuPopup
from Globals import LOCAL_PLAYER, CURRENT_TURN

class VictoryInfoOverlay(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.attack_hex = None
        self.defend_hex = None
        with self.canvas:
            # Translucent background
            Color(1, 1, 1, 0.8)  # White color with 80% opacity
            self.rect = Rectangle(size=self.size, pos=self.pos)
            # Border
            Color(0, 0, 0)
            self.border = Line(width=2, rectangle=(self.x, self.y, self.width, self.height))
        self.bind(pos=self.update_rect, size=self.update_rect)

        self.victory_label = Label(text="YOU ARE VICTORIOUS!", color=(0, 0, 0, 1), size_hint=(0.5, 0.2), pos_hint={"x": 0.25, "y": 0.5}, halign="center", valign="middle", bold=True, font_size=dp(50))
        self.add_widget(self.victory_label)

    def create_victory_layout(self, winner):
        if winner == 1:
            self.victory_label.text = "YOU HAVE BEEN DEFEATED."

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        self.border.rectangle = (self.x, self.y, self.width, self.height)


class BattleInfoOverlay(FloatLayout):
    def __init__(self, in_game_screen, **kwargs):
        super().__init__(**kwargs)
        self.game_screen = in_game_screen
        self.attack_hex = None
        self.defend_hex = None
        with self.canvas:
            # Translucent background
            Color(1, 1, 1, 0.8)  # White color with 80% opacity
            self.rect = Rectangle(size=self.size, pos=self.pos)
            # Border
            Color(0, 0, 0)
            self.border = Line(width=2, rectangle=(self.x, self.y, self.width, self.height))
        self.bind(pos=self.update_rect, size=self.update_rect)

        self.cancel_button = Button(text='CANCEL ATTACK', size_hint=(None, None), size=(160, 40), pos_hint={"x": 0.25, "y": 0.0}, halign="left", valign="middle")
        self.cancel_button.bind(on_press=self.on_cancel_button_press)
        self.add_widget(self.cancel_button)

        self.attack_button = Button(text='START ATTACK', size_hint=(None, None), size=(160, 40), pos_hint={"x": 0.55, "y": 0.0}, halign="right", valign="middle")
        self.attack_button.bind(on_press=self.on_attack_button_press)
        self.add_widget(self.attack_button)

        self.attack_label = Label(text="Attack Strength:", color=(0, 0, 0, 1), size_hint=(0.5, 0.2), pos_hint={"x": 0.0, "y": 0.15}, halign="left", valign="middle")
        self.add_widget(self.attack_label)

        self.defense_label = Label(text="Defense Strength:", color=(0, 0, 0, 1), size_hint=(0.5, 0.2), pos_hint={"x": 0.5, "y": 0.15}, halign="left", valign="middle")
        self.add_widget(self.defense_label)

        self.num_melee_attackers = 0
        self.num_ranged_attackers = 0
        self.num_cavalry_attackers = 0
        self.num_melee_defenders = 0
        self.num_ranged_defenders = 0
        self.num_cavalry_defenders = 0
        self.next_battle_update = -1.0
        self.unit_widgets = []
        self.pending_kills = []
        self.attack_strength = 0.0
        self.defense_strength = 0.0

    def create_battle_layout(self, from_hex, to_hex):
        self.attack_hex = from_hex
        self.defend_hex = to_hex
        self.num_melee_attackers = 0
        self.num_ranged_attackers = 0
        self.num_cavalry_attackers = 0
        self.num_melee_defenders = 0
        self.num_ranged_defenders = 0
        self.num_cavalry_defenders = 0
        self.next_battle_update = -1.0
        self.unit_widgets = []
        self.pending_kills = []
        self.attack_strength = 0.0
        self.defense_strength = 0.0

        # display units involved in formation
        for unit in self.attack_hex.game_units:
            self.display_attacker(unit)
            self.attack_strength = self.attack_strength + 1.0
        self.defense_strength = self.defend_hex.calc_defense_strength()
        for unit in self.defend_hex.game_units:
            self.display_defender(unit)
        self.attack_label.text=f"Attack Strength: {self.attack_strength}"
        self.defense_label.text=f"Defense Strength: {self.defense_strength}"

    def display_attacker(self, unit):
        if ((self.num_melee_attackers < Globals.MAX_UNIT_STACK/2) and (unit.battle_role == 'Melee')) or (self.num_ranged_attackers >= Globals.MAX_UNIT_STACK/2):
            # put this unit in front line
            pos_x = 0.3
            pos_y = 0.7 - 0.2 * self.num_melee_attackers
            self.num_melee_attackers += 1
        else:
            # rear line unit
            pos_x = 0.15
            pos_y = 0.7 - 0.2 * self.num_ranged_attackers
            self.num_ranged_attackers += 1

        # print(f"display attacker {unit.name} at {pos_x} {pos_y}")
        scale = Constants.HEX_SIZE * 0.01
        unit_image = Image(source=unit.image_path, size_hint=(None, None), size=(64.0 * scale, 64.0 * scale), pos_hint={"x": pos_x, "y": pos_y})
        self.add_widget(unit_image)
        self.unit_widgets.append(unit_image)
        unit.battle_image = unit_image
        # 'Ranged':
        # 'Melee'
        # 'Cavalry'

    def display_defender(self, unit):
        if ((self.num_melee_defenders < Globals.MAX_UNIT_STACK/2) and (unit.battle_role == 'Melee')) or (self.num_ranged_defenders >= Globals.MAX_UNIT_STACK/2):
            # put this unit in front line
            pos_x = 0.6
            pos_y = 0.7 - 0.2 * self.num_melee_defenders
            self.num_melee_defenders += 1
        else:
            # rear line unit
            pos_x = 0.75
            pos_y = 0.7 - 0.2 * self.num_ranged_defenders
            self.num_ranged_defenders += 1
        scale = Constants.HEX_SIZE * 0.01
        unit_image = Image(source=unit.image_path, size_hint=(None, None), size=(64.0 * scale, 64.0 * scale), pos_hint={"x": pos_x, "y": pos_y})
        self.add_widget(unit_image)
        self.unit_widgets.append(unit_image)
        unit.battle_image = unit_image

    def clear_unit_images(self):
        for image in self.unit_widgets:
            if image.parent is not None:
                image.parent.remove_widget(image)
        self.unit_widgets.clear()
        for unit in self.attack_hex.game_units:
            unit.battle_image = None
        for unit in self.defend_hex.game_units:
            unit.battle_image = None

    def on_cancel_button_press(self, instance):
        self.game_screen.pending_attack = False
        self.parent.remove_widget(self)
        sound = pygame.mixer.Sound("content/sounds/Select.wav")
        sound.play()
        self.clear_unit_images()

    def update_battle(self, dt):
        if self.next_battle_update > 0.0:
            self.next_battle_update -= dt
            if self.next_battle_update <= 0.0:
                if len(self.pending_kills) > 0:
                    self.pending_kills[0].killed(self.game_screen.hex_map)
                    self.game_screen.hex_overlay.update_unit_info(self.game_screen.currently_selected_hex, self.game_screen.currently_selected_unit)
                    sound = pygame.mixer.Sound(self.pending_kills[0].select_sound)
                    sound.play()
                    self.pending_kills.pop(0)
                    self.next_battle_update = 1.0
                else:
                    self.end_battle()

    def resolve_battle(self):
        # determine results and make pending_kills list
        # self.game_screen.game_rules.initiate_attack(self.attack_hex, self.defend_hex, self.game_screen.hex_map)
        # temp, for each unit, roll die, odds of being destroyed is defend/attack for attacker, and attack/defend for defender
        battle_odds = self.defense_strength/(1.0 + self.attack_strength + self.defense_strength)
        remaining_attackers = len(self.attack_hex.game_units)
        for unit in self.attack_hex.game_units:
            unit.group_moves = 0
            unit.remaining_moves = 0
            if random.random() < battle_odds:
                remaining_attackers -= 1
                if random.random() < 0.5:
                    self.pending_kills.append(unit)
                else:
                    self.pending_kills.insert(0, unit)
        battle_odds = self.attack_strength/(1.0 + self.attack_strength + self.defense_strength)
        last_defender_slot = 1
        if remaining_attackers < 1:
            last_defender_slot = 2
        remaining_defenders = len(self.defend_hex.game_units)
        for unit in self.defend_hex.game_units:
            if random.random() < battle_odds:
                remaining_defenders -= 1
                if remaining_defenders == 0:
                    self.pending_kills.append(unit)
                else:
                    self.pending_kills.insert(random.randint(0, len(self.pending_kills) - last_defender_slot), unit)

    def on_attack_button_press(self, instance):
        sound = pygame.mixer.Sound("content/sounds/Battle_horn.wav")
        sound.play()
        self.next_battle_update = 1.0
        self.resolve_battle()

    def end_battle(self):
        self.game_screen.pending_attack = False
        self.parent.remove_widget(self)
        self.clear_unit_images()

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        self.border.rectangle = (self.x, self.y, self.width, self.height)

class OverlayLabel(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.color = (0, 0, 0, 1)
        self.size_hint = (0.8, 0.2)
        self.halign = "left"
        self.valign = "middle"
        self.font_size = dp(20)


class OverlayButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.color = (0, 0, 0, 1)
        self.halign = "left"
        self.valign = "middle"
        self.font_size = dp(20)


class BorderedLabel(BoxLayout):
    def __init__(self, label_text="", **kwargs):
        super().__init__(**kwargs)

        with self.canvas.before:
            # Set the color and draw the rectangle
            Color(1, 1, 1, 0.8)  # RGBA
            self.rect = Rectangle(size=self.size, pos=self.pos, line_width=1.5)

        # Update the rectangle size and position when the widget size or position changes
        self.bind(size=self.update_rect, pos=self.update_rect)

        self.label = Label(text=label_text, size_hint=(1, 1), font_size=dp(24), color = (0, 0, 0, 1))
        self.add_widget(self.label)

    def update_rect(self, *args):
        self.rect.size = self.size
        self.rect.pos = self.pos


class HexagonInfoOverlay(FloatLayout):
    def __init__(self, in_game_screen, **kwargs):
        super().__init__(**kwargs)

        self.game_screen = in_game_screen
        with self.canvas:
            # Translucent background
            Color(1, 1, 1, 0.8)  # White color with 80% opacity
            self.rect = Rectangle(size=self.size, pos=self.pos)
            # Border
            Color(0, 0, 0)
            self.border = Line(width=2, rectangle=(self.x, self.y, self.width, self.height))
        self.bind(pos=self.update_rect, size=self.update_rect)

        self.terrain_label = OverlayLabel(text="Grasslands", pos_hint={"x": -0.2, "y": 0.70})
        self.add_widget(self.terrain_label)

        self.structure_label = OverlayLabel(text="", pos_hint={"x": -0.2, "y": 0.55})
        self.add_widget(self.structure_label)

        self.defense_label = OverlayLabel(text="Defense Bonus: 0", pos_hint={"x": -0.2, "y": 0.25})
        self.add_widget(self.defense_label)

        self.gold_label = OverlayLabel(text="", pos_hint={"x": -0.2, "y": 0.10})
        self.add_widget(self.gold_label)

        self.construction_time_label = OverlayLabel(text="", pos_hint={"x": -0.2, "y": 0.10})
        self.add_widget(self.construction_time_label)

        scaling = 0.01 * Constants.HEX_SIZE
        self.terrain_image = Image(source='content/New_Grass_2.png', size_hint=(None, None), size=(64.0*scaling, 64.0*scaling), pos_hint={"x": 0.01, "y": 0.4})
        self.add_widget(self.terrain_image)

        self.structure_image = Image(source='', size_hint=(None, None), size=(64.0*scaling, 64.0*scaling), pos_hint={"x": 0.01, "y": 0.4})
        self.add_widget(self.structure_image)
        self.structure_image.opacity = 0.0

        self.unit_images = []
        self.unit_forts = []
        scaling = 0.01 * Constants.HEX_SIZE
        for index in range(Globals.MAX_UNIT_STACK):
            x,y = self.get_unit_image_position(index)
            img_button = Image(source='content/green_phalanx_low.png', size_hint=(None, None), size=(48*scaling, 48*scaling), pos_hint={"x": x, "y": y})
            fortify_img = Image(source='content/Fortify.png', size_hint=(None, None), size=(48*scaling, 24*scaling), pos_hint={"x": x, "y": y})
            self.unit_images.append(img_button)
            self.unit_forts.append(fortify_img)
            self.add_widget(img_button)
            self.add_widget(fortify_img)
            img_button.opacity = 0.0
            fortify_img.opacity = 0.0

        self.unit_label = OverlayLabel(text="", pos_hint={"x": 0.45, "y": 0.74}, bold=True, font_size=dp(30))
        self.add_widget(self.unit_label)

        self.movement_label = OverlayLabel(text="", pos_hint={"x": 0.45, "y": 0.54})
        self.add_widget(self.movement_label)

        self.combat_label = OverlayLabel(text="", pos_hint={"x": 0.45, "y": 0.37})
        self.add_widget(self.combat_label)

        self.level_label = OverlayLabel(text="", pos_hint={"x": 0.45, "y": 0.20})
        self.add_widget(self.level_label)

        self.fortified_label = OverlayLabel(text="Fortified", pos_hint={"x": 0.45, "y": 0.02})
        self.add_widget(self.fortified_label)

        self.road_label_shadow = Label(text="Select adjacent hex as road destination", color=(0, 0, 0, 1), size_hint=(1.0, 0.4), pos_hint={"x": 0.006, "y": 0.97}, halign="left", valign="middle", bold=True, font_size=dp(40))
        self.add_widget(self.road_label_shadow)

        self.road_label = Label(text="Select adjacent hex as road destination", color=(1, 1, 0, 1), size_hint=(1.0, 0.4), pos_hint={"x": 0.0, "y": 1.0}, halign="left", valign="middle", bold=True, font_size=dp(40))
        self.add_widget(self.road_label)
        self.road_label.opacity = 0.0
        self.road_label_shadow.opacity = 0.0

        self.ai_label = BorderedLabel(label_text="AI is thinking", size_hint=(0.3, 0.25), pos_hint={"x": 0.35, "y": 1.05})
        self.add_widget(self.ai_label)

        self.fortify_button = OverlayButton(text='FORTIFY', size_hint=(0.2, 0.32), pos_hint={"x": 0.0, "y": 1.0})
        self.fortify_button.bind(on_press=self.on_fortify_button_press)
        self.add_widget(self.fortify_button)

        self.move_button = OverlayButton(text='MOVE', size_hint=(0.2, 0.32), pos_hint={"x": 0.2, "y": 1.0})
        self.move_button.bind(on_press=self.on_move_button_press)
        self.add_widget(self.move_button)

        self.group_button = OverlayButton(text='GROUP', size_hint=(0.2, 0.32), pos_hint={"x": 0.4, "y": 1.0})
        self.group_button.bind(on_press=self.on_group_button_press)
        self.add_widget(self.group_button)

        self.recruit_button = OverlayButton(text='RECRUIT', size_hint=(0.2, 0.32), pos_hint={"x": 0.6, "y": 1.0})
        self.recruit_button.bind(on_press=self.on_recruit_button_press)
        self.add_widget(self.recruit_button)

        self.road_button = OverlayButton(text='BUILD\nROAD', size_hint=(0.2, 0.32), pos_hint={"x": 0.8, "y": 1.0})
        self.road_button.bind(on_press=self.on_road_button_press)
        self.add_widget(self.road_button)

        self.end_turn_button = OverlayButton(text='END TURN', size_hint=(0.2, 0.32), pos_hint={"x": 1.0, "y": 0.0})
        self.end_turn_button.bind(on_press=self.on_end_turn_button_press)
        self.add_widget(self.end_turn_button)

    def get_unit_image_position(self, index):
        row_length = int((1.0 + Globals.MAX_UNIT_STACK) * 0.5)
        x = 0.625 - 0.1 * (index % row_length)
        y = 0.52 - 0.495 * int(index / row_length)
        return x, y

    def on_end_turn_button_press(self, instance):
        if (Globals.CURRENT_TURN == Globals.LOCAL_PLAYER) and not Globals.EDIT_MODE:
            self.game_screen.pass_turn()

    # returns true if can build on this hex
    # if there is no structure already here, and selected unit that hasn't moved yet
    def can_build(self):
        if (not self.game_screen.build_road) and (self.game_screen.currently_selected_hex.structure is None) and self.game_screen.currently_selected_unit.is_ready():
            return True
        return False

    # returns true if can recruit on this hex
    # can only recruit in cities
    def can_recruit(self):
        recruit_hex = self.game_screen.currently_selected_hex
        return (not self.game_screen.build_road) and (recruit_hex.structure is not None) and recruit_hex.structure.recruitable_units and (len(recruit_hex.game_units) < Globals.MAX_UNIT_STACK)

    # returns true if selected unit can move
    def can_move(self):
        my_unit = self.game_screen.currently_selected_unit
        if my_unit is None:
            return False
        my_hex = self.game_screen.currently_selected_hex
        if (len(my_hex.game_units) > 1) and my_unit.is_grouped:
            # grouped, so determine if group can move
            group_can_move = True
            for unit in my_hex.game_units:
                if unit.remaining_moves < 1:
                    group_can_move = False
                    break
            return group_can_move
        return my_unit.remaining_moves > 0

    def cannot_interact(self):
        # can't interact if enemy hex or not current player's turn
        return self.is_enemy_hex(Globals.LOCAL_PLAYER) or (Globals.CURRENT_TURN != Globals.LOCAL_PLAYER) or Globals.EDIT_MODE

    def on_recruit_button_press(self, instance):
        if self.cannot_interact():
            return
        gold_count = self.game_screen.game_rules.player_gold[Globals.CURRENT_TURN]
        print(f"Current Gold: {gold_count}")
        if self.can_build():
            structure_types = self.game_screen.hex_map.structure_types
            popup = StructureMenuPopup(structure_types, self.game_screen, Globals.LOCAL_PLAYER, edit_mode=False, current_gold=gold_count,
                                           structure_pos_x=self.game_screen.scroll_view.last_touch_x,
                                           structure_pos_y=self.game_screen.scroll_view.last_touch_y)
            popup.open()
        elif self.can_recruit():
            unit_types = self.game_screen.currently_selected_hex.structure.recruitable_units
            popup = UnitMenuPopup(unit_types, self.game_screen, Globals.LOCAL_PLAYER, edit_mode=False, current_gold=gold_count,
                                  unit_pos_x=self.game_screen.scroll_view.last_touch_x,
                                  unit_pos_y=self.game_screen.scroll_view.last_touch_y)
            popup.open()
        sound = pygame.mixer.Sound("content/sounds/Select.wav")
        sound.play()

    def on_road_button_press(self, instance):
        if self.cannot_interact():
            return
        if self.game_screen.game_rules.can_build_road(self.game_screen.currently_selected_unit):
            self.game_screen.start_building_road(self.game_screen.currently_selected_unit)
        sound = pygame.mixer.Sound("content/sounds/Select.wav")
        sound.play()

    def on_group_button_press(self, instance):
        if self.game_screen.build_road or self.cannot_interact() or (len(self.game_screen.currently_selected_hex.game_units) < 2):
            return
        new_grouping = not self.game_screen.currently_selected_hex.game_units[0].is_grouped
        if new_grouping:
            self.group_button.text = 'UNGROUP'
        else:
            self.group_button.text = 'GROUP'
        for unit in self.game_screen.currently_selected_hex.game_units:
            unit.is_grouped = new_grouping
        self.update_buttons()
        sound = pygame.mixer.Sound("content/sounds/Select.wav")
        sound.play()

    def on_move_button_press(self, instance):
        if self.game_screen.build_road or self.cannot_interact():
            return
        self.game_screen.move_active = not self.game_screen.move_active
        self.update_buttons()
        sound = pygame.mixer.Sound("content/sounds/Select.wav")
        sound.play()

    def on_fortify_button_press(self, instance):
        # can only fortify or pillage if have full movement left
        if not self.game_screen.currently_selected_unit.is_ready():
            return
        current_unit = self.game_screen.currently_selected_unit
        if self.game_screen.build_road or self.cannot_interact():
            return
        self.fortify_button.opacity = 0.0
        sound = pygame.mixer.Sound("content/sounds/Select.wav")
        sound.play()

        # check if pillaging rather than fortifying
        if current_unit.pillage(self.game_screen.hex_map):
            print("PILLAGE")
            self.fortify_button.opacity = 0.0
            self.fortify_button.text = 'FORTIFY'
            self.update_hex(self.game_screen.currently_selected_hex, self.game_screen.currently_selected_unit)
            sound = pygame.mixer.Sound("content/sounds/Pillage_Farm.wav")
            sound.play()
            return

        if current_unit.fortify(True):
            self.update_unit_info(self.game_screen.currently_selected_hex, self.game_screen.currently_selected_unit)

        self.fortified_label.opacity = 1.0
        sound = pygame.mixer.Sound("content/sounds/Fortify.wav")
        sound.play()

    def is_enemy_hex(self, current_player):
        current_hex = self.game_screen.currently_selected_hex
        if current_hex is None:
            return True
        if len(current_hex.game_units) > 0:
            if current_hex.game_units[0].player_owner != current_player:
                return True
            else:
                return False
        if (current_hex.structure is not None) and (current_hex.structure.player_owner != current_player):
            return True
        return False

    def update_buttons(self):
        self.ai_label.opacity = 0.0
        self.recruit_button.opacity = 0.0
        self.group_button.opacity = 0.0
        self.move_button.opacity = 0.0
        self.road_button.opacity = 0.0
        self.end_turn_button.opacity = 0.0
        self.road_label.opacity = 0.0
        self.road_label_shadow.opacity = 0.0
        self.fortify_button.opacity = 0.0
        if not Globals.EDIT_MODE:
            if Globals.CURRENT_TURN == Globals.LOCAL_PLAYER:
                self.end_turn_button.opacity = 1.0
            else:
                self.ai_label.opacity = 1.0
        if self.cannot_interact():
            return
        if self.game_screen.build_road:
            self.road_label.opacity = 1.0
            self.road_label_shadow.opacity = 1.0
            return
        if self.can_recruit():
            self.recruit_button.opacity = 1.0
            self.recruit_button.text = 'RECRUIT'
        if self.game_screen.currently_selected_unit is not None:
            self.group_button.opacity = 1.0
            selected_unit = self.game_screen.currently_selected_unit
            # can only fortify or pillage if have full movement left
            if self.game_screen.currently_selected_unit.is_ready():
                structure = self.game_screen.currently_selected_hex.structure
                if (structure is None) or not structure.container_structure:
                    if (structure is not None) and (structure.player_owner != Globals.LOCAL_PLAYER):
                        self.fortify_button.opacity = 1.0
                        self.fortify_button.text = 'PILLAGE'
                    elif not self.game_screen.currently_selected_unit.is_fortified:
                        self.fortify_button.opacity = 1.0
                        self.fortify_button.text = 'FORTIFY'
            if selected_unit.is_grouped:
                self.group_button.text = 'UNGROUP'
            else:
                self.group_button.text = 'GROUP'
            if self.can_move():
                self.move_button.opacity = 1.0
                if self.game_screen.move_active:
                    self.move_button.text = 'CANCEL\nMOVE'
                else:
                    self.move_button.text = 'MOVE'
            if self.can_build():
                self.recruit_button.opacity = 1.0
                self.recruit_button.text = 'BUILD'
            elif self.game_screen.game_rules.can_build_road(self.game_screen.currently_selected_unit):
                self.road_button.opacity = 1.0

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        self.border.rectangle = (self.x, self.y, self.width, self.height)

    def handle_touch(self, touch):
        # handle touches of unit info icons
        for index in range(Globals.MAX_UNIT_STACK):
            if (self.unit_images[index].opacity > 0.0) and self.unit_images[index].collide_point(*touch.pos):
                self.game_screen.currently_selected_unit = self.game_screen.currently_selected_hex.game_units[index]
                self.update_unit_info(self.game_screen.currently_selected_hex, self.game_screen.currently_selected_unit)
                sound = pygame.mixer.Sound("content/sounds/Button_Click.wav")
                sound.play()
                return True
        # game should ignore touches inside the hex info box
        if (self.rect.pos[0] <= touch.x <= self.rect.pos[0] + self.rect.size[0] and
                self.rect.pos[1] <= touch.y <= self.rect.pos[1] + self.rect.size[1]):
            return True
        return False

    def update_unit_info(self, highlighted_hex, selected_unit):
        self.update_buttons()
        for index in range(Globals.MAX_UNIT_STACK):
            self.unit_images[index].opacity = 0.0
            self.unit_forts[index].opacity = 0.0
        self.unit_label.text = ""
        self.combat_label.text = ""
        self.movement_label.text = ""
        self.level_label.text = ""
        self.fortified_label.opacity = 0.0
        if ((highlighted_hex.fog_level[Globals.LOCAL_PLAYER] == 0) or ini.NO_FOG):
            index = 0
            for unit in highlighted_hex.game_units:
                self.unit_images[index].source = unit.image_path
                self.unit_images[index].opacity = 0.4
                if unit.is_fortified:
                    self.unit_forts[index].opacity = 0.6
                if unit is selected_unit:
                    self.unit_label.text = selected_unit.name
                    self.combat_label.text = f"Combat strength: {selected_unit.combat_strength}"
                    self.movement_label.text = f"Remaining moves: {selected_unit.remaining_moves}"
                    self.level_label.text = selected_unit.level
                    self.unit_images[index].opacity = 1.0
                    if unit.is_fortified:
                        self.fortified_label.opacity = 1.0
                        self.unit_forts[index].opacity = 1.0
                index += 1
                if index >= Globals.MAX_UNIT_STACK:
                    break

    def update_hex(self, highlighted_hex, selected_unit):
        self.structure_image.opacity = 0.0
        self.structure_label.text = ""
        if (highlighted_hex.fog_level[Globals.LOCAL_PLAYER] == 2) and not ini.NO_FOG:
            self.terrain_label.text = "Unexplored"
            self.terrain_image.opacity = 0.0
            self.defense_label.text = ""
            return

        if highlighted_hex.terrain_type is not None:
            self.terrain_label.text = highlighted_hex.terrain_type.name
            self.terrain_image.source = highlighted_hex.terrain_type.image_path
            defense_bonus = highlighted_hex.terrain_type.defense_bonus
        else:
            self.terrain_label.text = "None"
            self.terrain_image.source = 'content\\water.png'
            defense_bonus = 0.0
        self.terrain_image.opacity = 1.0
        if highlighted_hex.structure is not None:
            if highlighted_hex.structure.remaining_build_time >= 0:
                defense_bonus += highlighted_hex.structure.defense_bonus
        self.defense_label.text = f"Defense Bonus:  {int(100.0 * defense_bonus)}%"
        self.update_unit_info(highlighted_hex, selected_unit)
        if highlighted_hex.structure is not None:
            self.structure_image.source = highlighted_hex.structure.image_path
            if highlighted_hex.structure.remaining_build_time <= 0:
                self.structure_label.text = highlighted_hex.structure.name
                self.construction_time_label.text = ""
                self.gold_label.text = f"Gold per turn: {str(highlighted_hex.structure.gold_per_turn)}"
            else:
                self.structure_label.text = highlighted_hex.structure.name + "(Under Construction)"
                self.construction_time_label.text = f"{highlighted_hex.structure.remaining_build_time} turns remaining"
                self.gold_label.text = ""
            self.structure_image.opacity = 1.0


class GameInfoOverlay(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            # Translucent background
            Color(1, 1, 1, 0.8)  # White color with 80% opacity
            self.rect = Rectangle(size=self.size, pos=self.pos)
            # Border
            Color(0, 0, 0)
            self.border = Line(width=2, rectangle=(self.x, self.y, self.width, self.height))
        self.bind(pos=self.update_rect, size=self.update_rect)

        # Create labels and position them at the corners
        self.viewing_label = Label(text='PLAYER 1', size_hint=(None, None), size=(100, 50), pos_hint={'x': 0.1, 'y': 0.5},
                                      color=(0, 0, 0, 1), halign='left', valign='middle')
        self.viewing_label.text_size = self.viewing_label.size
        self.viewing_label.opacity = 0.0
        self.add_widget(self.viewing_label)

        self.year_label = Label(text='500 B.C.', size_hint=(None, None), size=(120, 50), pos_hint={'x': 0.1, 'top': 1.0}, font_size=dp(25),
                                           color=(0, 0, 0, 1), halign='left', valign='middle')
        self.year_label.text_size = self.year_label.size
        self.year_label.opacity = 1.0
        self.add_widget(self.year_label)

        self.gold_label = Label(text='0', size_hint=(None, None), size=(120, 50), pos_hint={'x': 0.5, 'y': 0.35}, bold=True, font_size=dp(30),
                                           color=(0.3, 0.3, 0.0, 1), halign='left', valign='middle')
        self.gold_label.text_size = self.gold_label.size

        self.gold_image = Image(source='content/Gold_Icon.png', size_hint=(0.5, 0.5), pos_hint={'x': 0.05, 'y': 0.2})
        self.add_widget(self.gold_label)
        self.add_widget(self.gold_image)

    def update(self, in_GameScreen):
        self.viewing_label.opacity = 0.0
        self.gold_label.text = f"{in_GameScreen.game_rules.player_gold[Globals.LOCAL_PLAYER]}"
        self.update_year()

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        self.border.rectangle = (self.x, self.y, self.width, self.height)

    def update_year(self):
        self.year_label.text = f"{Globals.DATE} B.C."


class EditorInfoOverlay(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            # Translucent background
            Color(1, 1, 1, 0.8)  # White color with 80% opacity
            self.rect = Rectangle(size=self.size, pos=self.pos)
            # Border
            Color(0, 0, 0)
            self.border = Line(width=2, rectangle=(self.x, self.y, self.width, self.height))
        self.bind(pos=self.update_rect, size=self.update_rect)

        # Create labels and position them at the corners
        self.viewing_label = Label(text='PLAYER 1', size_hint=(None, None), size=(100, 50), pos_hint={'x': 0.1, 'y': 0.83},
                                      color=(0, 0, 0, 1), halign='left', valign='middle')
        self.viewing_label.text_size = self.viewing_label.size
        self.viewing_label.opacity = 1.0
        self.add_widget(self.viewing_label)

        self.year_label = Label(text='EDITING', size_hint=(None, None), size=(120, 50), pos_hint={'x': 0.1, 'top': 1.0}, font_size=dp(25),
                                           color=(0, 0, 0, 1), halign='left', valign='middle')
        self.year_label.text_size = self.year_label.size
        self.year_label.opacity = 1.0
        self.add_widget(self.year_label)

        self.shortcuts_label = Label(text='', size_hint=(0.1, 0.5), pos_hint={'x': 0.5, 'top': 0.75},
                                           color=(0, 0, 0, 1), halign='left', valign='middle')
        self.add_widget(self.shortcuts_label)
        self.shortcuts_label.text += 'f:    Forest\n'
        self.shortcuts_label.text += 'g:    Grasslands\n'
        self.shortcuts_label.text += 'h:    Hills\n'
        self.shortcuts_label.text += 'm:    Mountains\n'
        self.shortcuts_label.text += 'w:    Water\n'
        self.shortcuts_label.text += 'p:    Add unit\n'
        self.shortcuts_label.text += 'c:    Add structure\n'
        self.shortcuts_label.text += 'r:    Add road\n'
        self.shortcuts_label.text += 'b:    Clear hex\n'
        self.shortcuts_label.text += '1-6:  Add river\n'
        self.shortcuts_label.text += 's:    Save\n'
        self.shortcuts_label.text += 'q:    Structure menu\n'
        self.shortcuts_label.text += 'o:    Unit menu\n'
        self.shortcuts_label.text += 'l:    Load map\n'
        self.shortcuts_label.text += '[ ]:  Change player\n'

    def update(self, in_GameScreen):
        self.update_year()

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        self.border.rectangle = (self.x, self.y, self.width, self.height)

    def update_year(self):
        self.viewing_label = f"Player {Globals.CURRENT_TURN}"
