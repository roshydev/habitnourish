[app]

# App title shown on the phone
title = HabitNourish

# Package name (must be unique, lowercase, no spaces)
package.name = habitnourish

# Package domain (reverse domain style)
package.domain = com.roshydev

# Source directory (where main.py lives)
source.dir = .

# Entry point
source.include_exts = py,png,jpg,kv,atlas,csv,db

# Include all your source files
source.include_patterns = main.py,db.py,helpers.py,screens/*.py,*.csv

version = 1.0

# Python dependencies
requirements = python3,kivy==2.3.1,sqlite3

# Android orientation
orientation = portrait

# Android permissions
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# Minimum Android API (Android 8.0)
android.minapi = 26

# Target Android API
android.api = 33

# Android NDK version
android.ndk = 25b

# Android build tools version
android.build_tools_version = 37.0.0

# Android architecture (covers most modern phones)
android.archs = arm64-v8a, armeabi-v7a

# App icon (optional — add a 512x512 PNG named icon.png to use it)
# icon.filename = %(source.dir)s/icon.png

# Fullscreen
fullscreen = 0

[buildozer]

# Log level (0=error, 1=info, 2=debug)
log_level = 2

# Warn on root
warn_on_root = 1
