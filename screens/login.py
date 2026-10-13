# -*- coding: utf-8 -*-
import os

from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.checkbox import CheckBox
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, SlideTransition
from kivy.uix.widget import Widget

from db import (login_user, get_user_profile,
                load_remembered_login, save_remembered_login,
                clear_remembered_login)
from helpers import (C_GREEN, C_DARK_GREEN, C_WHITE, C_ORANGE,
                     styled_btn, spacer, text_input)


def _logo_path():
    """Return the first existing logo file path, or None if none is bundled."""
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for candidate in (
        os.path.join(here, "assets", "logo.png"),
        os.path.join(here, "logo.png"),
        os.path.join(here, "Logo.jpeg"),
        os.path.join(here, "logo.jpeg"),
        os.path.join(here, "logo.jpg"),
    ):
        if os.path.exists(candidate):
            return candidate
    return None


class LoginScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        from kivy.graphics import Color, Rectangle

        outer = BoxLayout(orientation="vertical")
        with outer.canvas.before:
            Color(*C_DARK_GREEN)
            outer._bg = Rectangle(pos=outer.pos, size=outer.size)
        outer.bind(pos=lambda o, v: setattr(o._bg, "pos", v),
                   size=lambda o, v: setattr(o._bg, "size", v))

        # Fixed top gap — keeps content near the top so the on-screen keyboard
        # does not cover the fields when they are focused. Large enough that the
        # logo clears the status bar / screen edge.
        outer.add_widget(spacer(dp(50)))

        # ── Branding: logo image if present, else text title ─────────────────
        logo = _logo_path()
        if logo:
            # The logo artwork has a light background, so sit it on a rounded
            # white card to blend cleanly against the dark-green screen.
            # The card is a bit wider than tall and the image keeps its ratio,
            # so the full "Habit Nourish" artwork is visible without clipping.
            from kivy.graphics import RoundedRectangle
            # Square card to match the square logo artwork so nothing clips.
            CARD_W, CARD_H = dp(150), dp(150)
            card = BoxLayout(size_hint=(None, None), size=(CARD_W, CARD_H),
                             padding=dp(10))
            with card.canvas.before:
                Color(1, 1, 1, 1)
                card._card = RoundedRectangle(pos=card.pos, size=card.size,
                                              radius=[dp(20)])
            card.bind(pos=lambda o, v: setattr(o._card, "pos", v),
                      size=lambda o, v: setattr(o._card, "size", v))
            card.add_widget(Image(source=logo, allow_stretch=True,
                                  keep_ratio=True))
            # Center the fixed-size card horizontally
            card_row = BoxLayout(size_hint_y=None, height=CARD_H)
            card_row.add_widget(Widget())  # flexible left pad
            card_row.add_widget(card)
            card_row.add_widget(Widget())  # flexible right pad
            outer.add_widget(card_row)
        else:
            outer.add_widget(Label(text="HabitNourish", font_size=dp(30),
                                    bold=True, color=C_WHITE,
                                    size_hint_y=None, height=dp(46)))
            outer.add_widget(Label(text="Build Habits. Nourish Life.",
                                    font_size=dp(13), color=(1, 1, 1, 0.8),
                                    size_hint_y=None, height=dp(28)))

        # Clear gap between the logo card and the first input field so the
        # full logo (including the "Nourish" wordmark) is never overlapped,
        # and the fields sit a comfortable distance below.
        outer.add_widget(spacer(dp(90)))

        # ── Login form ────────────────────────────────────────────────────────
        form = BoxLayout(orientation="vertical", padding=dp(24),
                         spacing=dp(10), size_hint_y=None, height=dp(300))
        self.id_input = text_input("Email or Mobile Number")
        self.pw_input = text_input("Password", password=True)

        # Remember-me row
        remember_row = BoxLayout(orientation="horizontal", size_hint_y=None,
                                 height=dp(30), spacing=dp(6))
        self.remember_cb = CheckBox(size_hint=(None, 1), width=dp(30))
        remember_row.add_widget(self.remember_cb)
        remember_row.add_widget(Label(text="Remember me on this device",
                                      font_size=dp(12), color=C_WHITE,
                                      halign="left", valign="middle",
                                      text_size=(None, None)))

        self.err_lbl  = Label(text="", font_size=dp(13), color=C_ORANGE,
                               halign="center", size_hint_y=None, height=dp(22))

        btn_login = styled_btn("Login", bg=C_GREEN, height=dp(48))
        btn_login.bind(on_release=lambda *_: self._login())

        btn_reg = styled_btn("Register New Account", bg=(0.2, 0.6, 0.86, 1),
                              height=dp(44))
        btn_reg.bind(on_release=lambda *_: self._go("register"))

        btn_reset = styled_btn("Forgot Password?", bg=(0.62, 0.62, 0.62, 1),
                                height=dp(36), font_size=dp(12))
        btn_reset.bind(on_release=lambda *_: self._go("reset_pw"))

        for w in [self.id_input, self.pw_input, remember_row, self.err_lbl,
                  btn_login, btn_reg, btn_reset]:
            form.add_widget(w)

        outer.add_widget(form)
        # Flexible bottom spacer absorbs the remaining height so the logo and
        # form stay anchored near the top (clear of the on-screen keyboard).
        outer.add_widget(Widget(size_hint_y=1))

        self.add_widget(outer)

        # Pre-fill saved credentials if the user chose "remember me" before
        ident, pw = load_remembered_login()
        if ident:
            self.id_input.text = ident
            self.pw_input.text = pw or ""
            self.remember_cb.active = True

    def _login(self):
        row = login_user(self.id_input.text, self.pw_input.text)
        if row:
            if self.remember_cb.active:
                save_remembered_login(self.id_input.text, self.pw_input.text)
            else:
                clear_remembered_login()
            app = App.get_running_app()
            app.user_id   = row[0]
            app.user_name = row[1]
            p = get_user_profile(row[0])
            if not p.get("age"):
                self._go("profile")
            else:
                app.profile = p
                self._go("dashboard")
        else:
            self.err_lbl.text = "Invalid credentials. Please try again."

    def _go(self, screen):
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = screen
