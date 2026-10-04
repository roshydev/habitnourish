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
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, RoundedRectangle

from db import (get_plan_for_range, save_plan_entry, delete_plan_entry,
                get_all_foods, foods_by_type, scale_nutrients)
from helpers import (C_GREEN, C_DARK_GREEN, C_LIGHT_GREEN, C_BLUE, C_RED,
                     C_GREY, C_TEXT, C_WHITE, C_CARD,
                     styled_btn, lbl, spacer, card_box,
                     scroll_layout, header_bar, confirm_popup)


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
                        del_btn.bind(on_release=lambda *_, ent=e:
                                     self._confirm_delete(ent))
                        row.add_widget(del_btn)
                        self._layout.add_widget(row)

        self._layout.add_widget(spacer(dp(20)))

    def _add_popup(self, plan_date):
        content = BoxLayout(orientation="vertical",
                            padding=dp(12), spacing=dp(6))
        d_label = datetime.strptime(plan_date, "%Y-%m-%d").strftime("%A, %d %b")
        content.add_widget(Label(text=f"Add food for {d_label}",
                                  font_size=dp(13), bold=True, color=C_TEXT,
                                  size_hint_y=None, height=dp(24)))

        # ── Meal type selector ───────────────────────────────────────────────
        self._plan_meal_var      = "Breakfast"
        self._plan_selected_food = None
        self._plan_food_cards    = {}   # food name -> card widget (for highlight)

        meal_row = BoxLayout(orientation="horizontal",
                              size_hint_y=None, height=dp(36), spacing=dp(4))
        for m in ["Breakfast", "Lunch", "Dinner", "Snacks"]:
            mb = ToggleButton(text=m, group="plan_meal",
                               state="down" if m == "Breakfast" else "normal",
                               size_hint=(1, None), height=dp(34),
                               background_normal="", background_down="",
                               background_color=C_LIGHT_GREEN if m == "Breakfast"
                               else (0.85, 0.85, 0.85, 1),
                               color=C_TEXT, font_size=dp(10), bold=True)

            def _mt(btn, val, b=mb, meal=m):
                b.background_color = C_LIGHT_GREEN if val == "down" \
                    else (0.85, 0.85, 0.85, 1)
                if val == "down":
                    self._plan_meal_var = meal
                    self._render_plan_food_list()
            mb.bind(state=_mt)
            meal_row.add_widget(mb)
        content.add_widget(meal_row)

        # ── Live search filter ───────────────────────────────────────────────
        search_ti = TextInput(hint_text="Filter foods (optional)...",
                              multiline=False, font_size=dp(12),
                              size_hint=(1, None), height=dp(36))
        content.add_widget(search_ti)

        # ── Scrollable browsable food list ───────────────────────────────────
        food_sv = ScrollView(size_hint=(1, 1))
        food_layout = BoxLayout(orientation="vertical", size_hint_y=None,
                                spacing=dp(4), padding=(0, dp(2)))
        food_layout.bind(minimum_height=food_layout.setter("height"))
        food_sv.add_widget(food_layout)
        content.add_widget(food_sv)

        def _food_card(food):
            card = BoxLayout(orientation="horizontal", size_hint_y=None,
                             height=dp(50), padding=dp(10), spacing=dp(6))
            # own canvas with a tracked Color so we can highlight on select
            with card.canvas.before:
                card._color = Color(*C_CARD)
                card._rect = RoundedRectangle(pos=card.pos, size=card.size,
                                              radius=[dp(10)])
            card.bind(pos=lambda o, v: setattr(o._rect, "pos", v),
                      size=lambda o, v: setattr(o._rect, "size", v))

            info = BoxLayout(orientation="vertical", spacing=dp(1))
            info.add_widget(lbl(food["name"], bold=True, size=dp(12), h=dp(22)))
            info.add_widget(lbl(
                f'Per 100g: {food["calories"]:.0f} kcal  |  '
                f'P:{food["protein"]:.1f}g  C:{food["carbs"]:.1f}g  '
                f'F:{food["fat"]:.1f}g',
                size=dp(9), color=C_GREY, h=dp(16)))
            card.add_widget(info)

            def _pick(f=food, c=card):
                self._plan_selected_food = f
                # reset all card backgrounds, highlight the picked one
                for cc in self._plan_food_cards.values():
                    cc._color.rgba = C_CARD
                c._color.rgba = C_LIGHT_GREEN
                _update_preview()

            # make the whole card tappable
            def _on_touch(w, t, f=food, c=card):
                if w.collide_point(*t.pos):
                    _pick(f=f, c=c)
                    return True
                return False
            card.bind(on_touch_down=_on_touch)
            self._plan_food_cards[food["name"]] = card
            return card

        def _render_plan_food_list(*_):
            food_layout.clear_widgets()
            self._plan_food_cards = {}
            q = search_ti.text.strip().lower()
            items = foods_by_type(self._plan_meal_var, self._email)
            if q:
                items = [f for f in items if q in f["name"].lower()]
            items = sorted(items, key=lambda f: f["name"].lower())
            if not items:
                food_layout.add_widget(lbl(
                    "No foods match your filter." if q
                    else f"No {self._plan_meal_var} foods available.",
                    color=C_GREY, halign="center", h=dp(40)))
                return
            food_layout.add_widget(lbl(
                f"{len(items)} food(s) - tap to select",
                size=dp(10), color=C_GREY, h=dp(20)))
            for f in items:
                food_layout.add_widget(_food_card(f))

        # expose so meal-tab callback can refresh the list
        self._render_plan_food_list = _render_plan_food_list
        search_ti.bind(text=lambda *_: _render_plan_food_list())

        # ── Grams + live nutrient preview ────────────────────────────────────
        g_row = BoxLayout(orientation="horizontal",
                           size_hint_y=None, height=dp(36), spacing=dp(6))
        g_row.add_widget(Label(text="Grams:", font_size=dp(12), color=C_GREY,
                                size_hint=(0.35, None), height=dp(34)))
        grams_ti = TextInput(text="100", multiline=False, input_filter="float",
                              size_hint=(0.65, None), height=dp(34),
                              font_size=dp(12))
        g_row.add_widget(grams_ti)
        content.add_widget(g_row)

        preview_l = Label(text="Select a food to see nutrition",
                          font_size=dp(11), color=C_DARK_GREEN, bold=True,
                          size_hint_y=None, height=dp(22))
        content.add_widget(preview_l)

        def _update_preview(*_):
            f = self._plan_selected_food
            if not f:
                preview_l.text = "Select a food to see nutrition"
                return
            try:
                g = float(grams_ti.text)
            except ValueError:
                preview_l.text = f"Selected: {f['name']}  (enter grams)"
                return
            s = scale_nutrients(f, g)
            preview_l.text = (f"{f['name']} @ {g:.0f}g:  {s['calories']:.0f} kcal  "
                              f"P:{s['protein']:.1f}g  C:{s['carbs']:.1f}g  "
                              f"F:{s['fat']:.1f}g")
        grams_ti.bind(text=_update_preview)

        err_l = Label(text="", color=C_RED, font_size=dp(11),
                       size_hint_y=None, height=dp(18))
        content.add_widget(err_l)

        # ── Action buttons ───────────────────────────────────────────────────
        btn_row = BoxLayout(orientation="horizontal",
                             size_hint_y=None, height=dp(42), spacing=dp(8))
        ok_btn  = styled_btn("Add to Plan", bg=C_GREEN, height=dp(40))
        can_btn = styled_btn("Cancel",      bg=C_GREY,  height=dp(40))
        btn_row.add_widget(ok_btn)
        btn_row.add_widget(can_btn)
        content.add_widget(btn_row)

        popup = Popup(title="Add to Meal Plan", content=content,
                      size_hint=(0.95, 0.9))
        can_btn.bind(on_release=popup.dismiss)

        def _ok(*_):
            if not self._plan_selected_food:
                err_l.text = "Please tap a food to select it first."
                return
            try:
                g = float(grams_ti.text)
            except ValueError:
                err_l.text = "Enter a valid gram value."
                return
            if g <= 0:
                err_l.text = "Grams must be greater than 0."
                return
            save_plan_entry(self._uid, plan_date,
                            self._plan_meal_var,
                            self._plan_selected_food, g)
            popup.dismiss()
            self._render_plan()

        ok_btn.bind(on_release=_ok)

        # initial render of the full Breakfast list
        _render_plan_food_list()
        popup.open()

    def _confirm_delete(self, entry):
        confirm_popup(
            "Delete Planned Item",
            f"Remove \"{entry['food_name']} ({int(entry['grams'])}g)\" "
            f"from this day's plan?\nThis can't be undone.",
            on_confirm=lambda: self._delete(entry["id"]))

    def _delete(self, entry_id):
        delete_plan_entry(entry_id)
        self._render_plan()

    def _back(self):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "dashboard"
