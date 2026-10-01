# -*- coding: utf-8 -*-
from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen, SlideTransition

from db import save_user_profile, get_user_profile, calc_target
from helpers import (C_GREEN, C_RED, C_DARK_GREEN,
                     styled_btn, lbl, spacer, text_input,
                     section_lbl, scroll_layout, header_bar, radio_group)

ACTIVITIES = ["Sedentary", "Lightly Active", "Moderately Active", "Very Active"]
GOALS      = ["Lose Weight", "Maintain Weight", "Gain Muscle"]
DIETS      = ["No Restriction", "Vegetarian", "Vegan", "High Protein"]


class ProfileScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        outer = BoxLayout(orientation="vertical")
        outer.add_widget(header_bar("Your Profile", bg=C_DARK_GREEN))
        sv, layout = scroll_layout()

        layout.add_widget(section_lbl("Age"))
        self.age_i    = text_input("Age (years)")
        layout.add_widget(self.age_i)

        layout.add_widget(section_lbl("Weight (kg)"))
        self.weight_i = text_input("Weight in kg")
        layout.add_widget(self.weight_i)

        layout.add_widget(section_lbl("Height (cm)"))
        self.height_i = text_input("Height in cm")
        layout.add_widget(self.height_i)

        layout.add_widget(section_lbl("Gender"))
        g_box, self.get_gender = radio_group(["Male", "Female"], "Male", "gender")
        layout.add_widget(g_box)

        layout.add_widget(section_lbl("Activity Level"))
        a_box, self.get_activity = radio_group(ACTIVITIES, "Sedentary", "activity")
        layout.add_widget(a_box)

        layout.add_widget(section_lbl("Goal"))
        goal_box, self.get_goal = radio_group(GOALS, "Lose Weight", "goal")
        layout.add_widget(goal_box)

        layout.add_widget(section_lbl("Dietary Preference"))
        d_box, self.get_diet = radio_group(DIETS, "No Restriction", "diet")
        layout.add_widget(d_box)

        self.err_lbl = lbl("", color=C_RED, halign="center", h=dp(24))
        layout.add_widget(self.err_lbl)

        btn = styled_btn("Save & Continue", bg=C_GREEN, height=dp(50))
        btn.bind(on_release=lambda *_: self._save())
        layout.add_widget(btn)
        layout.add_widget(spacer(dp(20)))

        outer.add_widget(sv)
        self.add_widget(outer)

    def on_pre_enter(self):
        app = App.get_running_app()
        p   = getattr(app, "profile", {})
        if p.get("age"):
            self.age_i.text    = str(p["age"])
            self.weight_i.text = str(p["weight"])
            self.height_i.text = str(p["height"])

    def _save(self):
        try:
            age    = int(float(self.age_i.text))
            weight = float(self.weight_i.text)
            height = float(self.height_i.text)
        except ValueError:
            self.err_lbl.text = "Please enter valid Age, Weight and Height."
            return

        app = App.get_running_app()
        p = {
            "name":      app.user_name,
            "age":       age,
            "weight":    weight,
            "height":    height,
            "gender":    self.get_gender(),
            "activity":  self.get_activity(),
            "goal":      self.get_goal(),
            "diet_pref": self.get_diet(),
        }
        p["target"] = calc_target(p)
        save_user_profile(app.user_id, p)
        app.profile = get_user_profile(app.user_id)
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = "dashboard"
