# -*- coding: utf-8 -*-
from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.progressbar import ProgressBar
from kivy.uix.screenmanager import Screen, SlideTransition
from kivy.uix.widget import Widget

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
        layout.add_widget(section_lbl("Macros  (today vs. target)"))

        # Daily macro targets (shared with the Analytics screen)
        macro_targets = {"protein": 50, "carbs": 260, "fat": 70, "fiber": 25}

        for name, key, col in [
            ("Protein", "protein", (0.91, 0.12, 0.39, 1)),
            ("Carbs",   "carbs",   C_ORANGE),
            ("Fat",     "fat",     C_GREEN),
            ("Fiber",   "fiber",   C_BLUE),
        ]:
            consumed_m = t[key]
            tgt = macro_targets[key]
            frac = min(consumed_m / tgt, 1.0) if tgt else 0
            pct_m = int(round((consumed_m / tgt) * 100)) if tgt else 0

            row = card_box(height=dp(70))
            col_box = BoxLayout(orientation="vertical", spacing=dp(3))

            # top line: name  ...  consumed / target  (pct%)
            top = BoxLayout(orientation="horizontal",
                            size_hint_y=None, height=dp(22))
            top.add_widget(lbl(name, size=dp(13), bold=True, h=dp(22)))
            top.add_widget(lbl(f"{consumed_m:.1f} / {tgt}g   {pct_m}%",
                               size=dp(12), color=col,
                               halign="right", h=dp(22)))
            col_box.add_widget(top)

            # gradient-style progress bar toward the target
            col_box.add_widget(self._macro_bar(frac, col))

            row.add_widget(col_box)
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

    def _macro_bar(self, frac, color):
        """A track + gradient fill showing progress toward a macro target.

        frac is 0..1 (capped). The fill goes from a lighter tint on the left
        to the full color on the right, so it reads as 'filling up'."""
        frac = max(0.0, min(frac, 1.0))
        bar = Widget(size_hint_y=None, height=dp(14))

        def _draw(w, *_):
            w.canvas.clear()
            x, y, bw, bh = w.x, w.y, w.width, w.height
            if bw <= 0 or bh <= 0:
                return
            r, g, b = color[0], color[1], color[2]
            with w.canvas:
                # track (light grey rounded background)
                Color(0.88, 0.88, 0.88, 1)
                RoundedRectangle(pos=(x, y), size=(bw, bh), radius=[bh / 2])
                # gradient fill, left (light tint) -> right (full color)
                fill_w = bw * frac
                if fill_w > 0:
                    steps = max(int(fill_w), 1)
                    seg_w = fill_w / steps
                    for i in range(steps):
                        # tint factor: 0.55 (light) at left -> 1.0 at right
                        tf = 0.55 + 0.45 * (i / max(steps - 1, 1))
                        rr = r + (1 - r) * (1 - tf)
                        gg = g + (1 - g) * (1 - tf)
                        bb = b + (1 - b) * (1 - tf)
                        Color(rr, gg, bb, 1)
                        RoundedRectangle(
                            pos=(x + i * seg_w, y),
                            size=(seg_w + 1, bh),
                            radius=[bh / 2] if (i == 0 or i == steps - 1) else [0])

        bar.bind(pos=_draw, size=_draw)
        Clock.schedule_once(lambda dt: _draw(bar), 0)
        return bar

    def _go(self, screen):
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = screen

    def _back(self):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "dashboard"
