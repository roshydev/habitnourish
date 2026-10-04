# -*- coding: utf-8 -*-
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import Screen, SlideTransition

from db import save_master_food, master_food_exists, load_master_foods
from helpers import (C_GREEN, C_DARK_GREEN, C_RED, C_GREY, C_ORANGE,
                     C_TEXT, C_LIGHT_GREEN,
                     styled_btn, lbl, spacer, text_input,
                     section_lbl, scroll_layout, header_bar,
                     radio_group, show_popup)


class CustomFoodScreen(Screen):
    # numeric fields the user MUST fill in
    REQUIRED_NUM = [
        ("Calories (kcal)", "cal_i",   "calories"),
        ("Protein (g)",     "prot_i",  "protein"),
        ("Carbs (g)",       "carb_i",  "carbs"),
        ("Fat (g)",         "fat_i",   "fat"),
        ("Fiber (g)",       "fiber_i", "fiber"),
    ]

    def on_pre_enter(self):
        self.clear_widgets()
        self._master = load_master_foods()

        outer = BoxLayout(orientation="vertical")
        outer.add_widget(header_bar("Custom Food",
                                     back_cb=self._back, bg=C_DARK_GREEN))
        sv, layout = scroll_layout()

        layout.add_widget(section_lbl("Food Name"))
        self.name_i = text_input("Food name")
        self.name_i.bind(text=lambda *_: self._on_name_change())
        layout.add_widget(self.name_i)

        # Autocomplete suggestion list of existing foods containing the text
        self.suggest_box = BoxLayout(orientation="vertical",
                                     size_hint_y=None, height=0, spacing=dp(2))
        self.suggest_box.bind(minimum_height=self.suggest_box.setter("height"))
        layout.add_widget(self.suggest_box)

        # Live duplicate warning (exact match already in master sheet)
        self.dup_lbl = lbl("", color=C_ORANGE, size=dp(11), h=dp(22))
        layout.add_widget(self.dup_lbl)

        layout.add_widget(section_lbl("Meal Type"))
        type_box, self.get_type = radio_group(
            ["Breakfast", "Lunch", "Dinner", "Snacks"], "Snacks", "ftype")
        layout.add_widget(type_box)

        layout.add_widget(lbl("Nutrition values are per 100g. All fields below "
                              "are required.",
                               color=C_GREY, size=dp(10), h=dp(20)))

        # Required numeric fields (float-only input)
        for lbl_txt, attr, _key in self.REQUIRED_NUM:
            layout.add_widget(section_lbl(lbl_txt + "  *"))
            ti = TextInput(hint_text=lbl_txt, multiline=False,
                           input_filter="float",
                           size_hint_y=None, height=dp(44), font_size=dp(13))
            setattr(self, attr, ti)
            layout.add_widget(ti)

        # Optional category
        layout.add_widget(section_lbl("Category"))
        self.cat_i = text_input("Category (optional)")
        layout.add_widget(self.cat_i)

        self.err_lbl = lbl("", color=C_RED, halign="center", h=dp(24))
        layout.add_widget(self.err_lbl)

        save_btn = styled_btn("Save Food", bg=C_GREEN, height=dp(48))
        save_btn.bind(on_release=lambda *_: self._save())
        layout.add_widget(save_btn)
        layout.add_widget(spacer(dp(20)))

        outer.add_widget(sv)
        self.add_widget(outer)

    # ── Name field: autocomplete + duplicate warning ─────────────────────────
    def _on_name_change(self):
        self._render_suggestions()
        self._check_duplicate()

    def _render_suggestions(self):
        """Show existing foods whose name CONTAINS the typed text (Option A:
        helps the user see what already exists and avoid duplicates)."""
        self.suggest_box.clear_widgets()
        q = self.name_i.text.strip().lower()
        if not q:
            return
        matches = [f for f in self._master if q in f["name"].lower()]
        # don't show the dropdown if the only match is an exact one
        matches = [f for f in matches if f["name"].lower() != q][:6]
        if not matches:
            return
        for f in matches:
            row = Button(
                text=f'{f["name"]}  ({f["type"]}, {f["calories"]:.0f} kcal/100g)',
                font_size=dp(10), size_hint_y=None, height=dp(30),
                halign="left", valign="middle",
                background_normal="", background_color=C_LIGHT_GREEN,
                color=C_TEXT)
            row.bind(size=lambda o, v: setattr(o, "text_size", (o.width - dp(12), None)))
            # tapping a suggestion fills the name so the user sees it exists
            row.bind(on_release=lambda *_, nm=f["name"]: self._use_suggestion(nm))
            self.suggest_box.add_widget(row)

    def _use_suggestion(self, name):
        self.name_i.text = name
        self.suggest_box.clear_widgets()
        self._check_duplicate()

    def _check_duplicate(self):
        name = self.name_i.text.strip()
        if name and master_food_exists(name):
            self.dup_lbl.text = f'"{name}" already exists in the master sheet.'
        else:
            self.dup_lbl.text = ""

    # ── Save with mandatory-field validation ─────────────────────────────────
    def _save(self):
        name = self.name_i.text.strip()
        if not name:
            self.err_lbl.text = "Food name is required."
            return
        if master_food_exists(name):
            self.err_lbl.text = f'"{name}" already exists. Choose a different name.'
            return

        # all numeric fields are mandatory
        values = {}
        for lbl_txt, attr, key in self.REQUIRED_NUM:
            raw = getattr(self, attr).text.strip()
            if raw == "":
                self.err_lbl.text = f"{lbl_txt} is required."
                return
            try:
                values[key] = float(raw)
            except ValueError:
                self.err_lbl.text = f"{lbl_txt} must be a number."
                return

        food = {
            "type":     self.get_type(),
            "name":     name,
            "calories": values["calories"],
            "protein":  values["protein"],
            "carbs":    values["carbs"],
            "fat":      values["fat"],
            "fiber":    values["fiber"],
            "sugar":    0.0,
            "sodium":   0.0,
            "category": self.cat_i.text.strip() or "Custom",
        }

        ok, err = save_master_food(food)
        if not ok:
            self.err_lbl.text = err
            return
        show_popup("Saved to Master Sheet",
                   f'"{name}" added to the shared master sheet!',
                   on_ok=self._back)

    def _back(self):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "dashboard"
