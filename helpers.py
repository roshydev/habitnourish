# -*- coding: utf-8 -*-
"""
helpers.py – Shared UI helpers, constants and palette for HabitNourish.
"""

from kivy.app import App
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import SlideTransition
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.widget import Widget

# ── Palette ──────────────────────────────────────────────────────────────────
C_GREEN       = (0.298, 0.686, 0.314, 1)
C_DARK_GREEN  = (0.180, 0.490, 0.196, 1)
C_LIGHT_GREEN = (0.506, 0.780, 0.518, 1)
C_ORANGE      = (1.000, 0.596, 0.000, 1)
C_RED         = (0.957, 0.263, 0.212, 1)
C_BLUE        = (0.129, 0.588, 0.953, 1)
C_WHITE       = (1, 1, 1, 1)
C_BG          = (0.945, 0.973, 0.914, 1)
C_GREY        = (0.620, 0.620, 0.620, 1)
C_TEXT        = (0.130, 0.130, 0.130, 1)
C_CARD        = (0.980, 0.995, 0.975, 1)


# ── Widgets ───────────────────────────────────────────────────────────────────
def styled_btn(text, bg=C_GREEN, color=C_WHITE, height=dp(44),
               width=None, font_size=dp(13)):
    sh = (None, None) if width else (1, None)
    sz = (width or dp(100), height)
    b = Button(text=text, size_hint=sh, size=sz,
               background_normal="", background_color=bg,
               color=color, font_size=font_size, bold=True)
    return b

def card_box(height=dp(80), bg=C_CARD, padding=dp(10), spacing=dp(6)):
    w = BoxLayout(orientation="horizontal", size_hint_y=None,
                  height=height, padding=padding, spacing=spacing)
    with w.canvas.before:
        Color(*bg)
        w._rect = RoundedRectangle(pos=w.pos, size=w.size, radius=[dp(10)])
    w.bind(pos=lambda o, v: setattr(o._rect, "pos", v),
           size=lambda o, v: setattr(o._rect, "size", v))
    return w

def darken(color, factor=0.75):
    """Return a darker shade of an RGBA color (keeps alpha)."""
    r, g, b = color[0], color[1], color[2]
    a = color[3] if len(color) > 3 else 1
    return (r * factor, g * factor, b * factor, a)

def header_bar(title, back_cb=None, bg=C_GREEN, right_btn=None):
    bar = BoxLayout(orientation="horizontal", size_hint_y=None,
                    height=dp(56), padding=dp(8), spacing=dp(6))
    with bar.canvas.before:
        Color(*bg)
        bar._rect = Rectangle(pos=bar.pos, size=bar.size)
    bar.bind(pos=lambda o, v: setattr(o._rect, "pos", v),
             size=lambda o, v: setattr(o._rect, "size", v))
    if back_cb:
        # Home button themed to the header: a darker shade of the header color
        b = styled_btn("Home", bg=darken(bg), height=dp(38), width=dp(68))
        b.bind(on_release=lambda *_: back_cb())
        bar.add_widget(b)
    bar.add_widget(Label(text=title, color=C_WHITE, font_size=dp(15),
                         bold=True, halign="left", valign="middle"))
    if right_btn:
        bar.add_widget(right_btn)
    return bar

def lbl(text, size=dp(13), color=C_TEXT, bold=False,
        halign="left", h=dp(26), wrap=True):
    l = Label(text=text, font_size=size, color=color, bold=bold,
              halign=halign, valign="middle",
              size_hint_y=None, height=h)
    if wrap:
        l.bind(size=lambda o, v: setattr(o, "text_size", v))
    return l

def spacer(h=dp(10)):
    return Widget(size_hint_y=None, height=h)

def scroll_layout(padding=dp(14), spacing=dp(10)):
    sv = ScrollView(size_hint=(1, 1))
    inner = BoxLayout(orientation="vertical", size_hint_y=None,
                      padding=padding, spacing=spacing)
    inner.bind(minimum_height=inner.setter("height"))
    sv.add_widget(inner)
    return sv, inner

def text_input(hint, password=False, height=dp(44)):
    return TextInput(hint_text=hint, multiline=False,
                     password=password,
                     size_hint_y=None, height=height,
                     font_size=dp(13))

def section_lbl(text):
    return lbl(text, size=dp(14), bold=True, color=C_DARK_GREEN, h=dp(32))

def radio_group(options, default, group_name):
    container = BoxLayout(orientation="vertical",
                          size_hint_y=None, spacing=dp(2))
    container.bind(minimum_height=container.setter("height"))
    buttons = []
    for opt in options:
        tb = ToggleButton(text=opt, group=group_name,
                          state="down" if opt == default else "normal",
                          size_hint_y=None, height=dp(38),
                          background_normal="", background_down="",
                          background_color=C_LIGHT_GREEN if opt == default
                          else (0.88, 0.88, 0.88, 1),
                          color=C_TEXT, font_size=dp(12))
        def _toggle(btn, val, b=tb):
            b.background_color = C_LIGHT_GREEN if val == "down" \
                else (0.88, 0.88, 0.88, 1)
        tb.bind(state=_toggle)
        buttons.append((opt, tb))
        container.add_widget(tb)

    def getter():
        for opt, tb in buttons:
            if tb.state == "down":
                return opt
        return default

    return container, getter

def show_popup(title, message, on_ok=None):
    content = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
    content.add_widget(Label(text=message, halign="center",
                              font_size=dp(13), color=C_TEXT))
    btn = styled_btn("OK", bg=C_GREEN, height=dp(40))
    content.add_widget(btn)
    p = Popup(title=title, content=content,
              size_hint=(0.85, None), height=dp(220),
              auto_dismiss=True)
    def _ok(*_):
        p.dismiss()
        if on_ok:
            on_ok()
    btn.bind(on_release=_ok)
    p.open()

def confirm_popup(title, message, on_confirm,
                  confirm_text="Delete", confirm_bg=None):
    """Ask the user to confirm a destructive action.

    Shows [Cancel] [confirm_text]. Runs on_confirm() only if confirmed.
    """
    if confirm_bg is None:
        confirm_bg = (0.957, 0.263, 0.212, 1)  # C_RED
    content = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(12))
    content.add_widget(Label(text=message, halign="center", valign="middle",
                              font_size=dp(13), color=C_TEXT))
    btn_row = BoxLayout(orientation="horizontal", size_hint_y=None,
                        height=dp(44), spacing=dp(10))
    cancel_btn  = styled_btn("Cancel", bg=(0.62, 0.62, 0.62, 1), height=dp(42))
    confirm_btn = styled_btn(confirm_text, bg=confirm_bg, height=dp(42))
    btn_row.add_widget(cancel_btn)
    btn_row.add_widget(confirm_btn)
    content.add_widget(btn_row)
    p = Popup(title=title, content=content,
              size_hint=(0.85, None), height=dp(220),
              auto_dismiss=True)
    cancel_btn.bind(on_release=lambda *_: p.dismiss())
    def _confirm(*_):
        p.dismiss()
        on_confirm()
    confirm_btn.bind(on_release=_confirm)
    p.open()

def go_screen(manager, screen, direction="left"):
    manager.transition = SlideTransition(direction=direction)
    manager.current = screen
