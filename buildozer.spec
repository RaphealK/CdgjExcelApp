[app]
# (字符串) 应用的标题
# 例如在任务管理器或窗口标题栏显示的名称
title = 轮换表计录入系统

# (字符串) 应用的包名
# 通常采用反向域名格式，例如 com.mycompany.myapp
package.name = yanshou_meter_entry

# (字符串) 应用的包域名
# 与包名一起构成完整的Android包ID: <package.domain>.<package.name>
package.domain = org.YanShou.k2025

# (字符串) 包含 main.py 的源代码目录
# '.' 表示当前目录
source.dir = .

# (列表) 需要包含在项目中的文件扩展名
# .py 是Python代码, .kv 是Kivy语言文件(如果使用的话), .png/.jpg是图片资源
source.include_exts = py,png,jpg,kv,atlas,xlsx,ttc

# (列表) 需要包含的目录
# 这里我们添加 'assets' 和 'fonts' 目录，以确保字体和默认Excel文件被打包
source.include_dirs = assets, fonts

# (字符串) 应用的版本号
version = 1.0.0

# (列表) 应用所需的Python依赖库
# buildozer会自动通过pip下载这些库。我们添加了pandas, openpyxl和plyer
# kivymd, kivy, jnius 通常会被buildozer自动包含，但明确写出更保险
requirements = python3,plyer,cython,pyjnius,jnius,et_xmlfile,openpyxl==3.1.2,kivy==2.3.0,pandas==2.0.3,numpy

# (字符串) 应用启动时加载的屏幕方向
# 可选项: landscape, portrait, all
orientation = portrait

# (布尔值) 设置为True时，每次构建前都会清除之前的下载和构建缓存
# 在遇到奇怪的构建问题时很有用，但会显著增加构建时间
# clean_build = True

# (字符串) 应用图标的文件名
# 图标文件需要放在源代码目录 (source.dir) 下
icon.filename = %(source.dir)s/icon.png

# (布-尔值) 应用是否全屏显示
# 0 = 非全屏, 1 = 全屏
fullscreen = 0

# (字符串) 应用启动时的加载闪屏图片
presplash.filename = %(source.dir)s/data/presplash.png


[android]
# (列表) 应用需要的安卓权限
# READ_EXTERNAL_STORAGE 和 WRITE_EXTERNAL_STORAGE 是为了读写设备上的Excel文件
android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

# (整数) 安卓API级别
# 这是构建应用时使用的目标SDK版本。建议使用较新的版本。
android.api = 33

# (整数) 应用支持的最低安卓API级别
# 决定了应用可以安装在哪些老版本的安卓系统上。21对应Android 5.0。
android.minapi = 21

# (整数) 编译时使用的安卓SDK版本
# 通常与 android.api 保持一致
android.sdk = 33

# (整数) 编译时使用的安卓NDK版本
# 推荐使用较新的稳定版本
android.ndk = 25b

# (列表) 目标CPU架构
# arm64-v8a 是现代64位安卓设备的标准。armeabi-v7a 是为了兼容旧的32位设备。
# 同时构建两者会使APK体积变大，但兼容性更好。
android.archs = arm64-v8a, armeabi-v7a

# (字符串) 生成的包类型
# aab 是上传到Google Play商店的推荐格式，apk 是用于直接安装的格式
# build_type = aab
# build_type = apk

# (字符串) Keystore文件的路径，用于应用签名
# 如果不指定，buildozer会创建一个调试用的keystore
# android.keystore = /path/to/your.keystore
# android.keystore_alias = your_alias
# android.keystore_pass = your_password
# android.alias_pass = your_alias_password

# (列表) 在构建过程中需要下载的Java库 (例如 .jar 或 .aar 文件)
# 对于使用了 jnius 与安卓原生功能深度交互的复杂应用，可能需要配置此项
# android.add_jars = libs/my-java-library.jar

# (字符串) Gradle构建工具的版本
# 通常保持默认即可，除非有特定需求
# android.gradle_version = 7.2


android.enable_androidx = True

[buildozer]
# (整数) 日志输出的详细程度
# 2 表示最详细的日志，有助于调试构建过程中的问题
log_level = 2

# (布尔值) 是否允许buildozer访问网络来下载依赖项
# 通常应保持为 True
warn_on_root = 1
