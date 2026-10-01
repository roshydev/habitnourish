# -*- coding: utf-8 -*-
from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen, SlideTransition
from kivy.uix.textinput import TextInput

from db import today_log, today_totals, delete_log_entry, update_log_entry
from helpers import (C_GREEN, C_DARK_GREEN, C_BLUE, C_RED, C_ORANGE, C_GREY,
                     styled_btn, lbl, spacer, card_box,
                     scroll_layout, header_bar)


class FoodLogScreen(Screen):
    def on_pre_enter(self):
        self.clear_widgets()
        app = App.get_running_app()
        uid = app.user_id
        log = today_log(uid)

        outer = BoxLayout(orientation="vertical")
        outer.add_widget(header_bar("Today's Food Log",
                                     back_cb=self._back, bg=C_ORANGE))

        t = today_totals(uid)
        outer.add_widget(lbl(
            f"  Total: {int(t['calories'])} kcal  |  "
            f"P:{t['protein']:.0f}g  C:{t['carbs']:.0f}g  "
            f"F:{t['fat']:.0f}g  Fiber:{t['fiber']:.0f}g",
            size=dp(11), color=C_DARK_GREEN, h=dp(24)))

        sv, layout = scroll_layout(padding=dp(10), spacing=dp(8))

        if not log:
            layout.add_widget(spacer(dp(16)))
            layout.add_widget(lbl("No food logged today.",
                                   color=C_GREY, halign="center", h=dp(40)))
        else:
            meals_order = ["Breakfast", "Lunch", "Dinner", "Snacks"]
            by_meal = {m: [] for m in meals_order}
            for entry in log:
                by_meal.setdefault(entry["meal"], []).append(entry)

            for meal in meals_order:
                entries = by_meal.get(meal, [])
                if not entries:
                    continue

                meal_cal = sum(e["calories"] for e in entries)
                meal_hdr = BoxLayout(orientation="horizontal",
                                      size_hint_y=None, height=dp(28))
                meal_hdr.add_widget(lbl(meal, bold=True, size=dp(13),
                                         color=C_DARK_GREEN, h=dp(26)))
                meal_hdr.add_widget(lbl(f"{int(meal_cal)} kcal",
                                         size=dp(11), color=C_ORANGE,
                                         halign="right", h=dp(26)))
                layout.add_widget(meal_hdr)

                for e in entries:
                    row = card_box(height=dp(58))
                    info = BoxLayout(orientation="vertical", spacing=dp(2))
                    info.add_widget(lbl(
                        f"{e['food_name']}  ({int(e['grams'])}g)",
                        bold=True, size=dp(12), h=dp(24)))
                    info.add_widget(lbl(
                        f"{int(e['calories'])} kcal  |  "
                        f"P:{e['protein']:.0f}g  C:{e['carbs']:.0f}g  "
                        f"F:{e['fat']:.0f}g",
                        size=dp(10), color=C_GREY, h=dp(20)))
                    row.add_widget(info)

                    edit_btn = styled_btn("Edit", bg=C_BLUE,
                                          height=dp(36), width=dp(46),
                                          font_size=dp(11))
                    edit_btn.bind(on_release=lambda *_, entry=e: self._edit_popup(entry))
                    row.add_widget(edit_btn)

                    del_btn = styled_btn("Del", bg=C_RED,
                                         height=dp(36), width=dp(44),
                                         font_size=dp(11))
                    del_btn.bind(on_release=lambda *_, eid=e["id"]: self._delete(eid))
                    row.add_widget(del_btn)
                    layout.add_widget(row)

                layout.add_widget(spacer(dp(4)))

        layout.add_widget(spacer(dp(10)))
        add_btn = styled_btn("+ Add More Food", bg=C_GREEN, height=dp(46))
        add_btn.bind(on_release=lambda *_: self._go("diet_plan"))
        layout.add_widget(add_btn)
        layout.add_widget(spacer(dp(20)))

        outer.add_widget(sv)
        self.add_widget(outer)

    def _edit_popup(self, entry):
        content = BoxLayout(orientation="vertical",
                            padding=dp(14), spacing=dp(10))
        content.add_widget(Label(
            text=f"{entry['food_name']}",
            font_size=dp(14), bold=True, color=C_DARK_GREEN,
            halign="center", size_hint_y=None, height=dp(30)))
        content.add_widget(Label(
            text=f"Current: {int(entry['grams'])}g  →  "
                 f"{int(entry['calories'])} kcal  |  "
                 f"P:{entry['protein']:.0f}g  C:{entry['carbs']:.0f}g",
            font_size=dp(11), color=C_GREY,
            halign="center", size_hint_y=None, height=dp(24)))
        content.add_widget(Label(text="New serving size (grams):",
                                  font_size=dp(12), color=C_DARK_GREEN,
                                  size_hint_y=None, height=dp(24)))
        grams_i = TextInput(text=str(int(entry["grams"])),
                             multiline=False, input_filter="float",
                             size_hint_y=None, height=dp(42))
        content.add_widget(grams_i)

        preview = Label(
            text=self._preview(entry, int(entry["grams"])),
            font_size=dp(11), color=C_DARK_GREEN,
            halign="center", size_hint_y=None, height=dp(24))
        content.add_widget(preview)

        def _upd(*_):
            try:
                preview.text = self._preview(entry, float(grams_i.text))
            except ValueError:
                preview.text = ""
        grams_i.bind(text=_upd)

        err_l = Label(text="", color=C_RED, font_size=dp(11),
                       size_hint_y=None, height=dp(20))
        content.add_widget(err_l)

        btn_row = BoxLayout(orientation="horizontal",
                             size_hint_y=None, height=dp(44), spacing=dp(10))
        ok_btn  = styled_btn("Save",   bg=C_GREEN, height=dp(40))
        can_btn = styled_btn("Cancel", bg=C_GREY,  height=dp(40))
        btn_row.add_widget(ok_btn)
        btn_row.add_widget(can_btn)
        content.add_widget(btn_row)

        popup = Popup(title="Edit Entry", content=content,
                      size_hint=(0.90, None), height=dp(340))
        can_btn.bind(on_release=popup.dismiss)

        def _save(*_):
            try:
                g = float(grams_i.text)
                if g <= 0:
                    raise ValueError
            except ValueError:
                err_l.text = "Enter a valid positive gram value."
                return
            update_log_entry(entry["id"], g)
            popup.dismiss()
            self.on_pre_enter()

        ok_btn.bind(on_release=_save)
        popup.open()

    @staticmethod
    def _preview(entry, grams):
        if not entry["grams"]:
            return ""
        f   = grams / entry["grams"]
        cal = entry["calories"] * f
        pro = entry["protein"]  * f
        crb = entry["carbs"]    * f
        fat = entry["fat"]      * f
        return (f"→  {cal:.0f} kcal  |  "
                f"P:{pro:.1f}g  C:{crb:.1f}g  F:{fat:.1f}g")

    def _delete(self, entry_id):
        delete_log_entry(entry_id)
        self.on_pre_enter()

    def _go(self, screen):
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = screen

    def _back(self):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "dashboard"
