# -*- coding: utf-8 -*-
from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen, SlideTransition
from kivy.uix.textinput import TextInput

from db import get_all_foods, foods_by_type, log_food
from helpers import (C_GREEN, C_DARK_GREEN, C_LIGHT_GREEN, C_GREY,
                     C_WHITE, C_TEXT, C_RED, C_ORANGE,
                     styled_btn, lbl, spacer, card_box,
                     scroll_layout, header_bar, show_popup)


class DietPlanScreen(Screen):
    MEALS = ["Breakfast", "Lunch", "Dinner", "Snacks"]

    def on_pre_enter(self):
        self.clear_widgets()
        app         = App.get_running_app()
        self._p     = app.profile
        self._pref  = self._p.get("diet_pref", "No Restriction")
        self._email = self._p.get("email", "")
        self._open  = None
        self._build()

    def _build(self):
        outer = BoxLayout(orientation="vertical")
        outer.add_widget(header_bar("Diet Plan", back_cb=self._back, bg=C_GREEN))

        info_row = BoxLayout(orientation="horizontal",
                              size_hint_y=None, height=dp(32),
                              padding=(dp(10), 0), spacing=dp(6))
        info_row.add_widget(lbl(f"Target: {self._p.get('target', 2000)} kcal",
                                 size=dp(11), color=C_DARK_GREEN, h=dp(28)))
        info_row.add_widget(lbl(f"Pref: {self._pref}",
                                 size=dp(11), color=C_GREY, halign="right", h=dp(28)))
        outer.add_widget(info_row)

        tab_row = BoxLayout(orientation="horizontal",
                             size_hint_y=None, height=dp(44),
                             padding=(dp(8), dp(4)), spacing=dp(6))
        self._tab_btns = {}
        for meal in self.MEALS:
            bg  = C_GREEN if meal == self._open else (0.82, 0.82, 0.82, 1)
            btn = Button(text=meal, size_hint=(1, None), height=dp(36),
                          background_normal="", background_color=bg,
                          color=C_WHITE if meal == self._open else C_TEXT,
                          font_size=dp(12), bold=True)
            btn.bind(on_release=lambda *_, m=meal: self._toggle(m))
            self._tab_btns[meal] = btn
            tab_row.add_widget(btn)
        outer.add_widget(tab_row)

        search_row = BoxLayout(orientation="horizontal",
                                size_hint_y=None, height=dp(44),
                                padding=(dp(8), dp(4)), spacing=dp(6))
        self._search_ti = TextInput(hint_text="Search foods...",
                                     multiline=False, font_size=dp(12),
                                     size_hint=(1, None), height=dp(36))
        clear_btn = styled_btn("✕", bg=C_GREY, height=dp(36),
                                width=dp(36), font_size=dp(13))
        clear_btn.bind(on_release=lambda *_: self._clear_search())
        self._search_ti.bind(text=lambda *_: self._render_food_list())
        search_row.add_widget(self._search_ti)
        search_row.add_widget(clear_btn)
        outer.add_widget(search_row)

        self._sv, self._food_layout = scroll_layout(padding=dp(10), spacing=dp(8))
        self._render_food_list()
        outer.add_widget(self._sv)
        self.add_widget(outer)

    def _toggle(self, meal):
        self._open = None if self._open == meal else meal
        for m, btn in self._tab_btns.items():
            if m == self._open:
                btn.background_color = C_GREEN
                btn.color = C_WHITE
            else:
                btn.background_color = (0.82, 0.82, 0.82, 1)
                btn.color = C_TEXT
        self._render_food_list()

    def _render_food_list(self):
        self._food_layout.clear_widgets()
        query = getattr(self, "_search_ti", None)
        query = query.text.strip().lower() if query else ""

        if query:
            all_items = get_all_foods(self._email)
            filtered  = self._filter(all_items, self._pref)
            results   = [f for f in filtered if query in f["name"].lower()]
            if not results:
                self._food_layout.add_widget(lbl(
                    f'No results for "{query}".', color=C_GREY,
                    halign="center", h=dp(40)))
                return
            self._food_layout.add_widget(lbl(
                f'{len(results)} result(s) for "{query}"',
                size=dp(11), color=C_GREY, h=dp(22)))
            for food in results:
                self._food_layout.add_widget(self._food_card(food, food["type"]))
            self._food_layout.add_widget(spacer(dp(16)))
            return

        if self._open is None:
            self._food_layout.add_widget(spacer(dp(20)))
            self._food_layout.add_widget(lbl(
                "Select a meal section above or search for a food.",
                color=C_GREY, halign="center", h=dp(40)))
            return

        items    = foods_by_type(self._open, self._email)
        filtered = self._filter(items, self._pref)
        if not filtered:
            self._food_layout.add_widget(lbl(
                f"No {self._pref} options found for {self._open}.",
                color=C_GREY, halign="center", h=dp(40)))
            return

        self._food_layout.add_widget(lbl(
            f"{len(filtered)} item(s) for {self._open}",
            size=dp(11), color=C_GREY, h=dp(22)))
        for food in filtered:
            self._food_layout.add_widget(self._food_card(food, self._open))
        self._food_layout.add_widget(spacer(dp(16)))

    def _food_card(self, food, meal):
        c = card_box(height=dp(88))
        info = BoxLayout(orientation="vertical", spacing=dp(2))
        info.add_widget(lbl(food["name"], bold=True, size=dp(13), h=dp(24)))
        info.add_widget(lbl(
            f'Per 100g:  {food["calories"]:.0f} kcal  |  '
            f'P: {food["protein"]:.1f}g   C: {food["carbs"]:.1f}g   '
            f'F: {food["fat"]:.1f}g',
            size=dp(10), color=C_GREY, h=dp(18)))
        info.add_widget(lbl(
            f'{food["category"]}  |  {food.get("source","master").upper()}'
            + (f'  |  {food["type"]}' if food["type"] != meal else ""),
            size=dp(10), color=C_LIGHT_GREEN, h=dp(18)))
        log_btn = styled_btn("+ Log", bg=C_GREEN, height=dp(40), width=dp(60))
        log_btn.bind(on_release=lambda *_, f=food, m=meal: self._log_popup(f, m))
        c.add_widget(info)
        c.add_widget(log_btn)
        return c

    def _clear_search(self):
        self._search_ti.text = ""
        self._render_food_list()

    def _filter(self, items, pref):
        NON_VEG = {"Chicken Breast (Cooked)", "Tuna (Canned)", "Salmon (Cooked)",
                   "Chicken Curry (Home Style)", "Fish Curry", "Grilled Fish",
                   "Mutton (Cooked)", "Grilled Fish Tacos", "Egg (Whole)",
                   "Egg White", "Egg Curry"}
        if pref == "Vegetarian":
            return [i for i in items if i["name"] not in NON_VEG]
        if pref == "Vegan":
            animal = NON_VEG | {"Greek Yogurt", "Milk (Full Fat)", "Paneer",
                                 "Cottage Cheese", "Egg (Whole)", "Egg White"}
            return [i for i in items if i["name"] not in animal]
        if pref == "High Protein":
            return [i for i in items if i["protein"] >= 10]
        return items

    def _log_popup(self, food, meal):
        content = BoxLayout(orientation="vertical",
                            padding=dp(14), spacing=dp(10))
        content.add_widget(Label(
            text=f"{food['name']}\nPer 100g: {food['calories']:.0f} kcal  "
                 f"P:{food['protein']:.1f}g  C:{food['carbs']:.1f}g  "
                 f"F:{food['fat']:.1f}g",
            halign="center", font_size=dp(12), color=C_TEXT,
            size_hint_y=None, height=dp(56)))
        content.add_widget(Label(text="Serving size (grams):",
                                  font_size=dp(12), color=C_GREY,
                                  size_hint_y=None, height=dp(24)))
        grams_i = TextInput(text="100", multiline=False,
                             input_filter="float",
                             size_hint_y=None, height=dp(42))
        content.add_widget(grams_i)

        preview = Label(text=self._nutrient_preview(food, 100),
                         font_size=dp(11), color=C_DARK_GREEN,
                         halign="center", size_hint_y=None, height=dp(24))
        content.add_widget(preview)

        def _update_preview(*_):
            try:
                preview.text = self._nutrient_preview(food, float(grams_i.text))
            except ValueError:
                preview.text = ""
        grams_i.bind(text=_update_preview)

        err_l = Label(text="", color=C_RED, font_size=dp(11),
                       size_hint_y=None, height=dp(20))
        content.add_widget(err_l)

        btn_row = BoxLayout(orientation="horizontal",
                            size_hint_y=None, height=dp(44), spacing=dp(10))
        ok_btn  = styled_btn("Log It", bg=C_GREEN, height=dp(40))
        can_btn = styled_btn("Cancel", bg=C_GREY,  height=dp(40))
        btn_row.add_widget(ok_btn)
        btn_row.add_widget(can_btn)
        content.add_widget(btn_row)

        p = Popup(title=f"Log — {meal}", content=content,
                  size_hint=(0.90, None), height=dp(320))
        can_btn.bind(on_release=p.dismiss)

        def _ok(*_):
            try:
                g = float(grams_i.text)
                if g <= 0:
                    raise ValueError
            except ValueError:
                err_l.text = "Enter a valid positive number."
                return
            log_food(App.get_running_app().user_id, meal, food, g)
            p.dismiss()
            show_popup("Logged ✓", f"{food['name']} ({int(g)}g) added to {meal}!")

        ok_btn.bind(on_release=_ok)
        p.open()

    @staticmethod
    def _nutrient_preview(food, grams):
        f   = grams / 100.0
        return (f"→  {food['calories']*f:.0f} kcal  |  "
                f"P: {food['protein']*f:.1f}g   C: {food['carbs']*f:.1f}g   "
                f"F: {food['fat']*f:.1f}g")

    def _back(self):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "dashboard"
