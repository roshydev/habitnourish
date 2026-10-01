# Quick probe - test all widget constructions used in main.py
import os
os.environ['KIVY_NO_CONSOLELOG'] = '1'

from kivy.core.window import Window
Window.size = (390, 844)

from kivymd.app import MDApp
from kivymd.uix.textfield import MDTextField
from kivymd.uix.card import MDCard
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.button import MDButton, MDButtonText, MDIconButton
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.metrics import dp

class TestApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Green"
        self.theme_cls.theme_style = "Light"

        # Test MDTextField without icon (plain)
        tf = MDTextField(hint_text="Full Name", mode="outlined",
                         size_hint_y=None, height=dp(56))
        print("MDTextField OK")

        # Test MDButton with MDButtonText child
        btn = MDButton(
            MDButtonText(text="Test", theme_text_color="Custom", text_color=(1,1,1,1)),
            style="filled",
            theme_bg_color="Custom",
            md_bg_color=[0.3,0.7,0.3,1],
            size_hint=(None,None), size=(dp(160), dp(48))
        )
        print("MDButton OK")

        # Test MDCard
        card = MDCard(padding=dp(10), radius=[dp(10)],
                      size_hint_y=None, height=dp(80), elevation=1)
        print("MDCard OK")

        # Test MDCheckbox
        cb = MDCheckbox(group="test", size_hint=(None,None), size=(dp(48),dp(48)))
        print("MDCheckbox OK")

        # Test MDIconButton
        ib = MDIconButton(icon="arrow-left")
        print("MDIconButton OK")

        print("\nAll widget probes PASSED")
        return MDBoxLayout()

TestApp().run()
