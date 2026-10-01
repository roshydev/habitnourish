# -*- coding: utf-8 -*-
from kivy.app import App
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen, SlideTransition

from db import register_user
from helpers import (C_GREEN, C_RED, C_DARK_GREEN,
                     styled_btn, lbl, spacer, text_input,
                     section_lbl, scroll_layout, header_bar, show_popup)


class RegisterScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        from kivy.uix.boxlayout import BoxLayout
        outer = BoxLayout(orientation="vertical")
        outer.add_widget(header_bar("Create Account",
                                     back_cb=lambda: self._go("login"),
                                     bg=C_DARK_GREEN))
        sv, layout = scroll_layout()

        self.name_i   = text_input("Full Name")
        self.email_i  = text_input("Email Address")
        self.mobile_i = text_input("Mobile Number")
        self.pw_i     = text_input("Password (min 6 chars)", password=True)
        self.pw2_i    = text_input("Confirm Password", password=True)
        self.err_lbl  = lbl("", color=C_RED, halign="center", h=dp(24))

        for hint, w in [("Full Name",        self.name_i),
                        ("Email",            self.email_i),
                        ("Mobile",           self.mobile_i),
                        ("Password",         self.pw_i),
                        ("Confirm Password", self.pw2_i)]:
            layout.add_widget(section_lbl(hint))
            layout.add_widget(w)

        layout.add_widget(self.err_lbl)
        btn = styled_btn("Register", bg=C_GREEN, height=dp(48))
        btn.bind(on_release=lambda *_: self._register())
        layout.add_widget(btn)
        outer.add_widget(sv)
        self.add_widget(outer)

    def _register(self):
        name   = self.name_i.text.strip()
        email  = self.email_i.text.strip()
        mobile = self.mobile_i.text.strip()
        pw     = self.pw_i.text
        pw2    = self.pw2_i.text

        if not name or not pw:
            self.err_lbl.text = "Name and password are required."
            return
        if not email and not mobile:
            self.err_lbl.text = "Email or mobile is required."
            return
        if pw != pw2:
            self.err_lbl.text = "Passwords do not match."
            return
        if len(pw) < 6:
            self.err_lbl.text = "Password must be at least 6 characters."
            return

        uid, err = register_user(email, mobile, pw, name)
        if err:
            self.err_lbl.text = err
        else:
            app = App.get_running_app()
            app.user_id   = uid
            app.user_name = name
            show_popup("Success", "Account created! Set up your profile.",
                       on_ok=lambda: self._go("profile"))

    def _go(self, screen):
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = screen
