# -*- coding: utf-8 -*-
"""
HabitNourish - Healthy Diet App
Entry point — imports all screens and launches the app.
"""

import sys
import os

# Ensure project root is on the path so screens/ can import db and helpers
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kivy.app import App
from kivy.core.window import Window
from kivy.logger import Logger
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager

from db import init_db

from screens.login      import LoginScreen
from screens.register   import RegisterScreen
from screens.reset_pw   import ResetPwScreen
from screens.profile    import ProfileScreen
from screens.dashboard  import DashboardScreen
from screens.diet_plan  import DietPlanScreen
from screens.food_log   import FoodLogScreen
from screens.custom_food import CustomFoodScreen
from screens.progress   import ProgressScreen
from screens.analytics  import AnalyticsScreen
from screens.meal_plan  import MealPlanScreen
from screens.lifestyle  import LifestyleScreen
from screens.edit_targets import EditTargetsScreen

def _system_bar_insets():
    """Return (top, bottom) padding in pixels for the Android system bars.

    Apps targeting API 35 on Android 15+ are forced edge-to-edge: the app
    draws behind the status bar and navigation bar. We pad the root layout
    by those bar heights so the header and bottom content stay visible.
    On older Android the system already reserves that space, so we return
    (0, 0) to avoid a double gap. On desktop, jnius isn't available.
    """
    try:
        from jnius import autoclass
    except ImportError:
        return 0, 0  # desktop
    try:
        sdk = autoclass("android.os.Build$VERSION").SDK_INT
        if sdk < 35:
            Logger.info(f"HabitNourish: SDK={sdk} insets top=0 bottom=0 (not edge-to-edge)")
            return 0, 0
        res = autoclass("android.content.res.Resources").getSystem()

        def dim(name):
            rid = res.getIdentifier(name, "dimen", "android")
            return res.getDimensionPixelSize(rid) if rid > 0 else 0

        top, bottom = dim("status_bar_height"), dim("navigation_bar_height")
        Logger.info(f"HabitNourish: SDK={sdk} insets top={top} bottom={bottom}")
        return top, bottom
    except Exception as e:
        Logger.warning(f"HabitNourish: inset detection failed: {e!r}")
        return 0, 0


try:
    from android import mActivity  # noqa: F401 — only present on Android
except ImportError:
    # Desktop — apply a phone-like preview size
    Window.size = (390, 844)

Window.clearcolor = (0.945, 0.973, 0.914, 1)


class HabitNourishApp(App):
    user_id   = None
    user_name = ""
    profile   = {}

    def build(self):
        init_db()
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(RegisterScreen(name="register"))
        sm.add_widget(ResetPwScreen(name="reset_pw"))
        sm.add_widget(ProfileScreen(name="profile"))
        sm.add_widget(DashboardScreen(name="dashboard"))
        sm.add_widget(EditTargetsScreen(name="edit_targets"))
        sm.add_widget(DietPlanScreen(name="diet_plan"))
        sm.add_widget(FoodLogScreen(name="food_log"))
        sm.add_widget(CustomFoodScreen(name="custom_food"))
        sm.add_widget(ProgressScreen(name="progress"))
        sm.add_widget(AnalyticsScreen(name="analytics"))
        sm.add_widget(MealPlanScreen(name="meal_plan"))
        sm.add_widget(LifestyleScreen(name="lifestyle"))

        # Keep every screen clear of the status bar and navigation bar
        top, bottom = _system_bar_insets()
        root = BoxLayout(padding=[0, top, 0, bottom])
        root.add_widget(sm)
        return root


if __name__ == "__main__":
    HabitNourishApp().run()
