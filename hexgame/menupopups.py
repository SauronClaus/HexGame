from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label

import os
import pygame

from kivy.uix.textinput import TextInput

import Globals


class ImageMenuPopup(Popup):
    def __init__(self, gamescreen, current_player=0, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.8, 0.6)  # Size of the popup
        self.auto_dismiss = True  # Allow clicking outside the popup to dismiss it
        self.title = 'Empty Menu'
        self.gamescreen = gamescreen
        self.current_player = current_player

    def exit_no_save(self, instance):
        sound = pygame.mixer.Sound('content/sounds/menu_select.wav')
        sound.play()
        self.gamescreen.menuMode = False
        self.dismiss()

    def on_dismiss(self):
        self.gamescreen.menuMode = False

    def open(self, *_args, **kwargs):
        super().open(*_args, **kwargs)
        sound = pygame.mixer.Sound('content/sounds/menu_select.wav')
        sound.play()


class StructureMenuPopup(ImageMenuPopup):
    def __init__(self, structure_types, gamescreen, current_player, edit_mode=True, current_gold=0, structure_pos_x=None, structure_pos_y=None, **kwargs):
        super().__init__(gamescreen, current_player=current_player, **kwargs)
        self.size_hint = (0.2 * min(len(structure_types), 4.0), 0.6)  # Size of the popup
        self.title = 'Select a Structure (ESC to exit)'
        self.gamescreen.menuMode = True
        grid = GridLayout(cols=len(structure_types))  # Adjust columns as needed
        self.structure_name_cost = {}
        self.current_gold = current_gold
        column_count = 0
        for structure_class in structure_types:
            structure_instance = structure_class(0, None)
            if structure_instance.in_build_menu:
                self.structure_name_cost[structure_instance.name] = structure_instance.cost
                # Create a layout for image and text
                layout = BoxLayout(orientation='vertical', padding=5, spacing=5)
                btn = Button(background_normal=structure_instance.image_path,
                             background_down=structure_instance.image_path,
                             size_hint=(1, 0.8))
                # Bind the button press to a method, passing the structure name
                btn.bind(on_release=lambda x, name=structure_instance.name: self.on_image_select(name, structure_pos_x, structure_pos_y))
                layout.add_widget(btn)
                # Add a label below the button
                label = Label(text=structure_instance.name, size_hint=(1, 0.2))
                cost = Label(text=f"{structure_instance.cost} gold", size_hint=(1, 0.2))
                if structure_instance.cost > self.current_gold and not Globals.EDIT_MODE:
                    cost.color = (1, 0, 0, 1)
                layout.add_widget(label)
                layout.add_widget(cost)
                grid.add_widget(layout)
                column_count += 1
        grid.cols = column_count
        self.content = grid

    def on_image_select(self, name, pos_x, pos_y):
        print(f'Selected Structure: {name}')  # Handle the structure selection
        structure_cost = self.structure_name_cost[name]
        if self.current_gold >= structure_cost or Globals.EDIT_MODE:
            print(f"Placing structure on called structure; {name}")
            if name != "Road":
                sound = pygame.mixer.Sound("content/sounds/Construction.wav")
                sound.play()
                self.gamescreen.place_structure(name)
            else:
                self.gamescreen.start_building_road(self.gamescreen.currently_selected_unit)
            self.dismiss()  # Dismiss the popup after selection
        else:
            sound = pygame.mixer.Sound("content/sounds/Click_Fail.wav")
            sound.play()
            print(f"{name} is too expensive! Costs {structure_cost} gold and you only have {self.current_gold}!")


class UnitMenuPopup(ImageMenuPopup):
    def __init__(self, unit_types, gamescreen, current_player, edit_mode=True, current_gold=0, unit_pos_x=None, unit_pos_y=None, **kwargs):
        super().__init__(gamescreen, current_player=current_player, **kwargs)
        self.size_hint = (0.2 * min(len(unit_types), 4.0), 0.6)  # Size of the popup
        self.gamescreen.menuMode = True
        self.title = 'Select a Unit (ESC to exit)'
        grid = GridLayout(cols=4)  # Adjust columns as needed
        self.unit_type_dict = {}
        self.current_gold = current_gold
        for unit in unit_types:
            instance = unit(0, None)
            self.unit_type_dict[instance.name] = unit
            layout = self.create_layout(instance.image_path, instance.name, instance.cost, unit_pos_x, unit_pos_y)
            grid.add_widget(layout)

        self.content = grid

    def create_layout(self, image_path, in_name, unit_cost, unit_pos_x, unit_pos_y):
        # Create a layout for image and text
        layout = BoxLayout(orientation='vertical', padding=5, spacing=5)
        btn = Button(background_normal=image_path,
                     background_down=image_path,
                     size_hint=(1, 0.8))
        # Bind the button press to a method, passing the structure name
        btn.bind(on_release=lambda x, name=in_name: self.on_image_select(name, unit_cost, unit_pos_x, unit_pos_y))
        layout.add_widget(btn)
        # Add a label below the button
        label = Label(text=in_name, size_hint=(1, 0.2))
        cost = Label(text=f"{unit_cost} gold", size_hint=(1, 0.2))
        if unit_cost > self.current_gold and not Globals.EDIT_MODE:
            cost.color = (1, 0, 0, 1)
        layout.add_widget(label)
        layout.add_widget(cost)
        return layout

    def on_image_select(self, name, unit_cost, pos_x, pos_y):
        print(f'Selected Unit: {name}')  # Handle the structure selection
        unit = self.unit_type_dict[name]
        if self.current_gold >= unit_cost or Globals.EDIT_MODE:
            self.gamescreen.place_unit(unit)
            self.dismiss()  # Dismiss the popup after selection
        else:
            sound = pygame.mixer.Sound("content/sounds/Click_Fail.wav")
            sound.play()
            print(f"{name} is too expensive! Costs {unit_cost} gold and you only have {self.current_gold}!")


class LoadScreenPopup(ImageMenuPopup):
    def __init__(self, gamescreen, **kwargs):
        super().__init__(gamescreen, **kwargs)
        self.gamescreen.menuMode = True
        self.title = 'Load Saved Maps'

        saved_maps = []
        directory = "Maps"
        number_maps = 1

        for filename in os.listdir(directory):
            path = os.path.join(directory, filename)
            if os.path.isfile(path):
                print(f"File: {filename[:len(filename) - 5:]}!")
                saved_maps.append(filename[:len(filename) - 5:])
                number_maps += 1

        saved_maps.append("New Small Map")
        saved_maps.append("New Medium Map")
        saved_maps.append("New Large Map")
        saved_maps.append("New Huge Map")

        # Small: 20x20
        # Medium: 50x50
        # Large: 70x70
        # Huge: 100x100

        grid = GridLayout(cols=number_maps, row_force_default=True, row_default_height=40)  # Adjust columns as needed
        for savedMap in saved_maps:
            # Create a layout for image and text
            layout = BoxLayout(orientation='vertical', padding=5, spacing=5)
            btn = Button(text=savedMap, width=100, size_hint_x=None)
            # Bind the button press to a method, passing the structure name
            btn.bind(on_release=lambda x, name=savedMap: self.on_image_select(name))
            layout.add_widget(btn)
            grid.add_widget(layout)

        self.content = grid
        print("Finished loading loadscreen!")

    def on_image_select(self, map_name):
        print(f'Selected Map: {map_name}')  # Handle the structure selection
        self.gamescreen.menuMode = False
        self.dismiss()  # Dismiss the popup after selection

        map_sizes = [[20, 20], [50, 50], [70, 70], [100, 100]]
        if map_name == "New Small Map":
            print("Selected a blank map. {Small}")
            self.gamescreen.current_map = ""
            self.gamescreen.hex_map.generate_map(map_sizes[0][0], map_sizes[0][1])
        elif map_name == "New Medium Map":
            print("Selected a blank map. {Medium}")
            self.gamescreen.current_map = ""
            self.gamescreen.hex_map.generate_map(map_sizes[1][0], map_sizes[1][1])
        elif map_name == "New Large Map":
            print("Selected a blank map. {Large}")
            self.gamescreen.current_map = ""
            self.gamescreen.hex_map.generate_map(map_sizes[2][0], map_sizes[2][1])
        elif map_name == "New Huge Map":
            print("Selected a blank map. {Huge}")
            self.gamescreen.current_map = ""
            self.gamescreen.hex_map.generate_map(map_sizes[3][0], map_sizes[3][1])
        else:
            self.gamescreen.load_map(map_name)
            self.gamescreen.current_map = map_name
        self.gamescreen.init_selected()

    def on_dismiss(self):
        print(f"Popup {self} dismissed!")
        self.gamescreen.menu_mode = False


class WaitScreenPopup(ImageMenuPopup):
    def __init__(self, gamescreen, **kwargs):
        super().__init__(gamescreen, **kwargs)
        self.title = 'Waiting for Server Response'
        self.gamescreen.menuMode = True
        self.size_hint = (None, None)
        self.size = (400, 200)

        layout = BoxLayout(orientation='vertical')
        wait_button = Button(text='Wait', size_hint=(1, 0.5))
        wait_button.bind(on_press=self.on_wait_button_press)

        layout.add_widget(wait_button)
        self.add_widget(layout)

    def on_wait_button_press(self, instance):
        # Do nothing on button press
        pass

    def on_dismiss(self):
        self.gamescreen.menuMode = False
        print(f"Waitscreen {self} dismissed!")


class SaveMenuPopup(ImageMenuPopup):
    def __init__(self, gamescreen, **kwargs):
        super().__init__(gamescreen, **kwargs)
        self.gamescreen = gamescreen
        self.gamescreen.menuMode = True
        print("Creating SaveMenuPopup...")
        self.title = "Save Map"
        content = BoxLayout(orientation='vertical', spacing=5, padding=10)

        text_input = TextInput(text=gamescreen.current_map, hint_text='Enter Your Map\'s Name', height=40)
        content.add_widget(text_input)

        save_button = Button(text='Save', size_hint=(1, 0.2))
        save_button.bind(on_release=self.close_popup)
        close_button = Button(text='Close without Saving', size_hint=(1, 0.2))
        close_button.bind(on_release=self.exit_no_save)

        content.add_widget(close_button)
        content.add_widget(save_button)
        self.content = content
        self.auto_dismiss = False

    def close_popup(self, instance):
        # Access the TextInput text or process it before closing
        print(self.content.children)
        entered_text = self.content.children[2].text
        print(f"Entered Text: {entered_text}")
        self.gamescreen.save_map(entered_text)
        self.gamescreen.menuMode = False

        self.dismiss()


class PauseMenuPopup(ImageMenuPopup):
    def __init__(self, gamescreen, **kwargs):
        super().__init__(gamescreen, **kwargs)
        self.gamescreen = gamescreen
        self.gamescreen.menuMode = True
        print("Creating PauseMenuPopup...")

        # Set size of the Popup
        self.size_hint = (None, None)
        self.size = (400, 300)

        # Create a custom title widget
        self.title = ""
        custom_title = Label(text="Pause Menu", font_size='20sp', size_hint=(1, None), height=50, halign='center', valign='middle')
        custom_title.bind(size=custom_title.setter('text_size'))

        content = BoxLayout(orientation='vertical', spacing=5, padding=10, size_hint=(None, None), size=(350, 250))

        save_popup = SaveMenuPopup(self.gamescreen)
        print(f"{save_popup}")
        save_button = Button(text='Save', size_hint=(None, None), size=(200, 50), pos_hint={'center_x': 0.5})
        save_button.bind(on_release=save_popup.open)

        close_button = Button(text='Back to Game', size_hint=(None, None), size=(200, 50), pos_hint={'center_x': 0.5})
        close_button.bind(on_release=self.exit_no_save)

        load_popup = LoadScreenPopup(self.gamescreen)
        load_button = Button(text='Load Scenario', size_hint=(None, None), size=(200, 50), pos_hint={'center_x': 0.5})
        load_button.bind(on_release=load_popup.open)

        exit_button = Button(text='Quit Game', size_hint=(None, None), size=(200, 50), pos_hint={'center_x': 0.5})
        exit_button.bind(on_release=self.quit_game)

        content.add_widget(close_button)
        content.add_widget(save_button)
        content.add_widget(load_button)
        content.add_widget(exit_button)

        # Add the custom title and content to the popup
        popup_layout = BoxLayout(orientation='vertical')
        popup_layout.add_widget(custom_title)
        popup_layout.add_widget(content)

        self.content = popup_layout
        self.auto_dismiss = False

    def close_popup(self, instance):
        # Access the TextInput text or process it before closing
        print(self.content.children)
        entered_text = self.content.children[2].text
        print(f"Entered Text: {entered_text}")
        self.gamescreen.save_map(entered_text)
        self.gamescreen.menuMode = False

        self.dismiss()

    def quit_game(self, instance):
        sound = pygame.mixer.Sound('content/sounds/menu_select.wav')
        sound.play()
        parent_app = self.gamescreen.find_parent_app()
        print("Quitting...")
        parent_app.stop()


class ObjectivesPopup(ImageMenuPopup):
    def __init__(self, gamescreen, **kwargs):
        super().__init__(gamescreen, **kwargs)
        self.gamescreen = gamescreen
        self.gamescreen.menuMode = True
        print("Creating Objectives...")

        objectives_text = "Objective:\n\n- Take Two Cities!"
        self.title = "Objectives"
        self.size_hint = (0.25, 0.6)
        self.content = FloatLayout()

        self.label = Label(text=objectives_text, size_hint=(None, None), size=(200, 50), halign='center', valign='center',
                           pos_hint={'center_x': 0.5, 'center_y': 0.8}, font_size='20sp')
        self.label.bind(size=self.label.setter('text_size'))  # Bind the size to the text size for proper wrapping

        self.ok_button = Button(text='Close', size_hint=(None, None), size=(200, 50), halign='center', valign='center', pos_hint={'center_x': 0.5, 'center_y': 0.3}, font_size='20sp')
        self.ok_button.bind(on_release=self.dismiss)

        self.content.add_widget(self.label)
        self.content.add_widget(self.ok_button)

    def close_popup(self, instance):
        self.dismiss()
