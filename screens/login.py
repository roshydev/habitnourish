# -*- coding: utf-8 -*-
from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, SlideTransition

from db import login_user, get_user_profile
from helpers import (C_GREEN, C_DARK_GREEN, C_WHITE, C_ORANGE,
                     styled_btn, spacer, text_input, show_popup)


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

        outer.add_widget(spacer(dp(60)))
        outer.add_widget(Label(text="HabitNourish", font_size=dp(34),
                                bold=True, color=C_WHITE,
                                size_hint_y=None, height=dp(50)))
        outer.add_widget(Label(text="Build Habits. Nourish Life.",
                                font_size=dp(13), color=(1, 1, 1, 0.8),
                                size_hint_y=None, height=dp(30)))
        outer.add_widget(spacer(dp(30)))

        form = BoxLayout(orientation="vertical", padding=dp(24),
                         spacing=dp(12), size_hint_y=None, height=dp(320))
        self.id_input = text_input("Email or Mobile Number")
        self.pw_input = text_input("Password", password=True)
        self.err_lbl  = Label(text="", font_size=dp(13), color=C_ORANGE,
                               halign="center", size_hint_y=None, height=dp(24))

        btn_login = styled_btn("Login", bg=C_GREEN, height=dp(48))
        btn_login.bind(on_release=lambda *_: self._login())

        btn_reg = styled_btn("Register New Account", bg=(0.2, 0.6, 0.86, 1),
                              height=dp(44))
        btn_reg.bind(on_release=lambda *_: self._go("register"))

        btn_reset = styled_btn("Forgot Password?", bg=(0.62, 0.62, 0.62, 1),
                                height=dp(38), font_size=dp(12))
        btn_reset.bind(on_release=lambda *_: self._go("reset_pw"))

        for w in [self.id_input, self.pw_input, self.err_lbl,
                  btn_login, btn_reg, btn_reset]:
            form.add_widget(w)

        outer.add_widget(form)
        self.add_widget(outer)

    def _login(self):
        row = login_user(self.id_input.text, self.pw_input.text)
        if row:
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
