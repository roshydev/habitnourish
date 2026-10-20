# -*- coding: utf-8 -*-
from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, SlideTransition

from db import save_user_profile, get_user_profile, calc_target
from helpers import (C_GREEN, C_RED, C_DARK_GREEN, C_GREY, C_TEXT,
                     styled_btn, lbl, spacer, text_input,
                     section_lbl, scroll_layout, header_bar, radio_group)

ACTIVITIES = ["Sedentary", "Lightly Active", "Moderately Active", "Very Active"]
GOALS      = ["Lose Weight", "Maintain Weight", "Gain Muscle"]
DIETS      = ["Vegetarian", "Non-Vegetarian"]
# UI label -> value stored in food_state (must match the CSV 'state' column)
STATES     = [("Kerala", "Kerala"), ("Tamil Nadu", "Tamil Nadu"),
              ("Andhra Pradesh", "Andhra"), ("Karnataka", "Karnataka")]


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
        for btn in g_box.children:
            btn.bind(state=lambda *_: self._check_changes())

        layout.add_widget(section_lbl("Activity Level"))
        a_box, self.get_activity = radio_group(ACTIVITIES, "Sedentary", "activity")
        layout.add_widget(a_box)
        for btn in a_box.children:
            btn.bind(state=lambda *_: self._check_changes())

        layout.add_widget(section_lbl("Goal"))
        goal_box, self.get_goal = radio_group(GOALS, "Lose Weight", "goal")
        layout.add_widget(goal_box)
        for btn in goal_box.children:
            btn.bind(state=lambda *_: self._check_changes())

        layout.add_widget(section_lbl("Dietary Preference"))
        d_box, self.get_diet = radio_group(DIETS, "Non-Vegetarian", "diet")
        layout.add_widget(d_box)
        for btn in d_box.children:
            btn.bind(state=lambda *_: self._check_changes())

        # ── Food from (multi-select states) ──────────────────────────────────
        layout.add_widget(section_lbl("Food from (select one or more)"))
        self.state_checks = {}   # state value -> CheckBox
        state_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(2))
        state_box.bind(minimum_height=state_box.setter("height"))
        for label, value in STATES:
            row = BoxLayout(orientation="horizontal", size_hint_y=None,
                            height=dp(40), spacing=dp(8))
            cb = CheckBox(size_hint=(None, 1), width=dp(34))
            cb.bind(active=lambda *_: self._check_changes())
            self.state_checks[value] = cb
            row.add_widget(cb)
            row.add_widget(Label(text=label, font_size=dp(13), color=C_TEXT,
                                 halign="left", valign="middle",
                                 size_hint_x=1, text_size=(dp(240), None)))
            state_box.add_widget(row)
        layout.add_widget(state_box)

        self.err_lbl = lbl("", color=C_RED, halign="center", h=dp(24))
        layout.add_widget(self.err_lbl)

        # Save & Continue button
        self.save_btn = styled_btn("Save & Continue", bg=C_GREEN, height=dp(50))
        self.save_btn.bind(on_release=lambda *_: self._save())
        self.save_btn.disabled = True
        layout.add_widget(self.save_btn)

        layout.add_widget(spacer(dp(20)))

        # Track text-field changes
        self.age_i.bind(text=self._check_changes)
        self.weight_i.bind(text=self._check_changes)
        self.height_i.bind(text=self._check_changes)

        outer.add_widget(sv)
        self.add_widget(outer)

    # ── Food-state helpers ─────────────────────────────────────────────────
    def _get_states(self):
        """Return selected states as a comma-separated string (value names)."""
        chosen = [v for v, cb in self.state_checks.items() if cb.active]
        return ",".join(chosen)

    def _set_states(self, food_state):
        """Tick the checkboxes matching a stored comma-separated food_state."""
        selected = {s.strip() for s in (food_state or "Kerala").split(",") if s.strip()}
        for value, cb in self.state_checks.items():
            cb.active = value in selected

    def on_pre_enter(self):
        app = App.get_running_app()
        p   = getattr(app, "profile", {})
        if p.get("age"):
            self.age_i.text    = str(p["age"])
            self.weight_i.text = str(p["weight"])
            self.height_i.text = str(p["height"])
        # Default to Kerala for new or upgrading users
        self._set_states(p.get("food_state") or "Kerala")

        self._original_values = {
            "age": self.age_i.text,
            "weight": self.weight_i.text,
            "height": self.height_i.text,
            "gender": self.get_gender(),
            "activity": self.get_activity(),
            "goal": self.get_goal(),
            "diet": self.get_diet(),
            "states": self._get_states(),
        }
        self.save_btn.disabled = True
        self.err_lbl.text = ""

    def _check_changes(self, *args):
        """Enable Save button only if there are changes in ANY field."""
        if not self._original_values:
            return
        current = {
            "age": self.age_i.text,
            "weight": self.weight_i.text,
            "height": self.height_i.text,
            "gender": self.get_gender(),
            "activity": self.get_activity(),
            "goal": self.get_goal(),
            "diet": self.get_diet(),
            "states": self._get_states(),
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

        states = self._get_states()
        if not states:
            self.err_lbl.text = "Please select at least one state under 'Food from'."
            return

        app = App.get_running_app()
        p = {
            "name":       app.user_name,
            "age":        age,
            "weight":     weight,
            "height":     height,
            "gender":     self.get_gender(),
            "activity":   self.get_activity(),
            "goal":       self.get_goal(),
            "diet_pref":  self.get_diet(),
            "food_state": states,
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
