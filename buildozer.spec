[app]

# Application title
title = 轮换表计录入系统

# Package name (reverse domain format)
package.name = com.yanshougongdiansuo.meterentry

# Application version
version = 1.0.0

# Source code directory
source.dir = .

# Application icon
#icon.filename = icon.png

# Presplash screen
#presplash.filename = presplash.png

# Supported orientations (portrait|landscape)
orientation = portrait

# Main application file
source.main = main.py

# Included files and patterns
source.include_exts = py,png,jpg,kv,atlas,ttf,xlsx
source.include_patterns = assets/*,fonts/*

# Android specific configurations
android.minapi = 21
android.target_api = 24
android.ndk_path = /opt/android-ndk  # Docker 容器中的路径
android.sdk_path = /sdk             # Docker 容器中的路径
android.arch = armeabi-v7a

# Accept SDK licenses automatically
android.accept_sdk_license = True

# Android permissions
android.permissions = WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

# Application requirements
requirements = python3==3.10.5, kivy==2.3.0, plyer, pandas, openpyxl, chardet

# Build behavior
log_level = 2
fullscreen = 0
android.wakelock = False
android.allow_backup = True
android.private_storage = False
