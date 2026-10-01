# -*- coding: utf-8 -*-
from kivy.app import App
from kivy.graphics import Color
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen, SlideTransition

from db import load_master_foods, save_user_food
from helpers import (C_GREEN, C_DARK_GREEN, C_BLUE, C_RED, C_GREY,
                     C_CARD, C_TEXT, C_LIGHT_GREEN,
                     styled_btn, lbl, spacer, text_input,
                     section_lbl, scroll_layout, header_bar,
                     radio_group, show_popup)


class CustomFoodScreen(Screen):
    def on_pre_enter(self):
        self.clear_widgets()
        self._master = load_master_foods()
        self._selected_master = None

        outer = BoxLayout(orientation="vertical")
        outer.add_widget(header_bar("Add Custom Food",
                                     back_cb=self._back, bg=C_DARK_GREEN))
        sv, layout = scroll_layout()

        layout.add_widget(section_lbl("Search Master Food Sheet"))
        self.search_i = text_input("Type food name to search...")
        layout.add_widget(self.search_i)
        s_btn = styled_btn("Search", bg=C_BLUE, height=dp(40))
        s_btn.bind(on_release=lambda *_: self._search())
        layout.add_widget(s_btn)

        self.search_results = BoxLayout(orientation="vertical",
                                         size_hint_y=None, spacing=dp(4))
        self.search_results.bind(
            minimum_height=self.search_results.setter("height"))
        layout.add_widget(self.search_results)

        layout.add_widget(spacer())
        layout.add_widget(lbl("-- Or enter manually (values per 100g) --",
                               color=C_GREY, halign="center", h=dp(24)))

        layout.add_widget(section_lbl("Food Name"))
        self.name_i = text_input("Food name")
        layout.add_widget(self.name_i)

        layout.add_widget(section_lbl("Meal Type"))
        type_box, self.get_type = radio_group(
            ["Breakfast", "Lunch", "Dinner", "Snacks"], "Snacks", "ftype")
        layout.add_widget(type_box)

        fields = [("Calories (kcal)", "cal_i"),  ("Protein (g)",  "prot_i"),
                  ("Carbs (g)",       "carb_i"), ("Fat (g)",      "fat_i"),
                  ("Fiber (g)",       "fiber_i"),("Category",     "cat_i")]
        for lbl_txt, attr in fields:
            layout.add_widget(section_lbl(lbl_txt))
            ti = text_input(lbl_txt)
            setattr(self, attr, ti)
            layout.add_widget(ti)

        self.err_lbl = lbl("", color=C_RED, halign="center", h=dp(24))
        layout.add_widget(self.err_lbl)

        save_btn = styled_btn("Save Food", bg=C_GREEN, height=dp(48))
        save_btn.bind(on_release=lambda *_: self._save())
        layout.add_widget(save_btn)
        layout.add_widget(spacer(dp(20)))

        outer.add_widget(sv)
        self.add_widget(outer)

    def _search(self):
        query = self.search_i.text.strip().lower()
        self.search_results.clear_widgets()
        if not query:
            return
        matches = [f for f in self._master if query in f["name"].lower()][:8]
        if not matches:
            self.search_results.add_widget(
                lbl("No results found.", color=C_GREY, h=dp(28)))
            return
        for food in matches:
            btn = Button(
                text=f'{food["name"]} ({food["type"]}) — {food["calories"]:.0f} kcal',
                font_size=dp(11), size_hint_y=None, height=dp(40),
                background_normal="", background_color=C_LIGHT_GREEN,
                color=C_TEXT)
            btn.bind(on_release=lambda *_, f=food: self._fill_from_master(f))
            self.search_results.add_widget(btn)

    def _fill_from_master(self, food):
        self.name_i.text  = food["name"]
        self.cal_i.text   = str(food["calories"])
        self.prot_i.text  = str(food["protein"])
        self.carb_i.text  = str(food["carbs"])
        self.fat_i.text   = str(food["fat"])
        self.fiber_i.text = str(food["fiber"])
        self.cat_i.text   = food["category"]
        self._selected_master = food
        self.search_results.clear_widgets()
        self.search_results.add_widget(
            lbl(f"Selected: {food['name']}", color=C_GREEN, h=dp(26)))

    def _save(self):
        name = self.name_i.text.strip()
        if not name:
            self.err_lbl.text = "Food name is required."
            return
        try:
            food = {
                "type":     self.get_type(),
                "name":     name,
                "calories": float(self.cal_i.text   or 0),
                "protein":  float(self.prot_i.text  or 0),
                "carbs":    float(self.carb_i.text  or 0),
                "fat":      float(self.fat_i.text   or 0),
                "fiber":    float(self.fiber_i.text or 0),
                "sugar":    0.0,
                "sodium":   0.0,
                "category": self.cat_i.text or "Custom",
            }
        except ValueError:
            self.err_lbl.text = "Please enter valid numeric values."
            return

        email = App.get_running_app().profile.get("email", "")
        save_user_food(food, email)
        show_popup("Saved", f'"{name}" saved to your food list!',
                   on_ok=self._back)

    def _back(self):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "dashboard"
