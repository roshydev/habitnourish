# -*- coding: utf-8 -*-
from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen, SlideTransition

from db import save_user_profile, get_user_profile, calc_target
from helpers import (C_GREEN, C_RED, C_DARK_GREEN, C_GREY,
                     styled_btn, lbl, spacer, text_input,
                     section_lbl, scroll_layout, header_bar, radio_group)

ACTIVITIES = ["Sedentary", "Lightly Active", "Moderately Active", "Very Active"]
GOALS      = ["Lose Weight", "Maintain Weight", "Gain Muscle"]
DIETS      = ["No Restriction", "Vegetarian", "Vegan", "High Protein"]


class ProfileScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._original_values = {}
        outer = BoxLayout(orientation="vertical")
        outer.add_widget(header_bar("Your Profile", back_cb=self._back, bg=C_DARK_GREEN))
        sv, layout = scroll_layout()

        # Edit Targets button — top of screen
        targets_btn = styled_btn("Edit Targets", bg=C_DARK_GREEN, height=dp(50))
        targets_btn.bind(on_release=lambda *_: self._go("edit_targets"))
        layout.add_widget(targets_btn)
        layout.add_widget(spacer(dp(8)))

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
        # Bind gender radio buttons to change detection
        for btn in g_box.children:
            btn.bind(state=lambda *_: self._check_changes())

        layout.add_widget(section_lbl("Activity Level"))
        a_box, self.get_activity = radio_group(ACTIVITIES, "Sedentary", "activity")
        layout.add_widget(a_box)
        # Bind activity radio buttons to change detection
        for btn in a_box.children:
            btn.bind(state=lambda *_: self._check_changes())

        layout.add_widget(section_lbl("Goal"))
        goal_box, self.get_goal = radio_group(GOALS, "Lose Weight", "goal")
        layout.add_widget(goal_box)
        # Bind goal radio buttons to change detection
        for btn in goal_box.children:
            btn.bind(state=lambda *_: self._check_changes())

        layout.add_widget(section_lbl("Dietary Preference"))
        d_box, self.get_diet = radio_group(DIETS, "No Restriction", "diet")
        layout.add_widget(d_box)
        # Bind dietary preference radio buttons to change detection
        for btn in d_box.children:
            btn.bind(state=lambda *_: self._check_changes())

        self.err_lbl = lbl("", color=C_RED, halign="center", h=dp(24))
        layout.add_widget(self.err_lbl)

        # Save & Continue button (only one)
        self.save_btn = styled_btn("Save & Continue", bg=C_GREEN, height=dp(50))
        self.save_btn.bind(on_release=lambda *_: self._save())
        self.save_btn.disabled = True
        layout.add_widget(self.save_btn)

        layout.add_widget(spacer(dp(20)))

        # Store initial state to track changes
        self.age_i.bind(text=self._check_changes)
        self.weight_i.bind(text=self._check_changes)
        self.height_i.bind(text=self._check_changes)
        # Radio buttons don't have a simple text bind, so we'll track in on_pre_enter

        outer.add_widget(sv)
        self.add_widget(outer)

    def on_pre_enter(self):
        app = App.get_running_app()
        p   = getattr(app, "profile", {})
        if p.get("age"):
            self.age_i.text    = str(p["age"])
            self.weight_i.text = str(p["weight"])
            self.height_i.text = str(p["height"])
        # Store original values to detect changes (all fields)
        self._original_values = {
            "age": self.age_i.text,
            "weight": self.weight_i.text,
            "height": self.height_i.text,
            "gender": self.get_gender(),
            "activity": self.get_activity(),
            "goal": self.get_goal(),
            "diet": self.get_diet(),
        }
        self.save_btn.disabled = True
        self.err_lbl.text = ""

    def _check_changes(self, *args):
        """Enable Save button only if there are changes in ANY field."""
        current = {
            "age": self.age_i.text,
            "weight": self.weight_i.text,
            "height": self.height_i.text,
            "gender": self.get_gender(),
            "activity": self.get_activity(),
            "goal": self.get_goal(),
            "diet": self.get_diet(),
        }
        has_changes = any(current[k] != self._original_values.get(k, "") for k in current)
        self.save_btn.disabled = not has_changes

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

    def _back(self):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "dashboard"

    def _go(self, screen):
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = screen
