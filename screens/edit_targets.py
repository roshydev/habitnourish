# -*- coding: utf-8 -*-
from kivy.app import App
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, SlideTransition
from kivy.uix.textinput import TextInput

from db import get_user_targets, save_user_targets
from helpers import (C_GREEN, C_DARK_GREEN, C_BLUE, C_RED, C_GREY, C_TEXT, C_WHITE,
                     styled_btn, lbl, spacer, card_box,
                     scroll_layout, header_bar)


class EditTargetsScreen(Screen):
    def on_pre_enter(self):
        self.clear_widgets()
        app = App.get_running_app()
        uid = app.user_id
        targets = get_user_targets(uid)

        outer = BoxLayout(orientation="vertical")

        # Custom header with "Back" button (instead of "Home")
        header = BoxLayout(orientation="horizontal", size_hint_y=None,
                          height=dp(56), padding=dp(8), spacing=dp(6))
        with header.canvas.before:
            Color(*C_DARK_GREEN)
            header._rect = Rectangle(pos=header.pos, size=header.size)
        header.bind(pos=lambda o, v: setattr(o._rect, "pos", v),
                   size=lambda o, v: setattr(o._rect, "size", v))
        
        back_btn = styled_btn("Back", bg=C_GREY,
                              height=dp(38), width=dp(68), font_size=dp(11))
        back_btn.bind(on_release=lambda *_: self._back())
        header.add_widget(back_btn)
        
        header.add_widget(Label(text="Edit Targets", color=C_WHITE, 
                               font_size=dp(15), bold=True, 
                               halign="left", valign="middle"))
        outer.add_widget(header)

        sv, layout = scroll_layout()

        layout.add_widget(lbl("Customize your daily targets",
                               size=dp(12), color=C_GREY, h=dp(24)))
        layout.add_widget(spacer(dp(8)))

        # Store inputs for later save
        self.target_inputs = {}
        
        # Store original values to detect changes
        self._original_targets = dict(targets)

        # Nutrition targets
        layout.add_widget(lbl("Nutrition Targets", bold=True,
                               size=dp(13), color=C_DARK_GREEN, h=dp(28)))

        nutrition_targets = [
            ("calories", "Calories", "kcal"),
            ("protein", "Protein", "g"),
            ("carbs", "Carbs", "g"),
            ("fat", "Fat", "g"),
            ("fiber", "Fiber", "g"),
            ("sugar", "Sugar", "g"),
        ]

        for key, label, unit in nutrition_targets:
            card = card_box(height=dp(60))
            
            left = BoxLayout(orientation="vertical", size_hint=(0.5, 1))
            left.add_widget(lbl(label, size=dp(12), bold=True, h=dp(20)))
            left.add_widget(lbl(f"Current: {int(targets[key])} {unit}",
                                size=dp(10), color=C_GREY, h=dp(18)))
            card.add_widget(left)

            # Input field
            ti = TextInput(text=str(int(targets[key])),
                           multiline=False,
                           input_filter="int",
                           size_hint=(0.5, None),
                           height=dp(44),
                           font_size=dp(12),
                           padding=(dp(8), dp(8)))
            ti.bind(text=lambda *_: self._check_changes())
            self.target_inputs[key] = ti
            card.add_widget(ti)
            layout.add_widget(card)

        layout.add_widget(spacer(dp(12)))

        # Lifestyle targets
        layout.add_widget(lbl("Lifestyle Targets", bold=True,
                               size=dp(13), color=C_DARK_GREEN, h=dp(28)))

        lifestyle_targets = [
            ("sleep_hours", "Sleep", "hours"),
            ("exercise_min", "Exercise", "minutes"),
            ("water_liters", "Water", "liters"),
            ("stress_level", "Stress Level", "1-10 scale"),
        ]

        for key, label, unit in lifestyle_targets:
            card = card_box(height=dp(60))

            left = BoxLayout(orientation="vertical", size_hint=(0.5, 1))
            left.add_widget(lbl(label, size=dp(12), bold=True, h=dp(20)))
            current_val = targets[key]
            display_val = f"{current_val:.1f}" if isinstance(current_val, float) else str(current_val)
            left.add_widget(lbl(f"Current: {display_val} {unit}",
                                size=dp(10), color=C_GREY, h=dp(18)))
            card.add_widget(left)

            # Input field
            ti = TextInput(text=display_val,
                           multiline=False,
                           input_filter="float" if key != "stress_level" else "int",
                           size_hint=(0.5, None),
                           height=dp(44),
                           font_size=dp(12),
                           padding=(dp(8), dp(8)))
            ti.bind(text=lambda *_: self._check_changes())
            self.target_inputs[key] = ti
            card.add_widget(ti)
            layout.add_widget(card)

        layout.add_widget(spacer(dp(12)))

        # Save and Cancel buttons
        btn_row = BoxLayout(orientation="horizontal", size_hint_y=None,
                             height=dp(48), spacing=dp(6))

        self.save_btn = styled_btn("Save Changes", bg=C_GREEN, height=dp(44))
        self.save_btn.bind(on_release=lambda *_: self._save_targets())
        self.save_btn.disabled = True
        btn_row.add_widget(self.save_btn)

        cancel_btn = styled_btn("Cancel", bg=C_GREY, height=dp(44))
        cancel_btn.bind(on_release=lambda *_: self._back())
        btn_row.add_widget(cancel_btn)

        layout.add_widget(btn_row)
        layout.add_widget(spacer(dp(20)))

        outer.add_widget(sv)
        self.add_widget(outer)

    def _check_changes(self, *args):
        """Enable Save button only if there are changes."""
        try:
            current = {
                "calories": int(self.target_inputs["calories"].text or 2000),
                "protein": float(self.target_inputs["protein"].text or 50),
                "carbs": float(self.target_inputs["carbs"].text or 260),
                "fat": float(self.target_inputs["fat"].text or 70),
                "fiber": float(self.target_inputs["fiber"].text or 25),
                "sugar": float(self.target_inputs["sugar"].text or 50),
                "sleep_hours": float(self.target_inputs["sleep_hours"].text or 8),
                "exercise_min": int(self.target_inputs["exercise_min"].text or 30),
                "water_liters": float(self.target_inputs["water_liters"].text or 2.5),
                "stress_level": int(self.target_inputs["stress_level"].text or 5),
            }
            
            # Check if any value changed
            has_changes = any(current[k] != self._original_targets.get(k, current[k]) for k in current)
            self.save_btn.disabled = not has_changes
        except ValueError:
            # If input is invalid, disable save
            self.save_btn.disabled = True

    def _save_targets(self):
        """Save updated targets to database."""
        app = App.get_running_app()
        uid = app.user_id

        try:
            new_targets = {
                "calories": int(self.target_inputs["calories"].text or 2000),
                "protein": float(self.target_inputs["protein"].text or 50),
                "carbs": float(self.target_inputs["carbs"].text or 260),
                "fat": float(self.target_inputs["fat"].text or 70),
                "fiber": float(self.target_inputs["fiber"].text or 25),
                "sugar": float(self.target_inputs["sugar"].text or 50),
                "sleep_hours": float(self.target_inputs["sleep_hours"].text or 8),
                "exercise_min": int(self.target_inputs["exercise_min"].text or 30),
                "water_liters": float(self.target_inputs["water_liters"].text or 2.5),
                "stress_level": int(self.target_inputs["stress_level"].text or 5),
            }

            save_user_targets(uid, new_targets)
            self._back()

        except ValueError:
            # Show error if input is invalid
            pass

    def _back(self):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "profile"
