[app]

# (str) Title of your application
title = Meter Replacement Entry System

# (str) Package name
package.name = meter_entry_app

# (str) Package domain (needed for android/ios packaging)
package.domain = org.example

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let buildozer find them)
source.include_exts = py,png,jpg,kv,atlas,ttc,xlsx

# (list) List of inclusions using pattern matching
# This is crucial for including your font and default excel file
source.include_patterns = assets/*, fonts/*

# (str) Application versioning
version = 1.0

# (list) Application requirements
# Kivy for the app, pandas for excel, plyer for filechooser, openpyxl for pandas to read/write xlsx
requirements = python3,kivy,pandas,plyer,openpyxl,cython,pyjnius,jnius

# (str) Custom orientation
orientation = portrait

# (str) Icon of the application
# icon.filename = %(source.dir)s/data/icon.png

# (str) Presplash of the application
# presplash.filename = %(source.dir)s/data/presplash.png

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

# (int) Android API to use
# As of 2024, Google Play requires a target API level of 33 or higher.
android.api = 33

# (int) Minimum API required
android.minapi = 21

# (list) Android architectures to build for
android.archs = arm64-v8a, armeabi-v7a

android.enable_androidx = True


[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
