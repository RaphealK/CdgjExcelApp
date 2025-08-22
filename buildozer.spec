[app]
# 应用名字
title = ExcelDataEntryApp
package.name = excel_data_entry
package.domain = org.example

# 入口文件
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,xls,xlsx

# 主程序
main.py = main.py

# 图标
#icon.filename = %(source.dir)s/data/icon.png

# 版本号
version = 0.1

# 支持的权限（你的程序需要读写Excel文件）
android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

# 支持的方向
orientation = portrait

# 依赖的库（非常重要！！！）
requirements = python3,kivy,pandas,openpyxl,plyer

android.add_presplash = true

# 使用哪种打包方式
fullscreen = 0
android.api = 33
android.build_tools_version = 33.0.2

[buildozer]
log_level = 2
warn_on_root = 1

[app:android]
# 打包后APK名字
package.filename = %(appname)s-%(version)s.apk
