[app]

# 应用名称和包名
title = 轮换表计录入系统
package.name = meterreplacement
package.domain = org.yanzhou

# 源文件配置
source.dir = .
source.include_exts = py,png,jpg,kv,ttf,xlsx
source.include_patterns = assets/*,fonts/*

# 主程序入口
orientation = portrait
fullscreen = 0
requirements = 
    python3,
    kivy==2.2.1,
    pandas,
    openpyxl,
    xlrd,
    plyer,
    pyjnius,
		libffi==3.3

# Android 特定配置
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
#android.api = 33
#android.minapi = 21
#android.ndk = 23b
#android.sdk_path = 
#p4a.branch = master

# 资源包含
assets.dir = assets
version = 0.1
