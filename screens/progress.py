# -*- coding: utf-8 -*-
from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.progressbar import ProgressBar
from kivy.uix.screenmanager import Screen, SlideTransition

from db import today_totals
from helpers import (C_GREEN, C_DARK_GREEN, C_BLUE, C_RED, C_ORANGE,
                     styled_btn, lbl, spacer, card_box,
                     scroll_layout, header_bar, section_lbl)


class ProgressScreen(Screen):
    def on_pre_enter(self):
        self.clear_widgets()
        app      = App.get_running_app()
        p        = app.profile
        uid      = app.user_id
        target   = p.get("target", 2000)
        t        = today_totals(uid)
        consumed = t["calories"]
        pct      = min(consumed / target, 1.0) if target else 0

        outer = BoxLayout(orientation="vertical")
        outer.add_widget(header_bar("Today's Progress",
                                     back_cb=self._back, bg=C_DARK_GREEN))
        sv, layout = scroll_layout()

        # Summary card
        c = card_box(height=dp(130))
        ci = BoxLayout(orientation="vertical", spacing=dp(6))
        ci.add_widget(lbl(f"{int(consumed)} / {target} kcal",
                           bold=True, size=dp(18), color=C_GREEN, h=dp(34)))
        ci.add_widget(ProgressBar(value=pct * 100, max=100,
                                   size_hint_y=None, height=dp(18)))
        if pct < 0.9:
            status, scol = "On Track!", C_GREEN
        elif pct < 1.0:
            status, scol = "Almost there!", C_ORANGE
        else:
            status, scol = "Daily limit reached!", C_RED
        ci.add_widget(lbl(status, bold=True, color=scol, size=dp(14), h=dp(28)))
        c.add_widget(ci)
        layout.add_widget(c)

        layout.add_widget(spacer())
        layout.add_widget(section_lbl("Macros"))

        for name, val, col in [
            ("Protein", f'{t["protein"]:.1f}g', (0.91, 0.12, 0.39, 1)),
            ("Carbs",   f'{t["carbs"]:.1f}g',   C_ORANGE),
            ("Fat",     f'{t["fat"]:.1f}g',     C_GREEN),
            ("Fiber",   f'{t["fiber"]:.1f}g',   C_BLUE),
        ]:
            row = card_box(height=dp(44))
            row.add_widget(lbl(name, size=dp(13), h=dp(36)))
            row.add_widget(lbl(val, size=dp(13), color=col,
                                halign="right", h=dp(36)))
            layout.add_widget(row)

        layout.add_widget(spacer())
        btn = styled_btn("View Full Log / Delete Entries",
                          bg=C_ORANGE, height=dp(44))
        btn.bind(on_release=lambda *_: self._go("food_log"))
        layout.add_widget(btn)

        layout.add_widget(spacer())
        btn2 = styled_btn("View Analytics", bg=C_DARK_GREEN, height=dp(44))
        btn2.bind(on_release=lambda *_: self._go("analytics"))
        layout.add_widget(btn2)

        layout.add_widget(spacer(dp(20)))
        outer.add_widget(sv)
        self.add_widget(outer)

    def _go(self, screen):
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = screen

    def _back(self):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "dashboard"
