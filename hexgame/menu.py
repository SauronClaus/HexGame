from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.app import App

import pygame
import Globals
import ini
from menupopups import ImageMenuPopup, LoadScreenPopup, ObjectivesPopup


class MenuScreen(Screen):
    def __init__(self, **kwargs):
        super(MenuScreen, self).__init__(**kwargs)
        self.layout = FloatLayout()
        self.logo = Image(source='content\\logo.png', size_hint=(0.3, 0.3), pos_hint={'center_x': 0.5, 'center_y': 0.8})

        self.new_game_button = Button(text='New Game', font_size=32, size_hint=(0.3, 0.1), pos_hint={'center_x': 0.5, 'center_y': 0.62})
        self.new_game_button.bind(on_press=self.start_new_game)

        self.load_game_button = Button(text='Load Game', font_size=32, size_hint=(0.3, 0.1), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.load_game_button.bind(on_press=self.load_game)

        self.credits_menu = CreditsPopup()
        self.credit_button = Button(text='Credits', font_size=32, size_hint=(0.3, 0.1), pos_hint={'center_x': 0.5, 'center_y': 0.38})
        self.credit_button.bind(on_release=self.credits_menu.open)

        self.editor_button = Button(text='Edit', font_size=32, size_hint=(0.3, 0.1), pos_hint={'center_x': 0.5, 'center_y': 0.27})
        self.editor_button.bind(on_release=self.start_edit_mode)

        self.exit_button = Button(text='Exit Game', font_size=32, size_hint=(0.3, 0.1), pos_hint={'center_x': 0.5, 'center_y': 0.16})
        self.exit_button.bind(on_release=self.quit_game)

        self.layout.add_widget(self.new_game_button)
        self.layout.add_widget(self.load_game_button)

        self.layout.add_widget(self.editor_button)
        self.layout.add_widget(self.exit_button)
        self.layout.add_widget(self.credit_button)

        self.layout.add_widget(self.logo)
        self.add_widget(self.layout)

    def play_select_sound(self):
        sound = pygame.mixer.Sound('content/sounds/menu_select.wav')
        sound.play()

    def start_new_game(self, instance):
        self.play_select_sound()
        if ini.TUTORIAL_ACTIVE is False:
            game_screen = self.manager.get_screen('game')
            self.manager.current = 'game'
            objectives_popup = ObjectivesPopup(game_screen)
            objectives_popup.open()
        else:
            self.manager.current = 'tutorial'

    def load_game(self, instance):
        self.play_select_sound()
        game_screen = self.manager.get_screen('game')
        self.manager.current = 'game'
        load_popup = LoadScreenPopup(game_screen)
        load_popup.open()

    def start_edit_mode(self, instance):
        self.play_select_sound()
        game_screen = self.manager.get_screen('game')
        game_screen.toggle_edit_mode()
        Globals.EDIT_ALLOWED = True
        print(f"Starting edit mode... {Globals.EDIT_MODE}/{Globals.EDIT_ALLOWED}")
        load_screen_popup = LoadScreenPopup(game_screen)
        load_screen_popup.open()
        self.manager.current = 'game'

    def quit_game(self, instance):
        self.play_select_sound()
        App.get_running_app().stop()

    def hello(self, instance):
        print("Hiiiiiiiiii!")
        print(f"{self.credits_menu}")


class CreditsPopup(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.8, 0.8)  # Size of the popup
        self.auto_dismiss = True  # Allow clicking outside the popup to dismiss it
        self.title = 'Credits'

        content = FloatLayout()

        self.image = Image(source='content/BronzeDiceLogo.png', size_hint=(1, 1), pos_hint={"x": 0.00, "y": 0.4})
        self.label_prog = Label(
            text='Programming',
            color=(1, 1, 1, 1),
            pos_hint = {"x": 0.00, "y": 0.0},
            size_hint=(1, 1),
            halign='left',
            valign='top',
            font_size='40sp',
            bold=True
        )
        self.label_prog_list = Label(
            text='Steve Polge\nSebastian Polge',
            color=(0.9, 0.9, 0.5, 1),
            pos_hint = {"x": 0.00, "y": -0.1},
            size_hint=(1, 1),
            halign='left',
            valign='top',
            font_size='35sp'
        )
        self.label_QA = Label(
            text='Quality Assurance',
            color=(1, 1, 1, 1),
            pos_hint = {"x": 0.00, "y": -0.22},
            size_hint=(1, 1),
            halign='left',
            valign='top',
            font_size='40sp',
            bold=True
        )
        self.label_QA_list = Label(
            text='Nico Polge',
            color=(0.9, 0.9, 0.5, 1),
            pos_hint = {"x": 0.00, "y": -0.3},
            size_hint=(1, 1),
            halign='left',
            valign='top',
            font_size='35sp'
        )
        content.add_widget(self.label_prog)
        content.add_widget(self.label_prog_list)
        content.add_widget(self.label_QA)
        content.add_widget(self.label_QA_list)
        content.add_widget(self.image)

        # Add the custom title and content to the popup
        # popup_layout = BoxLayout(orientation='vertical')
        # popup_layout.add_widget(content)

        self.content = content
        self.auto_dismiss = False

    def on_dismiss(self):
        self.play_select_sound()
        print(f"Popup {self} dismissed!")

    def hello(self):
        print("Hi!")
