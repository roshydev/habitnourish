# -*- coding: utf-8 -*-
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen, SlideTransition

from db import set_reset_token, reset_password
from helpers import (C_GREEN, C_RED, C_DARK_GREEN,
                     styled_btn, lbl, text_input,
                     section_lbl, scroll_layout, header_bar, show_popup)


class ResetPwScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        from kivy.uix.boxlayout import BoxLayout
        self.step = 1
        outer = BoxLayout(orientation="vertical")
        outer.add_widget(header_bar("Reset Password",
                                     back_cb=lambda: self._go("login"),
                                     bg=C_DARK_GREEN))
        sv, self.layout = scroll_layout()
        self._build_step1()
        outer.add_widget(sv)
        self.add_widget(outer)

    def _build_step1(self):
        self.layout.clear_widgets()
        self.layout.add_widget(lbl(
            "Enter your registered Email or Mobile to receive a reset token.",
            h=dp(48), color=(0.62, 0.62, 0.62, 1)))
        self.id_i  = text_input("Email or Mobile")
        self.err_l = lbl("", color=C_RED, h=dp(24))
        btn = styled_btn("Send Reset Token", bg=C_GREEN, height=dp(46))
        btn.bind(on_release=lambda *_: self._send_token())
        for w in [self.id_i, self.err_l, btn]:
            self.layout.add_widget(w)

    def _send_token(self):
        identifier = self.id_i.text.strip()
        if not identifier:
            self.err_l.text = "Please enter email or mobile."
            return
        import random, string
        token = "".join(random.choices(string.digits, k=6))
        set_reset_token(identifier, token)
        self._identifier = identifier
        show_popup("Token Sent",
                   f"Your reset token is: {token}\n(In production this is sent via SMS/Email)",
                   on_ok=lambda: self._build_step2())

    def _build_step2(self):
        self.layout.clear_widgets()
        self.layout.add_widget(section_lbl("Enter Reset Token"))
        self.token_i = text_input("6-digit token")
        self.layout.add_widget(self.token_i)
        self.layout.add_widget(section_lbl("New Password"))
        self.new_pw_i = text_input("New Password", password=True)
        self.layout.add_widget(self.new_pw_i)
        self.layout.add_widget(section_lbl("Confirm New Password"))
        self.new_pw2_i = text_input("Confirm Password", password=True)
        self.layout.add_widget(self.new_pw2_i)
        self.err_l2 = lbl("", color=C_RED, h=dp(24))
        self.layout.add_widget(self.err_l2)
        btn = styled_btn("Reset Password", bg=C_GREEN, height=dp(46))
        btn.bind(on_release=lambda *_: self._do_reset())
        self.layout.add_widget(btn)

    def _do_reset(self):
        token   = self.token_i.text.strip()
        new_pw  = self.new_pw_i.text
        new_pw2 = self.new_pw2_i.text
        if new_pw != new_pw2:
            self.err_l2.text = "Passwords do not match."
            return
        if len(new_pw) < 6:
            self.err_l2.text = "Password must be at least 6 characters."
            return
        if reset_password(self._identifier, token, new_pw):
            show_popup("Success", "Password reset! Please log in.",
                       on_ok=lambda: self._go("login"))
        else:
            self.err_l2.text = "Invalid token. Please try again."

    def _go(self, screen):
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = screen
