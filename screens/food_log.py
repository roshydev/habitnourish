# -*- coding: utf-8 -*-
from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen, SlideTransition
from kivy.uix.textinput import TextInput

from datetime import date

from db import (today_log, today_totals, delete_log_entry, update_log_entry,
                log_plan_item, get_plan_for_range, delete_plan_entry,
                save_plan_entry)
from helpers import (C_GREEN, C_DARK_GREEN, C_BLUE, C_RED, C_ORANGE, C_GREY,
                     C_WHITE, C_TEXT, C_LIGHT_GREEN,
                     styled_btn, lbl, spacer, card_box,
                     scroll_layout, header_bar, confirm_popup)


class FoodLogScreen(Screen):
    MEALS_ORDER = ["Breakfast", "Lunch", "Dinner", "Snacks"]

    def on_pre_enter(self):
        self.clear_widgets()
        app = App.get_running_app()
        uid = app.user_id
        log = today_log(uid)

        today = date.today()
        planned = get_plan_for_range(uid, today, today)

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

        # ── PLANNED FOR TODAY (from the 7-Day Meal Plan, not yet logged) ──────
        if planned:
            plan_cal = sum(e["calories"] for e in planned)
            hdr = BoxLayout(orientation="horizontal",
                            size_hint_y=None, height=dp(30))
            hdr.add_widget(lbl("Planned for Today", bold=True, size=dp(14),
                               color=C_BLUE, h=dp(28)))
            hdr.add_widget(lbl(f"{int(plan_cal)} kcal", size=dp(11),
                               color=C_BLUE, halign="right", h=dp(28)))
            layout.add_widget(hdr)

            by_meal_plan = {m: [] for m in self.MEALS_ORDER}
            for e in planned:
                by_meal_plan.setdefault(e["meal"], []).append(e)

            for meal in self.MEALS_ORDER:
                entries = by_meal_plan.get(meal, [])
                if not entries:
                    continue
                layout.add_widget(lbl(f"  {meal}", bold=True, size=dp(11),
                                      color=C_DARK_GREEN, h=dp(22)))
                for e in entries:
                    layout.add_widget(self._planned_card(e))

            layout.add_widget(spacer(dp(10)))

        # ── LOGGED TODAY ─────────────────────────────────────────────────────
        logged_hdr = lbl("Logged Today", bold=True, size=dp(14),
                         color=C_DARK_GREEN, h=dp(28))
        layout.add_widget(logged_hdr)

        if not log:
            layout.add_widget(lbl("No food logged today.",
                                   color=C_GREY, halign="center", h=dp(40)))
        else:
            by_meal = {m: [] for m in self.MEALS_ORDER}
            for entry in log:
                by_meal.setdefault(entry["meal"], []).append(entry)

            for meal in self.MEALS_ORDER:
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
                    del_btn.bind(on_release=lambda *_, e=e: self._confirm_delete_log(e))
                    row.add_widget(del_btn)
                    layout.add_widget(row)

                layout.add_widget(spacer(dp(4)))

        layout.add_widget(spacer(dp(10)))
        add_btn = styled_btn("+ Add from Catalog", bg=C_GREEN, height=dp(46))
        add_btn.bind(on_release=lambda *_: self._go("diet_plan"))
        layout.add_widget(add_btn)
        layout.add_widget(spacer(dp(20)))

        outer.add_widget(sv)
        self.add_widget(outer)

    # ── Planned item card: Edit / Del / + Log It ─────────────────────────────
    def _planned_card(self, entry):
        row = card_box(height=dp(70))
        info = BoxLayout(orientation="vertical", spacing=dp(2))
        info.add_widget(lbl(
            f"{entry['food_name']}  ({int(entry['grams'])}g)",
            bold=True, size=dp(12), h=dp(22)))
        info.add_widget(lbl(
            f"{int(entry['calories'])} kcal  |  "
            f"P:{entry['protein']:.0f}g  C:{entry['carbs']:.0f}g  "
            f"F:{entry['fat']:.0f}g",
            size=dp(10), color=C_GREY, h=dp(18)))

        btns = BoxLayout(orientation="horizontal", size_hint=(None, 1),
                         width=dp(150), spacing=dp(4))
        edit_btn = styled_btn("Edit", bg=C_BLUE, height=dp(32), width=dp(42),
                              font_size=dp(10))
        edit_btn.bind(on_release=lambda *_, e=entry: self._edit_plan_popup(e))
        del_btn = styled_btn("Del", bg=C_RED, height=dp(32), width=dp(40),
                             font_size=dp(10))
        del_btn.bind(on_release=lambda *_, e=entry: self._confirm_delete_plan(e))
        log_btn = styled_btn("+ Log It", bg=C_GREEN, height=dp(32), width=dp(60),
                             font_size=dp(10))
        log_btn.bind(on_release=lambda *_, e=entry: self._log_planned(e))
        btns.add_widget(edit_btn)
        btns.add_widget(del_btn)
        btns.add_widget(log_btn)

        row.add_widget(info)
        row.add_widget(btns)
        return row

    def _log_planned(self, entry):
        """Move a planned item into today's actual food log.

        Adds it to the log (no re-scaling) and removes it from the plan so it
        appears only under 'Logged Today', not in both sections."""
        uid = App.get_running_app().user_id
        log_plan_item(uid, entry["meal"], entry)
        delete_plan_entry(entry["id"])
        self.on_pre_enter()

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

    # ── Delete with confirmation ─────────────────────────────────────────────
    def _confirm_delete_log(self, entry):
        confirm_popup(
            "Delete Entry",
            f"Delete \"{entry['food_name']} ({int(entry['grams'])}g)\" "
            f"from today's log?\nThis can't be undone.",
            on_confirm=lambda: self._delete_log(entry["id"]))

    def _delete_log(self, entry_id):
        delete_log_entry(entry_id)
        self.on_pre_enter()

    def _confirm_delete_plan(self, entry):
        confirm_popup(
            "Delete Planned Item",
            f"Remove \"{entry['food_name']} ({int(entry['grams'])}g)\" "
            f"from today's plan?\nThis can't be undone.",
            on_confirm=lambda: self._delete_plan(entry["id"]))

    def _delete_plan(self, entry_id):
        delete_plan_entry(entry_id)
        self.on_pre_enter()

    # ── Edit a PLANNED item (adjusts the plan entry's grams) ─────────────────
    def _edit_plan_popup(self, entry):
        from kivy.uix.popup import Popup as _Popup
        content = BoxLayout(orientation="vertical",
                            padding=dp(14), spacing=dp(10))
        content.add_widget(Label(
            text=f"{entry['food_name']}  (Planned)",
            font_size=dp(14), bold=True, color=C_BLUE,
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

        preview = Label(text=self._preview(entry, int(entry["grams"])),
                        font_size=dp(11), color=C_BLUE,
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

        popup = _Popup(title="Edit Planned Item", content=content,
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
            self._update_plan_grams(entry, g)
            popup.dismiss()
            self.on_pre_enter()

        ok_btn.bind(on_release=_save)
        popup.open()

    def _update_plan_grams(self, entry, new_grams):
        """Re-scale a planned entry to the new grams by deleting and re-adding.

        The meal_plan row stores absolute values, so we scale from the current
        grams, then persist via delete + save_plan_entry (which expects a
        per-100g food dict)."""
        old_g = entry["grams"] or 1
        per100 = {
            "name":     entry["food_name"],
            "calories": entry["calories"] / old_g * 100,
            "protein":  entry["protein"]  / old_g * 100,
            "carbs":    entry["carbs"]    / old_g * 100,
            "fat":      entry["fat"]      / old_g * 100,
            "fiber":    entry["fiber"]    / old_g * 100,
            "sugar":    0.0,
            "sodium":   0.0,
        }
        uid = App.get_running_app().user_id
        delete_plan_entry(entry["id"])
        save_plan_entry(uid, str(date.today()), entry["meal"], per100, new_grams)

    def _go(self, screen):
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = screen

    def _back(self):
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "dashboard"
