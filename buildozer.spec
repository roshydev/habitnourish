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
source.include_exts = py,png,jpg,kv,atlas,csv

# Include all your source files
source.include_patterns = main.py,db.py,helpers.py,screens/*.py,*.csv

version = 1.0

# Python dependencies
# - chardet is required by the kivy recipe in p4a v2024.01.21 (python_depends)
# - Do NOT add charset-normalizer directly — v>=3.0.0 has a compiled C
#   extension (md.so) that causes architecture mismatch on ARM devices.
# - kivy version is set to 2.3.0 to match the p4a v2024.01.21 recipe exactly.
requirements = python3,kivy==2.3.0,sqlite3,certifi,chardet,idna,requests,urllib3,six

# Android orientation
orientation = portrait

# Android permissions
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# Minimum Android API (Android 8.0)
android.minapi = 26

# Target Android API — must be >= 34 for Android 15 devices to accept install
android.api = 35

# Pin python-for-android to v2024.01.21 which uses Python 3.11.5.
# p4a master has dropped support for Python < 3.14 (issue #3281) and
# hardcodes 3.14.2, which causes pip incompatibility errors during build.
# v2024.01.21 is the last stable release with Python 3.11 + NDK r25b support.
p4a.branch = v2024.01.21

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
