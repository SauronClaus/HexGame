import json

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.app import App

import Globals
from menupopups import ImageMenuPopup, LoadScreenPopup, ObjectivesPopup




class TutorialScreen(Screen):
    def __init__(self, **kwargs):
        super(TutorialScreen, self).__init__(**kwargs)
        self.layout = FloatLayout()
        self.logo = Image(source='content\\logo.png', size_hint=(0.3, 0.3), pos_hint={'center_x': 0.5, 'center_y': 0.8})

        with open("tutorial_dialogue.json", 'r') as file:
            data = json.load(file)

        self.index = 0
        self.dialogue = data['dialogue']
        self.images = data['image']
        self.label = Label(text=f"{self.dialogue[self.index]}", size_hint=(None, None), size=(200, 50), halign='center',
                           valign='center',
                           pos_hint={'center_x': 0.5, 'center_y': 0.5}, font_size='20sp', text_size=(400, None))
        self.label.bind(size=self.label.setter('text_size'))  # Bind the size to the text size for proper wrapping

        self.next_button = Button(text='Next Page', size_hint=(None, None), size=(200, 50), halign='center', valign='center',
                                pos_hint={'center_x': 0.5, 'center_y': 0.3}, font_size='20sp')
        self.next_button.bind(on_release=self.button_interaction)

        self.close_button = Button(text='Close', size_hint=(None, None), size=(200, 50), halign='center', valign='center',
                                  pos_hint={'center_x': 0.9, 'center_y': 0.9}, font_size='20sp')
        self.close_button.bind(on_release=self.button_interaction)

        self.layout.add_widget(self.label)
        self.layout.add_widget(self.next_button)
        self.layout.add_widget(self.close_button)

        self.layout.add_widget(self.logo)
        self.add_widget(self.layout)


    def button_interaction(self, instance):
        if instance.text == "Next Page":
            if self.index < len(self.dialogue) - 1:
                self.index+=1
                self.label.text = self.dialogue[self.index]
                self.logo.source = f"content\\{self.images[self.index]}"
            if self.index >= len(self.dialogue) - 1:
                self.next_button.text = "Close"
        elif instance.text == "Close":
            print("Close button")
            game_screen = self.manager.get_screen('game')
            self.manager.current = 'game'
            objectives_popup = ObjectivesPopup(game_screen)
            objectives_popup.open()