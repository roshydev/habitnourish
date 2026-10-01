# -*- coding: utf-8 -*-
from datetime import date, datetime

from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen, SlideTransition
from kivy.uix.textinput import TextInput

from db import save_lifestyle_log, get_today_lifestyle, get_lifestyle_history
from helpers import (C_GREEN, C_DARK_GREEN, C_BLUE, C_GREY,
                     styled_btn, lbl, spacer, card_box,
                     scroll_layout, header_bar, section_lbl, show_popup,
                     text_input)


class LifestyleScreen(Screen):
    def on_pre_enter(self):
        self.clear_widgets()
        app = App.get_running_app()
        uid = app.user_id

        outer = BoxLayout(orientation="vertical")
        outer.add_widget(header_bar("Lifestyle Tracking",
                                     back_cb=self._back, bg=C_BLUE))
        sv, layout = scroll_layout()

        layout.add_widget(section_lbl(
            f"Today: {date.today().strftime('%d %b %Y')}"))
        layout.add_widget(spacer(dp(10)))

        today_data = get_today_lifestyle(uid)

        def _input_card(label_text, hint, attr):
            card = card_box(height=dp(80), padding=dp(12))
            inner = BoxLayout(orientation="vertical", spacing=dp(4))
            inner.add_widget(lbl(label_text, size=dp(12), bold=True, h=dp(24)))
            ti = text_input(hint, height=dp(40))
            if today_data and today_data.get(attr):
                ti.text = str(today_data[attr])
            setattr(self, f"{attr}_input", ti)
            inner.add_widget(ti)
            card.add_widget(inner)
            return card

        layout.add_widget(_input_card("Sleep Hours",          "e.g., 7.5",          "sleep_hours"))
        layout.add_widget(spacer(dp(8)))
        layout.add_widget(_input_card("Stress Level (1-10)",  "1=calm, 10=stressed", "stress_level"))
        layout.add_widget(spacer(dp(8)))
        layout.add_widget(_input_card("Exercise (minutes)",   "e.g., 30",            "exercise_min"))
        layout.add_widget(spacer(dp(8)))
        layout.add_widget(_input_card("Water Intake (liters)","e.g., 2.5",           "water_liters"))
        layout.add_widget(spacer(dp(8)))
        layout.add_widget(_input_card("Screen Time (hours)",  "e.g., 4",             "screen_hours"))
        layout.add_widget(spacer(dp(8)))

        # Notes
        notes_card = card_box(height=dp(110), padding=dp(12))
        notes_inner = BoxLayout(orientation="vertical", spacing=dp(4))
        notes_inner.add_widget(lbl("Notes (optional)", size=dp(12),
                                    bold=True, h=dp(24)))
        self.notes_input = TextInput(
            hint_text="How did you feel today?",
            multiline=True, size_hint_y=None, height=dp(60),
            font_size=dp(12), background_normal="",
            background_color=(1, 1, 1, 1))
        if today_data and today_data.get("notes"):
            self.notes_input.text = today_data["notes"]
        notes_inner.add_widget(self.notes_input)
        notes_card.add_widget(notes_inner)
        layout.add_widget(notes_card)
        layout.add_widget(spacer(dp(12)))

        save_btn = styled_btn("Save Today's Data", bg=C_GREEN, height=dp(48))
        save_btn.bind(on_release=lambda *_: self._save_data())
        layout.add_widget(save_btn)
        layout.add_widget(spacer(dp(16)))

        # Recent history
        layout.add_widget(section_lbl("Recent History (Last 7 Days)"))
        history = get_lifestyle_history(uid, 7)
        if history:
            for entry in history:
                h_card  = card_box(height=dp(70), padding=dp(10))
                date_str = datetime.strptime(
                    entry["date"], "%Y-%m-%d").strftime("%d %b")
                info_box = BoxLayout(orientation="vertical")
                info_box.add_widget(lbl(date_str, size=dp(11),
                                         bold=True, color=C_DARK_GREEN, h=dp(20)))
                info_box.add_widget(lbl(
                    f"Sleep: {entry['sleep_hours'] or 0}h  |  "
                    f"Stress: {entry['stress_level'] or 0}/10  |  "
                    f"Exercise: {entry['exercise_min'] or 0}min",
                    size=dp(10), color=C_GREY, h=dp(18)))
                info_box.add_widget(lbl(
                    f"Water: {entry['water_liters'] or 0}L  |  "
                    f"Screen: {entry['screen_hours'] or 0}h",
                    size=dp(10), color=C_GREY, h=dp(18)))
                h_card.add_widget(info_box)
                layout.add_widget(h_card)
                layout.add_widget(spacer(dp(6)))
        else:
            layout.add_widget(lbl("No history yet. Start tracking today!",
                                   color=C_GREY, halign="center", h=dp(32)))

        layout.add_widget(spacer(dp(20)))
        outer.add_widget(sv)
        self.add_widget(outer)

    def _save_data(self):
        app = App.get_running_app()
        try:
            def _float(attr):
                val = getattr(self, f"{attr}_input").text.strip()
                return float(val) if val else None

            def _int(attr):
                val = getattr(self, f"{attr}_input").text.strip()
                return int(val) if val else None

            data = {
                "sleep_hours":  _float("sleep_hours"),
                "stress_level": _int("stress_level"),
                "exercise_min": _int("exercise_min"),
                "water_liters": _float("water_liters"),
                "screen_hours": _float("screen_hours"),
                "notes":        self.notes_input.text.strip(),
            }

            if data["stress_level"] is not None:
                if not (1 <= data["stress_level"] <= 10):
                    show_popup("Validation Error",
                               "Stress level must be between 1 and 10")
                    return

            save_lifestyle_log(app.user_id, data)
            show_popup("Success", "Lifestyle data saved successfully!",
                       on_ok=lambda: self.on_pre_enter())

        except ValueError:
            show_popup("Input Error",
                       "Please enter valid numbers for all fields")

    def _back(self):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "dashboard"
