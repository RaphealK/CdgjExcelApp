[app]
# (必须) 应用标题
title = 轮换表计录入系统

# (必须) 应用的包名，格式为 com.domain.appname
package.name = meter_entry_app

# (必须) 应用的包域名
package.domain = org.cdgj

# (必须) 源文件目录，'.' 代表当前目录
source.dir = .

# (必须) 要包含的文件扩展名
source.include_exts = py,png,jpg,kv,atlas,txt,ttc,xlsx

# (可选) 要排除的目录和文件，可以减小APK体积
source.exclude_dirs = tests, .github, docs, examples
source.exclude_patterns = .git/, *.spec, .buildozer/, bin/

# (必须) 应用版本号
version = 1.0

# (必须) 应用的依赖库列表
# 锁定 pyjnius 和 Cython 的版本以确保编译成功
requirements = python3,kivy==2.2.1,pandas,openpyxl,xlrd,plyer,pyjnius==1.5.0,Cython==0.29.36

# (必须) 应用的屏幕方向
orientation = portrait

# (可选) 应用启动时的加载屏幕
presplash.filename = %(source.dir)s/data/presplash.png

# (可选) 应用图标
icon.filename = %(source.dir)s/data/icon.png

# (必须) 要使用的Android API级别
# 注意：Google Play要求新应用target API 33 (Android 13) 或更高
android.api = 33

# (必须) 最低支持的Android API级别
android.minapi = 21

# (必须) 安卓权限
# READ_EXTERNAL_STORAGE 和 WRITE_EXTERNAL_STORAGE 对于文件选择和保存至关重要
android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

# (可选) 全屏模式
fullscreen = 0


[buildozer]
# (必须) 日志级别。2表示详细输出，有助于调试
log_level = 2

# (可选) 在编译失败前显示警告
warn_on_root = 1
