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
        sm.add_widget(DietPlanScreen(name="diet_plan"))
        sm.add_widget(FoodLogScreen(name="food_log"))
        sm.add_widget(CustomFoodScreen(name="custom_food"))
        sm.add_widget(ProgressScreen(name="progress"))
        sm.add_widget(AnalyticsScreen(name="analytics"))
        sm.add_widget(MealPlanScreen(name="meal_plan"))
        sm.add_widget(LifestyleScreen(name="lifestyle"))
        return sm


if __name__ == "__main__":
    HabitNourishApp().run()
