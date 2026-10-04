# -*- coding: utf-8 -*-
from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.screenmanager import Screen, SlideTransition

from db import today_totals
from helpers import (C_GREEN, C_DARK_GREEN, C_LIGHT_GREEN, C_RED, C_ORANGE,
                     C_GREY, C_TEXT, C_WHITE,
                     styled_btn, lbl, spacer, card_box,
                     scroll_layout, header_bar)


class DashboardScreen(Screen):
    def on_pre_enter(self):
        self.clear_widgets()
        app      = App.get_running_app()
        p        = app.profile
        uid      = app.user_id
        t        = today_totals(uid)
        target   = p.get("target", 2000)
        consumed = t["calories"]
        remaining = max(target - consumed, 0)
        pct      = min(consumed / target, 1.0) if target else 0

        outer = BoxLayout(orientation="vertical")

        # Right-side header controls: Settings (profile) + Logout
        # Width = two 72dp buttons + 6dp spacing
        right_box = BoxLayout(orientation="horizontal", size_hint=(None, 1),
                              width=dp(150), spacing=dp(6))
        settings_btn = styled_btn("Settings", bg=C_GREY,
                                  height=dp(34), width=dp(72), font_size=dp(11))
        settings_btn.bind(on_release=lambda *_: self._go("profile"))
        logout_btn = styled_btn("Logout", bg=C_RED,
                                 height=dp(34), width=dp(72), font_size=dp(11))
        logout_btn.bind(on_release=lambda *_: self._logout())
        right_box.add_widget(settings_btn)
        right_box.add_widget(logout_btn)
        outer.add_widget(header_bar("HabitNourish", bg=C_DARK_GREEN,
                                     right_btn=right_box))

        sv, layout = scroll_layout()

        layout.add_widget(lbl(f"Hello, {p.get('name', 'User')}!",
                               size=dp(20), bold=True, color=C_DARK_GREEN, h=dp(40)))
        layout.add_widget(lbl(
            f"Goal: {p.get('goal', '—')}  |  Diet: {p.get('diet_pref', '—')}",
            size=dp(11), color=C_GREY, h=dp(22)))
        layout.add_widget(spacer())

        # Calorie summary card
        c = card_box(height=dp(150))
        ci = BoxLayout(orientation="vertical", spacing=dp(4))
        ci.add_widget(lbl("Today's Calories", bold=True,
                           color=C_DARK_GREEN, size=dp(14), h=dp(26)))
        ci.add_widget(ProgressBar(value=pct * 100, max=100,
                                   size_hint_y=None, height=dp(16)))
        row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(48))
        for txt, col in [(f"{int(consumed)}\nConsumed", C_GREEN),
                         (f"{int(remaining)}\nRemaining", C_ORANGE),
                         (f"{target}\nTarget",            C_DARK_GREEN)]:
            row.add_widget(Label(text=txt, color=col, halign="center",
                                  font_size=dp(12), bold=True))
        ci.add_widget(row)
        macro = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(26))
        for m, v in [("P", f'{t["protein"]:.0f}g'),
                     ("C", f'{t["carbs"]:.0f}g'),
                     ("F", f'{t["fat"]:.0f}g'),
                     ("Fiber", f'{t["fiber"]:.0f}g')]:
            macro.add_widget(Label(text=f"{m}:{v}", font_size=dp(11),
                                    color=C_TEXT, halign="center"))
        ci.add_widget(macro)
        c.add_widget(ci)
        layout.add_widget(c)

        layout.add_widget(spacer())
        layout.add_widget(lbl("Quick Actions", bold=True, size=dp(14), h=dp(28)))

        # Row 1 — Daily tracking (medium green)
        r1 = BoxLayout(orientation="horizontal", size_hint_y=None,
                       height=dp(48), spacing=dp(6))
        for txt, scr in [("Log Food",  "food_log"),
                         ("Lifestyle", "lifestyle")]:
            b = styled_btn(txt, bg=C_GREEN, height=dp(44))
            b.bind(on_release=lambda *_, s=scr: self._go(s))
            r1.add_widget(b)
        layout.add_widget(r1)

        # Row 2 — Input & planning (dark green)
        r2 = BoxLayout(orientation="horizontal", size_hint_y=None,
                       height=dp(48), spacing=dp(6))
        for txt, scr in [("Custom Food", "custom_food"),
                         ("Meal Plan",   "meal_plan")]:
            b = styled_btn(txt, bg=C_DARK_GREEN, height=dp(44))
            b.bind(on_release=lambda *_, s=scr: self._go(s))
            r2.add_widget(b)
        layout.add_widget(r2)

        # Row 3 — Review & insights (light green)
        r3 = BoxLayout(orientation="horizontal", size_hint_y=None,
                       height=dp(48), spacing=dp(6))
        for txt, scr in [("Progress",  "progress"),
                         ("Analytics", "analytics")]:
            b = styled_btn(txt, bg=C_LIGHT_GREEN, height=dp(44))
            b.bind(on_release=lambda *_, s=scr: self._go(s))
            r3.add_widget(b)
        layout.add_widget(r3)

        layout.add_widget(spacer(dp(20)))
        outer.add_widget(sv)
        self.add_widget(outer)

    def _go(self, screen):
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = screen

    def _logout(self):
        app = App.get_running_app()
        app.user_id = None
        app.profile = {}
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "login"
