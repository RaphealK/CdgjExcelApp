import os
import openpyxl
import pandas as pd
from datetime import datetime
import traceback
from functools import partial

# ==================== Kivy, KivyMD & Font Setup ====================
from kivy.core.text import LabelBase
from kivy.resources import resource_add_path
from kivy.utils import platform
from kivy.properties import StringProperty, ObjectProperty
from kivy.clock import Clock

# KivyMD Imports
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.screen import MDScreen
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.menu import MDDropdownMenu
from kivymd.icon_definitions import md_icons

# 动态添加字体路径
# Ensure you have a font that supports Chinese characters in the 'fonts' directory.
# 'msyh.ttc' (Microsoft YaHei) is a good choice if available.
font_path = os.path.join(os.getcwd(), 'fonts')
if os.path.exists(font_path):
    resource_add_path(font_path)
    LabelBase.register(name='Roboto', fn_regular='msyh.ttc')

# ==================== Android Specific Imports ====================
if platform == 'android':
    from android import activity, mActivity
    from jnius import autoclass, cast
    from android.permissions import request_permissions, Permission, check_permission
    Intent = autoclass('android.content.Intent')
    Uri = autoclass('android.net.Uri')
    Environment = autoclass('android.os.Environment')
    DocumentsContract = autoclass('android.provider.DocumentsContract')
    ContentResolver = autoclass('android.content.ContentResolver')
    FileOutputStream = autoclass('java.io.FileOutputStream')
    InputStream = autoclass('java.io.InputStream')
    BufferedOutputStream = autoclass('java.io.BufferedOutputStream')
    ByteArrayOutputStream = autoclass('java.io.ByteArrayOutputStream')
    Context = autoclass('android.content.Context')
    PythonActivity = autoclass('org.kivy.android.PythonActivity')

# ==================== Global Constants & Helpers ====================
REQUIRED_COLUMNS = ['客户号', '用户名', '原表资产号', '原表表码']
INSTALLER_NAMES = '胡军明、胡柏兴、胡海亮、梁群平'
# Use a global dialog instance to prevent multiple popups
dialog = None

def show_popup_global(title, message):
    """A global KivyMD dialog for showing errors and information."""
    global dialog
    if not dialog:
        dialog = MDDialog(
            title=title,
            text=message,
            buttons=[
                MDFlatButton(
                    text="关闭",
                    theme_text_color="Custom",
                    text_color=MDApp.get_running_app().theme_cls.primary_color,
                    on_release=lambda x: dialog.dismiss()
                ),
            ],
        )
    else:
        dialog.title = title
        dialog.text = message
        
    dialog.open()


class AssetDatabase:
    def __init__(self, excel_path):
        try:
            self.df = pd.read_excel(excel_path, header=2, engine='openpyxl')
        except FileNotFoundError:
            self.df = pd.DataFrame()
            raise
        
        missing_cols = [col for col in REQUIRED_COLUMNS if col not in self.df.columns]
        if missing_cols:
            raise KeyError(f"Excel文件缺少必要的列: {', '.join(missing_cols)}")
        
        self.df.dropna(subset=['原表资产号'], inplace=True)
        self.df['原表资产号'] = self.df['原表资产号'].astype(str).str.strip()
    
    def get_info_by_last_6_digits(self, last_6_digits):
        last_6_digits = str(last_6_digits).strip()
        if not last_6_digits:
            return []
        matches = self.df[self.df['原表资产号'].str.endswith(last_6_digits)].copy()
        return matches.to_dict('records')

class StartupScreen(MDScreen):
    ACTIVITY_RESULT_FILE_PICKER = 101
    log_text = StringProperty("文件操作日志:\n")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if platform == 'android':
            self.android_init()
        
        self.main_layout = MDBoxLayout(orientation='vertical', padding="20dp", spacing="10dp", adaptive_height=True)
        
        self.main_layout.add_widget(MDLabel(
            text="轮换表计录入系统",
            halign='center',
            font_style='H4'
        ))
        
        path_layout = MDBoxLayout(size_hint_y=None, height="48dp", spacing="10dp")
        self.excel_path_input = MDTextField(
            hint_text="点击右侧按钮选择Excel文件",
            text=os.path.join(os.getcwd(), 'assets', '轮换表计台账.xlsx'),
            mode="rectangle",
        )
        path_layout.add_widget(self.excel_path_input)
        
        browse_btn = MDRaisedButton(text="浏览...")
        browse_btn.bind(on_press=self.browse_file)
        path_layout.add_widget(browse_btn)
        self.main_layout.add_widget(path_layout)
        
        btn = MDRaisedButton(
            text="启动系统",
            pos_hint={'center_x': 0.5},
            size_hint_x=0.5
        )
        btn.bind(on_press=self.start_app)
        self.main_layout.add_widget(btn)
        
        log_layout = MDBoxLayout(orientation='vertical', size_hint_y=None, height="200dp", spacing="5dp")
        log_layout.add_widget(MDLabel(text="文件操作日志:", size_hint_y=None, height="20dp"))
        
        log_scroll = MDScrollView()
        self.log_textinput = MDTextField(
            text=self.log_text,
            multiline=True,
            readonly=True,
            mode="fill"
        )
        log_scroll.add_widget(self.log_textinput)
        log_layout.add_widget(log_scroll)
        self.main_layout.add_widget(log_layout)
        
        footer_layout = MDBoxLayout(orientation='vertical', adaptive_height=True)
        footer_layout.add_widget(MDLabel(
            text="延寿供电所-K-2025年制",
            halign='center',
            font_style='Caption',
            theme_text_color="Secondary"
        ))
        self.main_layout.add_widget(footer_layout)
        
        self.add_widget(self.main_layout)
        
        self.add_log("系统初始化完成")
        self.add_log(f"默认文件路径: {self.excel_path_input.text}")
    
    def add_log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text += log_entry
        self.log_textinput.text = self.log_text
    
    def android_init(self):
        activity.bind(on_activity_result=self.on_activity_result)
        self.request_android_permissions()
    
    def request_android_permissions(self):
        try:
            if platform != 'android':
                return
            if (not check_permission(Permission.READ_EXTERNAL_STORAGE) or 
                not check_permission(Permission.WRITE_EXTERNAL_STORAGE)):
                permissions = [Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE]
                request_permissions(permissions)
                self.add_log("已请求存储权限")
        except Exception as e:
            self.add_log(f"权限请求错误: {e}")
            Clock.schedule_once(lambda dt: self.show_popup("权限错误", f"无法请求安卓权限: {e}"))

    def browse_file(self, instance):
        self.add_log("启动文件选择器...")
        if platform == 'android':
            self.open_android_file_chooser()
        else:
            try:
                from plyer import filechooser
                self.add_log("打开桌面文件选择器")
                filechooser.open_file(
                    on_selection=self.handle_selection, 
                    title="请选择台账Excel文件", 
                    filters=[("Excel Files", "*.xlsx", "*.xls")]
                )
            except ImportError:
                self.add_log("错误: 需要安装'plyer'库")
                self.show_popup("功能缺失", "文件选择功能需要安装'plyer'库。\n请运行: pip install plyer")
    
    def handle_selection(self, selection):
        if selection:
            path = selection[0]
            self.excel_path_input.text = path
            self.add_log(f"已选择文件: {path}")
        else:
            self.add_log("文件选择已取消")

    def open_android_file_chooser(self):
        try:
            intent = Intent(Intent.ACTION_OPEN_DOCUMENT)
            intent.addCategory(Intent.CATEGORY_OPENABLE)
            intent.setType("*/*")
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            intent.addFlags(Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION)
            current_activity = cast('android.app.Activity', PythonActivity.mActivity)
            current_activity.startActivityForResult(intent, self.ACTIVITY_RESULT_FILE_PICKER)
            self.add_log("已启动安卓文件选择器")
        except Exception as e:
            self.add_log(f"文件选择器错误: {e}")
            self.show_popup("文件选择错误", f"无法打开文件选择器: {e}")

    def on_activity_result(self, request_code, result_code, intent):
        Clock.schedule_once(
            lambda dt: self._process_activity_result(request_code, result_code, intent)
        )

    def _process_activity_result(self, request_code, result_code, intent):
        if request_code != self.ACTIVITY_RESULT_FILE_PICKER or result_code != -1:
            self.add_log("文件选择已取消")
            return
        try:
            uri = intent.getData()
            if not uri:
                self.add_log("错误: 未获取到文件URI")
                return
            self.add_log(f"获取到文件URI: {uri.toString()}")
            context = PythonActivity.mActivity.getApplicationContext()
            content_resolver = context.getContentResolver()
            content_resolver.takePersistableUriPermission(
                uri, 
                Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION
            )
            self.add_log("已获取文件持久化权限")
            self.add_log("开始复制文件...")
            self.copy_and_process_uri(uri)
        except Exception as e:
            error_msg = f"文件处理错误: {e}\n{traceback.format_exc()}"
            self.add_log(error_msg)
            self.show_popup("文件处理错误", f"处理文件URI时出错: {error_msg}")

    def copy_and_process_uri(self, uri):
        try:
            context = PythonActivity.mActivity.getApplicationContext()
            content_resolver = context.getContentResolver()
            cache_dir = context.getCacheDir().getAbsolutePath()
            self.add_log(f"应用缓存目录: {cache_dir}")
            
            cursor = content_resolver.query(uri, None, None, None, None)
            file_name = ""
            if cursor:
                name_index = cursor.getColumnIndex('_display_name')
                cursor.moveToFirst()
                file_name = cursor.getString(name_index)
                cursor.close()
                self.add_log(f"获取文件名: {file_name}")
            else:
                file_name = f"台账_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                self.add_log(f"无法获取文件名，使用默认: {file_name}")
            
            local_path = os.path.join(cache_dir, file_name)
            self.add_log(f"目标路径: {local_path}")
            
            input_stream = content_resolver.openInputStream(uri)
            output_stream = BufferedOutputStream(FileOutputStream(local_path))
            
            buffer = bytearray(1024 * 1024)
            total_bytes = 0
            self.add_log("开始复制文件内容...")
            while True:
                length = input_stream.read(buffer)
                if length == -1:
                    break
                output_stream.write(buffer, 0, length)
                total_bytes += length
            
            input_stream.close()
            output_stream.close()
            self.add_log(f"文件复制完成，大小: {total_bytes//1024} KB")
            
            self.excel_path_input.text = local_path
            self.add_log(f"文件已复制到: {local_path}")
            
        except Exception as e:
            error_msg = f"文件复制错误: {e}\n{traceback.format_exc()}"
            self.add_log(error_msg)
            self.show_popup("文件复制错误", f"无法复制文件: {e}")

    def start_app(self, instance):
        excel_path = self.excel_path_input.text.strip()
        self.add_log(f"尝试加载文件: {excel_path}")
        
        if not os.path.exists(excel_path):
            error_msg = f"文件不存在或无法访问: {excel_path}"
            self.add_log(error_msg)
            self.show_popup("错误", error_msg)
            return
        
        app = MDApp.get_running_app()
        try:
            self.add_log("初始化资产数据库...")
            timestamp = datetime.now().strftime("%H:%M:%S")
            app.asset_db = AssetDatabase(excel_path)
            
            row_count = len(app.asset_db.df)
            self.add_log(f"文件加载成功! 时间: {timestamp}")
            self.add_log(f"记录总数: {row_count}")
            self.add_log(f"首条记录资产号: {app.asset_db.df.iloc[0]['原表资产号']}")
            
            main_screen = self.manager.get_screen('main')
            main_screen.reset_session()
            self.add_log("正在进入主界面...")
            self.manager.current = 'main'
        except KeyError as e:
            error_msg = f"Excel格式错误: {str(e)}"
            self.add_log(error_msg)
            self.show_popup("Excel读取错误", error_msg)
        except Exception as e:
            error_msg = f"加载Excel时发生未知错误: {str(e)}\n{traceback.format_exc()}"
            self.add_log(error_msg)
            self.show_popup("启动错误", error_msg)

    def show_popup(self, title, message):
        show_popup_global(title, message)

class MainScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = MDBoxLayout(orientation='vertical', padding="10dp", spacing="10dp")
        self.output_path = None
        self.current_count = 0
        self.meter_type_menu = None
        self.box_type_menu = None
        self.create_input_ui()
        self.add_widget(self.layout)

    def reset_session(self):
        self.current_count = 0
        self.output_path = None
        self.create_input_ui() 
      
    def create_input_ui(self):
        self.layout.clear_widgets()
      
        self.layout.add_widget(MDLabel(text='输入原表资产号后6位:', halign='center', adaptive_height=True))
        self.asset_input = MDTextField(
            hint_text="资产号后6位",
            mode="rectangle",
            helper_text_mode="on_focus"
        )
        self.asset_input.focus = True
        self.layout.add_widget(self.asset_input)
      
        submit_btn = MDRaisedButton(text='提交查询', pos_hint={'center_x': 0.5})
        submit_btn.bind(on_press=self.check_asset)
        self.layout.add_widget(submit_btn)
      
        self.stats_layout = MDBoxLayout(adaptive_height=True, spacing="10dp")
        self.stats_label = MDLabel(text=f'本轮已录入: {self.current_count}条')
        self.stats_btn = MDRaisedButton(text='导出数据')
        self.stats_btn.bind(on_press=self.export_data)
        self.stats_layout.add_widget(self.stats_label)
        self.stats_layout.add_widget(self.stats_btn)
        self.layout.add_widget(self.stats_layout)
      
        back_btn = MDRaisedButton(text='返回首页', pos_hint={'center_x': 0.5})
        back_btn.bind(on_press=self.back_to_start)
        self.layout.add_widget(back_btn)

        self.layout.add_widget(MDLabel(
            text="By 延寿供电所 K", 
            halign='center',
            font_style='Caption', 
            adaptive_height=True, 
            theme_text_color="Secondary"
        ))

    def back_to_start(self, instance):
        self.manager.current = 'start'

    def check_asset(self, instance):
        last_6_digits = self.asset_input.text.strip()
        if not last_6_digits:
            self.show_popup("错误", "资产号不能为空")
            return
      
        matches = MDApp.get_running_app().asset_db.get_info_by_last_6_digits(last_6_digits)
        self.asset_input.text = ""
      
        if not matches:
            self.show_popup("不存在", f"未找到以 '{last_6_digits}' 结尾的资产号")
        elif len(matches) == 1:
            self.show_verification_screen(matches[0])
        else:
            self.show_duplicate_selection_popup(matches)
      
    def show_duplicate_selection_popup(self, matches):
        buttons = []
        for record in matches:
            display_text = f"客户号: {record['客户号']}\n用户名: {record['用户名']}\n资产号: {record['原表资产号']}"
            btn = MDFlatButton(
                text=display_text,
                on_release=partial(self.select_duplicate, record)
            )
            buttons.append(btn)

        self.popup = MDDialog(
            title="选择重复数据",
            type="simple",
            items=buttons
        )
        self.popup.open()
      
    def select_duplicate(self, record, instance):
        self.popup.dismiss()
        self.show_verification_screen(record)

    def show_verification_screen(self, user_info):
        self.layout.clear_widgets()
        user_text = (f"客户号: {user_info.get('客户号', '')}\n"
                     f"用户名: {user_info.get('用户名', '')}\n"
                     f"原表资产号: {user_info.get('原表资产号', '')}")
        self.layout.add_widget(MDLabel(text=user_text, halign='center'))
        self.layout.add_widget(MDLabel(text='请核对以上信息是否正确', halign='center'))
      
        btn_layout = MDBoxLayout(adaptive_height=True, spacing="10dp", pos_hint={'center_x': 0.5})
        correct_btn = MDRaisedButton(text='正确，下一步')
        correct_btn.bind(on_press=partial(self.show_detail_input, user_info))
        incorrect_btn = MDRaisedButton(text='错误，返回')
        incorrect_btn.bind(on_press=lambda x: self.create_input_ui())
        btn_layout.add_widget(correct_btn)
        btn_layout.add_widget(incorrect_btn)
        self.layout.add_widget(btn_layout)

    def show_detail_input(self, user_info, instance):
        self.layout.clear_widgets()
        self.user_info = user_info
      
        header_text = (f"客户号: {user_info.get('客户号', '')} | 用户名: {user_info.get('用户名', '')}\n"
                       f"原表资产号: {user_info.get('原表资产号', '')}")
        self.layout.add_widget(MDLabel(text=header_text, adaptive_height=True, halign='center'))

        self.inputs = {}
        fields = [
            ('原表表码', 'old_meter', str(user_info.get('原表表码', ''))),
            ('新资产号', 'new_asset', ''),
            ('铅封号', 'seal_number', ''),
            ('材料使用', 'material_usage', ''),
            ('备注', 'remark', '')
        ]
      
        for label_text, name, default in fields:
            self.inputs[name] = MDTextField(hint_text=label_text, text=default, mode="rectangle")
            self.layout.add_widget(self.inputs[name])
          
        # Dropdown for Meter Type
        meter_types = ['单相表', '三相表']
        self.inputs['meter_type_button'] = MDRaisedButton(text='表计类型: 单相表', pos_hint={'center_x': 0.5})
        self.meter_type_menu = self.create_dropdown_menu(self.inputs['meter_type_button'], meter_types, "表计类型")
        self.inputs['meter_type_button'].bind(on_release=lambda x: self.meter_type_menu.open())
        self.layout.add_widget(self.inputs['meter_type_button'])
      
        # Dropdown for Box Type
        box_types = ['利旧未换', '单位', '双位', '双位单装']
        self.inputs['box_type_button'] = MDRaisedButton(text='表箱类型: 利旧未换', pos_hint={'center_x': 0.5})
        self.box_type_menu = self.create_dropdown_menu(self.inputs['box_type_button'], box_types, "表箱类型")
        self.inputs['box_type_button'].bind(on_release=lambda x: self.box_type_menu.open())
        self.layout.add_widget(self.inputs['box_type_button'])

        btn_layout = MDBoxLayout(adaptive_height=True, spacing="10dp", pos_hint={'center_x': 0.5})
        submit_btn = MDRaisedButton(text='提交保存')
        submit_btn.bind(on_press=self.save_data)
        btn_layout.add_widget(submit_btn)
      
        back_btn = MDRaisedButton(text='返回上一步')
        back_btn.bind(on_press=lambda x: self.show_verification_screen(self.user_info))
        btn_layout.add_widget(back_btn)
        self.layout.add_widget(btn_layout)

    def create_dropdown_menu(self, caller, items, prefix):
        menu_items = [
            {
                "text": item,
                "viewclass": "OneLineListItem",
                "on_release": lambda x=item: self.set_item(caller, x, prefix),
            } for item in items
        ]
        return MDDropdownMenu(
            caller=caller,
            items=menu_items,
            width_mult=4,
        )

    def set_item(self, caller, text_item, prefix):
        caller.text = f"{prefix}: {text_item}"
        if self.meter_type_menu: self.meter_type_menu.dismiss()
        if self.box_type_menu: self.box_type_menu.dismiss()
        
    def get_output_path(self):
        if platform == 'android':
            from jnius import autoclass
            Environment = autoclass('android.os.Environment')
            output_dir = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS).getAbsolutePath()
        else:
            output_dir = os.path.expanduser("~/Downloads")
            if not os.path.exists(output_dir):
                 output_dir = os.getcwd()

        if self.output_path is None or not os.path.dirname(self.output_path) == output_dir:
            now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_path = os.path.join(output_dir, f'录入结果_{now_str}.xlsx')
        
        return self.output_path

    def save_data(self, instance):
        meter_type = self.inputs['meter_type_button'].text.split(': ')[1]
        box_type = self.inputs['box_type_button'].text.split(': ')[1]
        
        data = {
            '客户号': self.user_info.get('客户号', ''), '用户名': self.user_info.get('用户名', ''),
            '原表资产号': self.user_info.get('原表资产号', ''), '原表表码': self.inputs['old_meter'].text,
            '新资产号': self.inputs['new_asset'].text, '铅封号': self.inputs['seal_number'].text,
            '表计类型': meter_type, '表箱类型': box_type,
            '安装人员': INSTALLER_NAMES,
            '材料使用': self.inputs['material_usage'].text, '备注': self.inputs['remark'].text,
            '录入时间': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.save_to_excel(data)

    def save_to_excel(self, data):
        output_file = self.get_output_path()
        try:
            new_row = pd.DataFrame([data])
            df = pd.read_excel(output_file, engine='openpyxl') if os.path.exists(output_file) else pd.DataFrame()
            df = pd.concat([df, new_row], ignore_index=True)
          
            column_order = [
                '客户号', '用户名', '原表资产号', '原表表码', '新资产号',
                '表计类型', '铅封号', '表箱类型', '材料使用', '安装人员',
                '备注', '录入时间'
            ]
            df = df.reindex(columns=column_order)
            df.to_excel(output_file, index=False)

            self.current_count += 1
            self.show_popup("成功", f"数据已保存！\n路径:\n{output_file}")
            self.create_input_ui()
            self.stats_label.text = f'本轮已录入: {self.current_count}条'

        except PermissionError:
            self.show_popup("保存错误", f"无法写入文件！\n请检查权限或关闭已打开的Excel文件:\n{output_file}")
        except Exception as e:
            self.show_popup("保存错误", f"保存数据时出错: {str(e)}")

    def export_data(self, instance):
        if self.output_path and os.path.exists(self.output_path):
            self.show_popup("导出成功", f"数据已保存到:\n{self.output_path}")
        else:
            self.show_popup("警告", "尚未录入任何数据，无文件可导出")

    def show_popup(self, title, message):
        show_popup_global(title, message)


class ExcelDataEntryApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        self.screen_manager = MDScreenManager()
        self.screen_manager.add_widget(StartupScreen(name='start'))
        self.screen_manager.add_widget(MainScreen(name='main'))
        return self.screen_manager


if __name__ == '__main__':
    ExcelDataEntryApp().run()
