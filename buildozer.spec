# =======================================================================================
#
# Buildozer.spec for "轮换表计录入系统"
#
# Optimized for GitHub Actions and stable builds.
# Last Updated: 2025-08-22
#
# =======================================================================================

[app]
# (必填) 应用的标题，将显示在设备上
title = 轮换表计录入系统

# (必填) 应用的包名，必须是唯一的，通常采用反向域名格式
package.name = meterentry

# (必填) 应用的包域名
package.domain = org.k.yanshou

# (必填) 包含 main.py 的源码目录。'.' 代表当前目录。
source.dir = .

# (必填) 需要打包到应用中的文件扩展名列表。
# 已根据您的项目添加了字体文件 'ttc' 和 Excel 文件 'xlsx'。
source.include_exts = py,png,jpg,kv,atlas,ttc,xlsx

# (可选) 应用的版本号
version = 1.0.1

# (必填) 应用所需的 Python 依赖库列表。
# - python3, kivy: 基础运行环境
# - pandas: 用于处理Excel数据
# - openpyxl: pandas 读写 .xlsx 文件需要此库
# - plyer: 用于调用文件选择器等原生功能
requirements = python3,kivy,pandas,openpyxl,plyer

# (可选) 应用在设备上显示的旋转方向。
# 'portrait' (竖屏), 'landscape' (横屏), 'all' (所有方向)
orientation = portrait

# (可选) 应用图标的文件路径。
# 请确保在项目根目录下有一个名为 "icon.png" 的 1024x1024 像素的图片文件。
# icon.filename = %(source.dir)s/icon.png

# (可选) 应用启动画面的图片路径。
# splash.filename = %(source.dir)s/data/splash.png

# (可选) 是否全屏模式。
# 0 = 窗口化, 1 = 全屏
fullscreen = 0


[buildozer]
# (可选) buildozer 日志的详细程度。
# 0: 安静模式, 1: 基本信息, 2: 详细信息 (推荐用于调试)
log_level = 2

# (可选) 在每次构建前清除之前的构建缓存。
# 设为 1 可以解决一些缓存问题，但会显著增加构建时间。
# 0 = 否, 1 = 是
clean_dist = 1


# =======================================================================================
# Android Specific Settings
# =======================================================================================
[android]
# (推荐) 指定要构建的 CPU 架构。
# arm64-v8a 适用于现代64位设备，armeabi-v7a 兼容旧的32位设备。
android.archs = arm64-v8a, armeabi-v7a

# --- 版本锁定以确保稳定性 ---
# (推荐) 指定一个稳定的 Android SDK Platform 版本。
android.sdk = 33

# (推荐) 指定一个稳定的 Android NDK 版本。25b 是目前与 Kivy 兼容性最好的版本之一。
android.ndk = 25b

# (必填/推荐) 指定一个确切的 Build Tools 版本。
# 这可以避免 Buildozer 自动选择不稳定的预发布版本 (如 ...-rc1)，从而解决许可证接受问题。
android.build_tools = 34.0.0
# -----------------------------

# (推荐) 应用的目标 SDK 版本 (targetSdkVersion)，应与 android.sdk 保持一致。
android.api = 33

# (推荐) 应用支持的最低 SDK 版本 (minSdkVersion)。21 覆盖了约 98% 的设备。
android.minapi = 21

# (必填) 应用需要向用户请求的安卓权限。
# READ/WRITE_EXTERNAL_STORAGE 是为了让应用能够选择Excel文件和导出结果文件。
android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

# (可选) 如果你有预编译的 Java .jar 库，可以在这里添加。
# android.add_jars = foo.jar,bar.jar,path/to/more/

# (必填) 除了源码目录外，还需要额外完整包含进APK的资源目录。
# 这里我们将包含字体文件的 'fonts' 目录和包含Excel模板的 'assets' 目录添加进去。
p4a.source_dirs = assets,fonts
