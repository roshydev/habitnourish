# -*- coding: utf-8 -*-
from datetime import date, datetime, timedelta

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, Line, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.screenmanager import Screen, SlideTransition
from kivy.uix.widget import Widget

from db import week_nutrients, meal_breakdown, get_lifestyle_history
from helpers import (C_GREEN, C_DARK_GREEN, C_BLUE, C_RED, C_ORANGE,
                     C_GREY, C_TEXT, C_WHITE,
                     styled_btn, lbl, spacer, card_box,
                     scroll_layout, header_bar, section_lbl)


class AnalyticsScreen(Screen):
    SERIES = [
        ("calories", "Cal",  (0.298, 0.686, 0.314, 1)),
        ("protein",  "Pro",  (0.129, 0.588, 0.953, 1)),
        ("carbs",    "Carb", (1.000, 0.596, 0.000, 1)),
        ("fat",      "Fat",  (0.600, 0.200, 0.800, 1)),
        ("fiber",    "Fib",  (0.000, 0.700, 0.700, 1)),
        ("sugar",    "Sug",  (0.950, 0.300, 0.100, 1)),
    ]
    TARGETS = {
        "protein": 50, "carbs": 260, "fat": 70, "fiber": 25, "sugar": 50
    }

    # ── Nutrition chart drawing ───────────────────────────────────────────────
    def _draw_chart(self, widget, all_days, nutrient_data, cal_target, series):
        all_vals = []
        for d in all_days:
            nd = nutrient_data[d]
            all_vals.extend([nd[k] for k, _, _ in series])
        global_max = max(all_vals) if any(v > 0 for v in all_vals) else max(cal_target, 1)

        targets = {
            "calories": cal_target,
            "protein":  self.TARGETS["protein"],
            "carbs":    self.TARGETS["carbs"],
            "fat":      self.TARGETS["fat"],
            "fiber":    self.TARGETS["fiber"],
            "sugar":    self.TARGETS["sugar"],
        }

        def _draw(w, *_):
            w.canvas.clear()
            cw, ch = w.width, w.height
            if cw <= 0 or ch <= 0:
                return
            n_days, n_series = len(all_days), len(series)
            left_m, right_m  = dp(6), dp(6)
            bot_m,  top_m    = dp(4), dp(10)
            usable_w = cw - left_m - right_m
            usable_h = ch - bot_m - top_m
            base_y   = w.y + bot_m
            group_w  = usable_w / n_days
            gap, bar_gap = dp(4), dp(1)
            bar_w = max((group_w - gap) / n_series - bar_gap, dp(2))
            scale = usable_h / (global_max * 1.15) if global_max else 1

            with w.canvas:
                for di, d in enumerate(all_days):
                    nd     = nutrient_data[d]
                    grp_x0 = w.x + left_m + di * group_w + gap / 2
                    for si, (key, _, color) in enumerate(series):
                        val = nd[key]
                        bx  = grp_x0 + si * (bar_w + bar_gap)
                        bh  = min(val * scale, usable_h) if val else 0
                        if key == "calories" and cal_target and val > cal_target:
                            Color(0.85, 0.15, 0.15, 1)
                        else:
                            Color(*color)
                        Rectangle(pos=(bx, base_y), size=(bar_w, bh))
                    for si, (key, _, color) in enumerate(series):
                        tgt = targets.get(key)
                        if tgt is None or nd[key] == 0:
                            continue
                        ty  = base_y + min(tgt * scale, usable_h)
                        bx  = grp_x0 + si * (bar_w + bar_gap)
                        Color(0.58, 0.0, 0.83, 0.8)
                        seg, gap_s = dp(3), dp(2)
                        x = bx
                        while x < bx + bar_w:
                            x1 = min(x + seg, bx + bar_w)
                            Line(points=[x, ty, x1, ty], width=1.5)
                            x += seg + gap_s

        widget.bind(pos=_draw, size=_draw)
        _draw(widget)

    # ── Lifestyle chart drawing ───────────────────────────────────────────────
    def _draw_lifestyle_chart(self, widget, all_days, lifestyle_dict, series, targets):
        global_max = max([s[3] for s in series])

        def _draw(w, *_):
            w.canvas.clear()
            cw, ch = w.width, w.height
            if cw <= 0 or ch <= 0:
                return
            n_days, n_series = len(all_days), len(series)
            left_m, right_m = dp(6), dp(6)
            bot_m,  top_m   = dp(4), dp(10)
            usable_w = cw - left_m - right_m
            usable_h = ch - bot_m - top_m
            base_y   = w.y + bot_m
            group_w  = usable_w / n_days
            gap, bar_gap = dp(4), dp(1)
            bar_w = max((group_w - gap) / n_series - bar_gap, dp(2))
            scale = usable_h / (global_max * 1.15) if global_max else 1

            with w.canvas:
                for di, d in enumerate(all_days):
                    entry  = lifestyle_dict.get(d, {})
                    grp_x0 = w.x + left_m + di * group_w + gap / 2
                    for si, (key, _, color, max_val) in enumerate(series):
                        val = entry.get(key, 0) or 0
                        bx  = grp_x0 + si * (bar_w + bar_gap)
                        normalized_val = val * (global_max / max_val)
                        bh  = min(normalized_val * scale, usable_h) if val else 0
                        if key == "stress_level" and val > 0:
                            if val <= 3:
                                Color(0.298, 0.686, 0.314, 1)
                            elif val <= 6:
                                Color(1.0, 0.596, 0.0, 1)
                            else:
                                Color(0.957, 0.263, 0.212, 1)
                        else:
                            Color(*color)
                        Rectangle(pos=(bx, base_y), size=(bar_w, bh))
                    for si, (key, _, color, max_val) in enumerate(series):
                        tgt = targets.get(key)
                        if tgt is None or (entry.get(key, 0) or 0) == 0:
                            continue
                        normalized_tgt = tgt * (global_max / max_val)
                        ty  = base_y + min(normalized_tgt * scale, usable_h)
                        bx  = grp_x0 + si * (bar_w + bar_gap)
                        Color(0.58, 0.0, 0.83, 0.8)
                        seg, gap_s = dp(3), dp(2)
                        x = bx
                        while x < bx + bar_w:
                            x1 = min(x + seg, bx + bar_w)
                            Line(points=[x, ty, x1, ty], width=1.5)
                            x += seg + gap_s

        widget.bind(pos=_draw, size=_draw)
        _draw(widget)

    # ── Static helpers ────────────────────────────────────────────────────────
    @staticmethod
    def _cal_label_row(all_days, nutrient_data, cal_target):
        row = BoxLayout(orientation="horizontal",
                         size_hint_y=None, height=dp(28))
        for d in all_days:
            cal = nutrient_data[d]["calories"]
            if cal == 0:
                txt, col = "–", C_GREY
            else:
                diff  = int(cal) - cal_target
                sign  = "+" if diff >= 0 else ""
                d_col = "ff4444" if diff > 0 else "44bb44"
                txt   = f"{int(cal)}\n[color=#{d_col}]({sign}{diff})[/color]"
                col   = C_TEXT
            row.add_widget(Label(text=txt, markup=True, font_size=dp(8),
                                  color=col, halign="center",
                                  valign="middle", bold=True))
        return row

    @staticmethod
    def _day_row(all_days):
        row = BoxLayout(orientation="horizontal",
                         size_hint_y=None, height=dp(20))
        for d in all_days:
            short = datetime.strptime(d, "%Y-%m-%d").strftime("%a\n%d")
            row.add_widget(Label(text=short, font_size=dp(8),
                                  color=C_GREY, halign="center"))
        return row

    @staticmethod
    def _legend(series):
        outer = BoxLayout(orientation="horizontal",
                           size_hint_y=None, height=dp(22),
                           spacing=dp(4), padding=(dp(4), 0))
        for _, label, color in series:
            outer.add_widget(Label(
                text=f"[b]■[/b] {label}", markup=True,
                font_size=dp(9), color=color,
                halign="center", size_hint=(1, None), height=dp(20)))
        return outer

    # ── Toggle ────────────────────────────────────────────────────────────────
    def _toggle_chart(self):
        if self.chart_mode == "nutrition":
            self.chart_mode = "lifestyle"
            self.toggle_btn.text = "Switch to Nutrition"
            self.toggle_btn.background_color = C_GREEN
            self._render_lifestyle_chart()
        else:
            self.chart_mode = "nutrition"
            self.toggle_btn.text = "Switch to Lifestyle"
            self.toggle_btn.background_color = C_BLUE
            self._render_nutrition_chart()

    def _render_nutrition_chart(self):
        if hasattr(self, "chart_container"):
            self.layout.remove_widget(self.chart_container)

        self.chart_container = BoxLayout(orientation="vertical",
                                          size_hint_y=None, height=dp(300))
        self.chart_container.add_widget(self._legend(self.SERIES))
        self.chart_container.add_widget(lbl(
            "Violet dashes = target per nutrient  |  Red Cal bar = over target",
            size=dp(9), color=C_GREY, h=dp(16)))

        chart_w = Widget(size_hint=(1, None), height=dp(220))
        self.chart_container.add_widget(chart_w)
        self.chart_container.add_widget(self._day_row(self.all_days))
        self.chart_container.add_widget(
            self._cal_label_row(self.all_days, self.nutrient_data, self.target))

        Clock.schedule_once(lambda dt: self._draw_chart(
            chart_w, self.all_days, self.nutrient_data,
            self.target, self.SERIES), 0.05)

        children = self.layout.children[:]
        self.layout.add_widget(self.chart_container, index=len(children) - 1)

    def _render_lifestyle_chart(self):
        if hasattr(self, "chart_container"):
            self.layout.remove_widget(self.chart_container)

        LIFESTYLE_SERIES = [
            ("sleep_hours",  "Sleep",    (0.129, 0.588, 0.953, 1), 10),
            ("exercise_min", "Exercise", (0.298, 0.686, 0.314, 1), 120),
            ("water_liters", "Water",    (0.0,   0.7,   0.7,   1), 4),
            ("stress_level", "Stress",   (1.0,   0.596, 0.0,   1), 10),
        ]
        LIFESTYLE_TARGETS = {
            "sleep_hours":  8,
            "exercise_min": 30,
            "water_liters": 2.5,
            "stress_level": 3,
        }

        self.chart_container = BoxLayout(orientation="vertical",
                                          size_hint_y=None, height=dp(300))

        legend = BoxLayout(orientation="horizontal", size_hint_y=None,
                           height=dp(22), spacing=dp(4), padding=(dp(4), 0))
        for _, label, color, _ in LIFESTYLE_SERIES:
            legend.add_widget(Label(
                text=f"[b]■[/b] {label}", markup=True,
                font_size=dp(9), color=color,
                halign="center", size_hint=(1, None), height=dp(20)))
        self.chart_container.add_widget(legend)
        self.chart_container.add_widget(lbl(
            "Violet dashes = target for each metric",
            size=dp(9), color=C_GREY, h=dp(16)))

        chart_w = Widget(size_hint=(1, None), height=dp(220))
        self.chart_container.add_widget(chart_w)
        self.chart_container.add_widget(self._day_row(self.all_days))

        # Averages summary
        active = [d for d in self.all_days
                  if d in self.lifestyle_dict
                  and self.lifestyle_dict[d].get("sleep_hours")]
        if active:
            n = len(active)
            avg_sleep    = sum(self.lifestyle_dict.get(d, {}).get("sleep_hours",    0) for d in self.all_days) / n
            avg_exercise = sum(self.lifestyle_dict.get(d, {}).get("exercise_min",   0) for d in self.all_days) / n
            avg_water    = sum(self.lifestyle_dict.get(d, {}).get("water_liters",   0) for d in self.all_days) / n
            avg_stress   = sum(self.lifestyle_dict.get(d, {}).get("stress_level",   0) for d in self.all_days) / n
            txt = (f"Avg: Sleep {avg_sleep:.1f}h | Exercise {avg_exercise:.0f}min | "
                   f"Water {avg_water:.1f}L | Stress {avg_stress:.1f}/10")
        else:
            txt = "No lifestyle data logged yet"

        summary_row = BoxLayout(orientation="horizontal",
                                size_hint_y=None, height=dp(28))
        summary_row.add_widget(Label(text=txt, font_size=dp(9),
                                      color=C_DARK_GREEN, bold=True))
        self.chart_container.add_widget(summary_row)

        Clock.schedule_once(lambda dt: self._draw_lifestyle_chart(
            chart_w, self.all_days, self.lifestyle_dict,
            LIFESTYLE_SERIES, LIFESTYLE_TARGETS), 0.05)

        children = self.layout.children[:]
        self.layout.add_widget(self.chart_container, index=len(children) - 1)

    # ── Main build ────────────────────────────────────────────────────────────
    def on_pre_enter(self):
        self.clear_widgets()
        app    = App.get_running_app()
        uid    = app.user_id
        target = app.profile.get("target", 2000)

        outer = BoxLayout(orientation="vertical")
        outer.add_widget(header_bar("Analytics",
                                     back_cb=self._back, bg=C_DARK_GREEN))
        sv, layout = scroll_layout()

        all_days = [str(date.today() - timedelta(days=i))
                    for i in range(6, -1, -1)]
        raw   = week_nutrients(uid)
        blank = {"calories": 0, "protein": 0, "carbs": 0,
                 "fat": 0, "fiber": 0, "sugar": 0}
        nutrient_data = {d: raw.get(d, dict(blank)) for d in all_days}
        active_days   = [d for d in all_days if nutrient_data[d]["calories"] > 0]

        lifestyle_raw  = get_lifestyle_history(uid, 7)
        lifestyle_dict = {e["date"]: e for e in lifestyle_raw}

        # ── Toggle header ────────────────────────────────────────────────────
        self.chart_mode = "nutrition"
        header_row = BoxLayout(orientation="horizontal",
                               size_hint_y=None, height=dp(40))
        header_row.add_widget(section_lbl("7-Day Overview"))
        self.toggle_btn = styled_btn("Switch to Lifestyle", bg=C_BLUE,
                                      height=dp(36), width=dp(140))
        self.toggle_btn.bind(on_release=lambda *_: self._toggle_chart())
        header_row.add_widget(self.toggle_btn)
        layout.add_widget(header_row)

        # Store for toggle reuse
        self.layout        = layout
        self.all_days      = all_days
        self.nutrient_data = nutrient_data
        self.lifestyle_dict = lifestyle_dict
        self.target        = target
        self.user_id       = uid

        self._render_nutrition_chart()

        layout.add_widget(spacer())

        # ── Week summary card ────────────────────────────────────────────────
        met  = sum(1 for d in all_days if 0 < nutrient_data[d]["calories"] <= target)
        over = sum(1 for d in all_days if nutrient_data[d]["calories"] > target)
        no_d = len(all_days) - len(active_days)
        wc   = card_box(height=dp(40))
        wc.add_widget(lbl(
            f"Last 7 days:  ✓ {met} days on target  "
            f"✗ {over} days over  – {no_d} days no data",
            size=dp(11), color=C_DARK_GREEN, bold=True, h=dp(32)))
        layout.add_widget(wc)
        layout.add_widget(spacer())

        # ── Detailed table ───────────────────────────────────────────────────
        layout.add_widget(section_lbl("7-Day Detailed Summary  (+/- vs target)"))
        hdr = card_box(height=dp(32), bg=C_DARK_GREEN)
        for txt in ["Date","Cal","Pro","Carb","Fat","Fib","Sug","Status"]:
            hdr.add_widget(Label(text=txt, color=C_WHITE,
                                  font_size=dp(9), bold=True))
        layout.add_widget(hdr)

        nut_targets = {
            "calories": target,
            "protein":  self.TARGETS["protein"],
            "carbs":    self.TARGETS["carbs"],
            "fat":      self.TARGETS["fat"],
            "fiber":    self.TARGETS["fiber"],
            "sugar":    self.TARGETS["sugar"],
        }

        def val_cell(val, tgt, unit=""):
            if val == 0:
                return Label(text="–", font_size=dp(9), color=C_GREY,
                              halign="center", size_hint_y=None, height=dp(44))
            diff  = val - tgt
            sign  = "+" if diff >= 0 else ""
            d_col = "44bb44" if diff < 0 else "ff4444"
            text  = f"{val:.0f}{unit}\n[color=#{d_col}]({sign}{diff:.0f})[/color]"
            return Label(text=text, markup=True, font_size=dp(8),
                          color=C_TEXT, halign="center", valign="middle",
                          size_hint_y=None, height=dp(44), bold=True)

        for d in all_days:
            nd    = nutrient_data[d]
            short = datetime.strptime(d, "%Y-%m-%d").strftime("%d%b")
            cal   = nd["calories"]
            if cal == 0:
                status_sym, s_col = "–", C_GREY
            elif cal <= target:
                status_sym, s_col = "✓", C_GREEN
            else:
                status_sym, s_col = "✗", C_RED
            row = card_box(height=dp(44))
            row.add_widget(lbl(short, size=dp(9), h=dp(36)))
            row.add_widget(val_cell(nd["calories"], nut_targets["calories"]))
            row.add_widget(val_cell(nd["protein"],  nut_targets["protein"], "g"))
            row.add_widget(val_cell(nd["carbs"],    nut_targets["carbs"],   "g"))
            row.add_widget(val_cell(nd["fat"],      nut_targets["fat"],     "g"))
            row.add_widget(val_cell(nd["fiber"],    nut_targets["fiber"],   "g"))
            row.add_widget(val_cell(nd["sugar"],    nut_targets["sugar"],   "g"))
            row.add_widget(lbl(status_sym, size=dp(12), bold=True,
                                color=s_col, halign="center", h=dp(36)))
            layout.add_widget(row)

        layout.add_widget(lbl(
            f"  Targets: Cal={target} kcal  Pro={self.TARGETS['protein']}g  "
            f"Carb={self.TARGETS['carbs']}g  Fat={self.TARGETS['fat']}g  "
            f"Fib={self.TARGETS['fiber']}g  Sug={self.TARGETS['sugar']}g",
            size=dp(9), color=C_GREY, h=dp(18)))
        layout.add_widget(spacer())

        # ── Meal breakdown ───────────────────────────────────────────────────
        layout.add_widget(section_lbl("Today's Meal Breakdown"))
        breakdown   = meal_breakdown(uid)
        total_today = sum(breakdown.values()) or 1
        m_colors    = {"Breakfast": C_ORANGE, "Lunch": C_GREEN,
                       "Dinner": C_DARK_GREEN, "Snacks": C_BLUE}
        if breakdown:
            for meal, cal in breakdown.items():
                pct = cal / total_today
                row = card_box(height=dp(44))
                row.add_widget(lbl(meal, size=dp(12), h=dp(36)))
                row.add_widget(ProgressBar(value=pct * 100, max=100,
                                            size_hint=(0.4, None), height=dp(14)))
                row.add_widget(lbl(f"{int(cal)} kcal", size=dp(11),
                                    color=m_colors.get(meal, C_GREEN),
                                    halign="right", h=dp(36)))
                layout.add_widget(row)
        else:
            layout.add_widget(lbl("No food logged today.",
                                   color=C_GREY, halign="center", h=dp(32)))

        layout.add_widget(spacer())

        # ── Averages ─────────────────────────────────────────────────────────
        n_active = len(active_days)
        layout.add_widget(section_lbl(
            f"Averages  (based on {n_active} active day"
            f"{'s' if n_active != 1 else ''} only)"))

        if n_active == 0:
            layout.add_widget(lbl("No data logged in the last 7 days.",
                                   color=C_GREY, halign="center", h=dp(32)))
        else:
            avg_vals = {k: sum(nutrient_data[d][k] for d in active_days) / n_active
                        for k in ["calories","protein","carbs","fat","fiber","sugar"]}
            avg_defs = [
                ("Calories", "kcal", C_GREEN,            target),
                ("Protein",  "g",    C_BLUE,              self.TARGETS["protein"]),
                ("Carbs",    "g",    C_ORANGE,            self.TARGETS["carbs"]),
                ("Fat",      "g",    (0.6, 0.2, 0.8, 1), self.TARGETS["fat"]),
                ("Fiber",    "g",    (0.0, 0.7, 0.7, 1), self.TARGETS["fiber"]),
                ("Sugar",    "g",    (0.95, 0.3, 0.1, 1),self.TARGETS["sugar"]),
            ]
            for name, unit, col, tgt in avg_defs:
                val  = avg_vals[name.lower()]
                diff = val - tgt
                sign = "+" if diff >= 0 else ""
                d_col_hex = "ff4444" if diff > 0 else "44bb44"
                row = card_box(height=dp(52))
                left = BoxLayout(orientation="vertical")
                left.add_widget(lbl(f"Avg {name}", size=dp(12), bold=True, h=dp(22)))
                left.add_widget(lbl(f"Target: {tgt} {unit}",
                                     size=dp(9), color=C_GREY, h=dp(16)))
                row.add_widget(left)
                val_lbl = Label(
                    text=f"{val:.1f} {unit}/day\n"
                         f"[color=#{d_col_hex}]({sign}{diff:.0f})[/color]",
                    markup=True, font_size=dp(11), bold=True, color=C_TEXT,
                    halign="right", valign="middle",
                    size_hint_y=None, height=dp(44))
                row.add_widget(val_lbl)
                layout.add_widget(row)

        layout.add_widget(spacer())
        plan_btn = styled_btn("Plan Next 7 Days", bg=C_DARK_GREEN, height=dp(46))
        plan_btn.bind(on_release=lambda *_: self._go("meal_plan"))
        layout.add_widget(plan_btn)

        layout.add_widget(spacer(dp(20)))
        outer.add_widget(sv)
        self.add_widget(outer)

    def _go(self, screen):
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = screen

    def _back(self):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "dashboard"
