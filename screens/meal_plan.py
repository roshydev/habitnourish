# -*- coding: utf-8 -*-
from datetime import date, datetime, timedelta

from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen, SlideTransition
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton

from db import get_plan_for_range, save_plan_entry, delete_plan_entry, get_all_foods
from helpers import (C_GREEN, C_DARK_GREEN, C_LIGHT_GREEN, C_BLUE, C_RED,
                     C_GREY, C_TEXT, C_WHITE,
                     styled_btn, lbl, spacer, card_box,
                     scroll_layout, header_bar)


class MealPlanScreen(Screen):
    def on_pre_enter(self):
        self.clear_widgets()
        app = App.get_running_app()
        self._uid   = app.user_id
        self._email = app.profile.get("email", "")

        self._start = date.today()
        self._end   = self._start + timedelta(days=6)
        self._plan  = get_plan_for_range(self._uid, self._start, self._end)

        outer = BoxLayout(orientation="vertical")
        outer.add_widget(header_bar("7-Day Meal Plan",
                                     back_cb=self._back, bg=C_DARK_GREEN))
        outer.add_widget(lbl(
            f"  Plan: {self._start.strftime('%d %b')} – "
            f"{self._end.strftime('%d %b %Y')}",
            size=dp(12), color=C_GREY, h=dp(22)))

        sv, self._layout = scroll_layout(padding=dp(10), spacing=dp(8))
        self._render_plan()
        outer.add_widget(sv)
        self.add_widget(outer)

    def _render_plan(self):
        self._layout.clear_widgets()
        self._plan = get_plan_for_range(self._uid, self._start, self._end)

        by_date = {}
        for e in self._plan:
            by_date.setdefault(e["plan_date"], []).append(e)

        for i in range(7):
            d       = self._start + timedelta(days=i)
            d_str   = str(d)
            label   = d.strftime("%A, %d %b")
            entries = by_date.get(d_str, [])
            day_cal = sum(e["calories"] for e in entries)

            day_hdr = card_box(height=dp(44), bg=C_DARK_GREEN)
            day_hdr.add_widget(Label(text=label, color=C_WHITE,
                                      font_size=dp(13), bold=True))
            day_hdr.add_widget(Label(text=f"{int(day_cal)} kcal",
                                      color=(1, 1, 0.6, 1), font_size=dp(11)))
            add_btn = styled_btn("+ Add", bg=C_GREEN,
                                  height=dp(32), width=dp(58), font_size=dp(11))
            add_btn.bind(on_release=lambda *_, ds=d_str: self._add_popup(ds))
            day_hdr.add_widget(add_btn)
            self._layout.add_widget(day_hdr)

            if not entries:
                self._layout.add_widget(lbl("   No meals planned yet.",
                                             color=C_GREY, size=dp(11), h=dp(24)))
            else:
                by_meal = {}
                for e in entries:
                    by_meal.setdefault(e["meal"], []).append(e)
                for meal in ["Breakfast", "Lunch", "Dinner", "Snacks"]:
                    meal_entries = by_meal.get(meal, [])
                    if not meal_entries:
                        continue
                    self._layout.add_widget(lbl(
                        f"   {meal}", color=C_DARK_GREEN,
                        bold=True, size=dp(11), h=dp(22)))
                    for e in meal_entries:
                        row = card_box(height=dp(48))
                        info = BoxLayout(orientation="vertical")
                        info.add_widget(lbl(
                            f"{e['food_name']}  ({int(e['grams'])}g)",
                            size=dp(11), bold=True, h=dp(22)))
                        info.add_widget(lbl(
                            f"{int(e['calories'])} kcal | "
                            f"P:{e['protein']:.0f}g  C:{e['carbs']:.0f}g  "
                            f"F:{e['fat']:.0f}g",
                            size=dp(9), color=C_GREY, h=dp(18)))
                        row.add_widget(info)
                        del_btn = styled_btn("✕", bg=C_RED,
                                              height=dp(32), width=dp(36),
                                              font_size=dp(12))
                        del_btn.bind(on_release=lambda *_, eid=e["id"]:
                                     self._delete(eid))
                        row.add_widget(del_btn)
                        self._layout.add_widget(row)

        self._layout.add_widget(spacer(dp(20)))

    def _add_popup(self, plan_date):
        content = BoxLayout(orientation="vertical",
                            padding=dp(12), spacing=dp(8))
        d_label = datetime.strptime(plan_date, "%Y-%m-%d").strftime("%A, %d %b")
        content.add_widget(Label(text=f"Add food for {d_label}",
                                  font_size=dp(13), bold=True, color=C_TEXT,
                                  size_hint_y=None, height=dp(28)))

        content.add_widget(Label(text="Meal:", font_size=dp(12),
                                  color=C_GREY, size_hint_y=None, height=dp(22)))
        meal_row = BoxLayout(orientation="horizontal",
                              size_hint_y=None, height=dp(38), spacing=dp(4))
        self._plan_meal_var = "Breakfast"
        for m in ["Breakfast", "Lunch", "Dinner", "Snacks"]:
            mb = ToggleButton(text=m, group="plan_meal",
                               state="down" if m == "Breakfast" else "normal",
                               size_hint=(1, None), height=dp(34),
                               background_normal="", background_down="",
                               background_color=C_LIGHT_GREEN if m == "Breakfast"
                               else (0.85, 0.85, 0.85, 1),
                               color=C_TEXT, font_size=dp(10))
            def _mt(btn, val, b=mb, meal=m):
                b.background_color = C_LIGHT_GREEN if val == "down" \
                    else (0.85, 0.85, 0.85, 1)
                if val == "down":
                    self._plan_meal_var = meal
            mb.bind(state=_mt)
            meal_row.add_widget(mb)
        content.add_widget(meal_row)

        content.add_widget(Label(text="Search food:", font_size=dp(12),
                                  color=C_GREY, size_hint_y=None, height=dp(22)))
        search_row = BoxLayout(orientation="horizontal",
                                size_hint_y=None, height=dp(38), spacing=dp(6))
        search_ti = TextInput(hint_text="Type food name", multiline=False,
                               font_size=dp(12), size_hint=(0.7, None), height=dp(36))
        results_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(2))
        results_box.bind(minimum_height=results_box.setter("height"))
        self._plan_selected_food = None

        def _search(*_):
            results_box.clear_widgets()
            q = search_ti.text.strip().lower()
            if not q:
                return
            matches = [f for f in get_all_foods(self._email)
                       if q in f["name"].lower()][:6]
            for f in matches:
                fb = Button(
                    text=f'{f["name"]} ({f["type"]}) — {f["calories"]:.0f} kcal/100g',
                    font_size=dp(10), size_hint_y=None, height=dp(32),
                    background_normal="", background_color=C_LIGHT_GREEN,
                    color=C_TEXT)
                def _sel(*_, food=f):
                    self._plan_selected_food = food
                    results_box.clear_widgets()
                    results_box.add_widget(Label(
                        text=f"Selected: {food['name']}",
                        font_size=dp(11), color=C_GREEN,
                        size_hint_y=None, height=dp(24)))
                fb.bind(on_release=_sel)
                results_box.add_widget(fb)

        s_btn = styled_btn("Go", bg=C_BLUE, height=dp(36), width=dp(44))
        s_btn.bind(on_release=_search)
        search_row.add_widget(search_ti)
        search_row.add_widget(s_btn)
        content.add_widget(search_row)
        content.add_widget(results_box)

        g_row = BoxLayout(orientation="horizontal",
                           size_hint_y=None, height=dp(38), spacing=dp(6))
        g_row.add_widget(Label(text="Grams:", font_size=dp(12),
                                color=C_GREY, size_hint=(0.4, None), height=dp(36)))
        grams_ti = TextInput(text="100", multiline=False, input_filter="float",
                              size_hint=(0.6, None), height=dp(36))
        g_row.add_widget(grams_ti)
        content.add_widget(g_row)

        err_l = Label(text="", color=C_RED, font_size=dp(11),
                       size_hint_y=None, height=dp(20))
        content.add_widget(err_l)

        btn_row = BoxLayout(orientation="horizontal",
                             size_hint_y=None, height=dp(42), spacing=dp(8))
        ok_btn  = styled_btn("Add to Plan", bg=C_GREEN, height=dp(38))
        can_btn = styled_btn("Cancel",      bg=C_GREY,  height=dp(38))
        btn_row.add_widget(ok_btn)
        btn_row.add_widget(can_btn)
        content.add_widget(btn_row)

        popup = Popup(title="Add to Meal Plan", content=content,
                      size_hint=(0.92, None), height=dp(520))
        can_btn.bind(on_release=popup.dismiss)

        def _ok(*_):
            if not self._plan_selected_food:
                err_l.text = "Please select a food first."
                return
            try:
                g = float(grams_ti.text)
            except ValueError:
                err_l.text = "Enter a valid gram value."
                return
            save_plan_entry(self._uid, plan_date,
                            self._plan_meal_var,
                            self._plan_selected_food, g)
            popup.dismiss()
            self._render_plan()

        ok_btn.bind(on_release=_ok)
        popup.open()

    def _delete(self, entry_id):
        delete_plan_entry(entry_id)
        self._render_plan()

    def _back(self):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "analytics"
