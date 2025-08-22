[app]

# 应用名称
title = 轮换表计录入系统
# 包名 (反向域名格式)
package.name = com.yanshougongdiansuo.meter_entry
# 应用版本
version = 0.1
# 源代码文件
source.dir = .
# 主程序入口
source.include_exts = py,png,jpg,kv,atlas,ttf,xlsx
# 主文件
source.main = main.py
# 支持的Android API版本
android.minapi = 21
# 目标Android API版本
android.target_api = 33
# 应用权限
android.permissions = WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE
# 使用的SDK版本
android.sdk = 24
# 使用的NDK版本
android.ndk = 23b
# 包含的额外文件
source.include_patterns = assets/*,fonts/*
# 打包时排除的目录
source.exclude_dirs = tests, bin, docs, .github, venv, __pycache__
# 图标文件
#icon.filename = %(source.dir)s/assets/icon.png
# 启动画面
#presplash.filename = %(source.dir)s/assets/presplash.png
# 应用方向
orientation = portrait
# 完整屏幕设置
fullscreen = 0
# 日志级别
log_level = 2
# Kivy版本
requirements = python3,kivy==2.3.0,plyer,pandas,openpyxl,chardet
# 额外依赖
android.extra_dependencies = androidx.appcompat:appcompat:1.4.1, androidx.core:core:1.7.0
# 打包模式
p4a.branch = master
# 使用的Android架构
android.arch = armeabi-v7a
# 允许备份
android.allow_backup = True
# 密匙库配置
# (buildozer android debug将自动创建)
