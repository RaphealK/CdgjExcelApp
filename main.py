import os
import pandas as pd
from datetime import datetime
import traceback
from functools import partial

# ==================== Kivy & Font Setup ====================
from kivy.core.text import LabelBase
from kivy.resources import resource_add_path
from kivy.utils import platform

# 动态添加字体路径
font_path = os.path.join(os.getcwd(), 'fonts')
if os.path.exists(font_path):
    resource_add_path(font_path)
    LabelBase.register(name='Roboto', fn_regular='msyh.ttc')

# ==================== Kivy Imports ====================
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock

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

def show_popup_global(title, message):
    """一个全局的、可滚动的Popup，用于显示错误和信息"""
    scroll_view = ScrollView(size_hint=(1, 1))
    content_layout = BoxLayout(orientation='vertical', padding=10, spacing=10, size_hint_y=None)
    content_layout.bind(minimum_height=content_layout.setter('height'))
    
    msg_label = Label(text=message, size_hint_y=None, halign='center', valign='top')
    msg_label.bind(width=lambda *x: msg_label.setter('text_size')(msg_label, (msg_label.width, None)))
    msg_label.bind(texture_size=lambda *x: msg_label.setter('height')(msg_label, msg_label.texture_size[1]))
    
    content_layout.add_widget(msg_label)
    
    btn = Button(text='关闭', size_hint_y=None, height=44)
    popup = Popup(title=title, content=scroll_view, size_hint=(0.9, 0.6))
    btn.bind(on_press=popup.dismiss)
    content_layout.add_widget(btn)
    scroll_view.add_widget(content_layout)
    
    popup.open()

class AssetDatabase:
    def __init__(self, excel_path):
        try:
            self.df = pd.read_excel(excel_path, header=2)
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

class StartupScreen(Screen):
    ACTIVITY_RESULT_FILE_PICKER = 101
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if platform == 'android':
            self.android_init()
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        layout.add_widget(Label(text="轮换表计录入系统", font_size=24))
        
        path_layout = BoxLayout(size_hint_y=0.1)
        self.excel_path_input = TextInput(
            hint_text="点击右侧按钮选择Excel文件",
            text=os.path.join(os.getcwd(), 'assets', '轮换表计台账.xlsx'),
            readonly=True
        )
        path_layout.add_widget(self.excel_path_input)
        
        browse_btn = Button(text="浏览...", size_hint_x=0.2)
        browse_btn.bind(on_press=self.browse_file)
        path_layout.add_widget(browse_btn)
        layout.add_widget(path_layout)
        
        btn = Button(text="启动系统", size_hint_y=0.1)
        btn.bind(on_press=self.start_app)
        layout.add_widget(btn)
        
        layout.add_widget(Label(
            text="延寿供电所-K-2025年制", font_size='12sp',
            size_hint_y=None, height=30, color=(0.5, 0.5, 0.5, 1)
        ))
        self.add_widget(layout)
    
    def android_init(self):
        """安卓初始化"""
        # 绑定活动结果处理
        activity.bind(on_activity_result=self.on_activity_result)
        
        # 首次启动时请求权限
        self.request_android_permissions()
    
    def request_android_permissions(self):
        """请求必要的安卓权限"""
        try:
            if platform != 'android':
                return
                
            # 检查是否已经有权限
            if (not check_permission(Permission.READ_EXTERNAL_STORAGE) or 
                not check_permission(Permission.WRITE_EXTERNAL_STORAGE)):
                permissions = [Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE]
                request_permissions(permissions)
        except Exception as e:
            Clock.schedule_once(lambda dt: self.show_popup("权限错误", f"无法请求安卓权限: {e}"))

    def browse_file(self, instance):
        """打开文件选择器"""
        if platform == 'android':
            self.open_android_file_chooser()
        else:
            # 桌面平台使用plyer
            try:
                from plyer import filechooser
                filechooser.open_file(
                    on_selection=self.handle_selection, 
                    title="请选择台账Excel文件", 
                    filters=[("Excel Files", "*.xlsx", "*.xls")]
                )
            except ImportError:
                self.show_popup("功能缺失", "文件选择功能需要安装'plyer'库。\n请运行: pip install plyer")

    def open_android_file_chooser(self):
        """安卓原生文件选择器"""
        try:
            intent = Intent(Intent.ACTION_OPEN_DOCUMENT)
            intent.addCategory(Intent.CATEGORY_OPENABLE)
            intent.setType("*/*")  # 所有文件类型
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            intent.addFlags(Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION)
            
            current_activity = cast('android.app.Activity', PythonActivity.mActivity)
            current_activity.startActivityForResult(intent, self.ACTIVITY_RESULT_FILE_PICKER)
        except Exception as e:
            self.show_popup("文件选择错误", f"无法打开文件选择器: {e}")

    def on_activity_result(self, request_code, result_code, intent):
        """处理安卓文件选择结果"""
        if request_code != self.ACTIVITY_RESULT_FILE_PICKER or result_code != -1:  # -1 = RESULT_OK
            return
            
        try:
            uri = intent.getData()
            if not uri:
                return
                
            # 获取持久化权限
            context = PythonActivity.mActivity.getApplicationContext()
            content_resolver = context.getContentResolver()
            content_resolver.takePersistableUriPermission(
                uri, 
                Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION
            )
            
            # 复制文件到缓存
            Clock.schedule_once(lambda dt: self.copy_and_process_uri(uri), 0)
        except Exception as e:
            self.show_popup("文件处理错误", f"处理文件URI时出错: {e}")

    def copy_and_process_uri(self, uri):
        """复制URI指向的文件到应用缓存"""
        try:
            context = PythonActivity.mActivity.getApplicationContext()
            content_resolver = context.getContentResolver()
            
            # 获取缓存目录
            cache_dir = context.getCacheDir().getAbsolutePath()
            
            # 从URI获取文件名
            cursor = content_resolver.query(uri, None, None, None, None)
            if cursor:
                name_index = cursor.getColumnIndex(DocumentsContract.Document.COLUMN_DISPLAY_NAME)
                cursor.moveToFirst()
                file_name = cursor.getString(name_index)
                cursor.close()
            else:
                file_name = f"台账_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            # 目标文件路径
            local_path = os.path.join(cache_dir, file_name)
            
            # 复制文件
            input_stream = content_resolver.openInputStream(uri)
            output_stream = BufferedOutputStream(FileOutputStream(local_path))
            
            # 使用缓冲区高效复制
            buffer = bytearray(1024 * 1024)  # 1MB缓冲区
            total_bytes = 0
            while True:
                length = input_stream.read(buffer)
                if length == -1:
                    break
                output_stream.write(buffer, 0, length)
                total_bytes += length
            
            input_stream.close()
            output_stream.close()
            
            # 更新UI
            self.excel_path_input.text = local_path
            
        except Exception as e:
            self.show_popup("文件复制错误", f"无法复制文件: {e}\n{traceback.format_exc()}")

    def start_app(self, instance):
        excel_path = self.excel_path_input.text.strip()
        if not os.path.exists(excel_path):
            self.show_popup("错误", f"文件不存在或无法访问: {excel_path}")
            return
        
        app = App.get_running_app()
        try:
            app.asset_db = AssetDatabase(excel_path)
            main_screen = self.manager.get_screen('main')
            main_screen.reset_session()
            self.manager.current = 'main'
        except KeyError as e:
            self.show_popup("Excel读取错误", str(e))
        except Exception as e:
            self.show_popup("启动错误", f"加载Excel时发生未知错误: {str(e)}")

    def show_popup(self, title, message):
        show_popup_global(title, message)

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.output_path = None
        self.current_count = 0
        self.create_input_ui()
        self.add_widget(self.layout)

    def reset_session(self):
        """Resets the counter and output path when starting a new session."""
        self.current_count = 0
        self.output_path = None
        self.create_input_ui() 
      
    def create_input_ui(self):
        self.layout.clear_widgets()
      
        self.layout.add_widget(Label(text='输入原表资产号后6位:', size_hint_y=0.08))
        self.asset_input = TextInput(multiline=False, size_hint_y=0.08)
        self.asset_input.focus = True
        self.layout.add_widget(self.asset_input)
      
        submit_btn = Button(text='提交查询', size_hint_y=0.1)
        submit_btn.bind(on_press=self.check_asset)
        self.layout.add_widget(submit_btn)
      
        self.stats_layout = BoxLayout(size_hint_y=0.1)
        self.stats_label = Label(text=f'本轮已录入: {self.current_count}条')
        self.stats_btn = Button(text='导出数据', size_hint_x=0.3)
        self.stats_btn.bind(on_press=self.export_data)
        self.stats_layout.add_widget(self.stats_label)
        self.stats_layout.add_widget(self.stats_btn)
        self.layout.add_widget(self.stats_layout)
      
        back_btn = Button(text='返回首页', size_hint_y=0.1)
        back_btn.bind(on_press=self.back_to_start)
        self.layout.add_widget(back_btn)

        self.layout.add_widget(Label(
            text="By 延寿供电所 K", 
            font_size='12sp', 
            size_hint_y=None, 
            height=30, 
            color=(0.5, 0.5, 0.5, 1)
        ))

    def back_to_start(self, instance):
        self.manager.current = 'start'

    def check_asset(self, instance):
        last_6_digits = self.asset_input.text.strip()
        if not last_6_digits:
            self.show_popup("错误", "资产号不能为空")
            return
      
        matches = App.get_running_app().asset_db.get_info_by_last_6_digits(last_6_digits)
        self.asset_input.text = ""
      
        if not matches:
            self.show_popup("不存在", f"未找到以 '{last_6_digits}' 结尾的资产号")
        elif len(matches) == 1:
            self.show_verification_screen(matches[0])
        else:
            self.show_duplicate_selection_popup(matches)
      
    def show_duplicate_selection_popup(self, matches):
        content = GridLayout(cols=1, spacing=10, size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))
      
        content.add_widget(Label(text="发现多条重复数据，请选择正确的一条:"))
        for record in matches:
            display_text = f"客户号: {record['客户号']} | 用户名: {record['用户名']} | 资产号: {record['原表资产号']}"
            btn = Button(text=display_text, size_hint_y=None, height=40)
            btn.bind(on_press=partial(self.select_duplicate, record))
            content.add_widget(btn)

        self.popup = Popup(title="选择重复数据", content=content, size_hint=(0.9, 0.8))
        self.popup.open()
      
    def select_duplicate(self, record, instance):
        self.popup.dismiss()
        self.show_verification_screen(record)

    def show_verification_screen(self, user_info):
        self.layout.clear_widgets()
        user_text = (f"客户号: {user_info.get('客户号', '')}\n"
                     f"用户名: {user_info.get('用户名', '')}\n"
                     f"原表资产号: {user_info.get('原表资产号', '')}")
        self.layout.add_widget(Label(text=user_text, size_hint_y=0.15))
        self.layout.add_widget(Label(text='请核对以上信息是否正确', size_hint_y=0.05))
      
        btn_layout = BoxLayout(size_hint_y=0.15)
        correct_btn = Button(text='正确，下一步')
        correct_btn.bind(on_press=partial(self.show_detail_input, user_info))
        incorrect_btn = Button(text='错误，返回')
        incorrect_btn.bind(on_press=lambda x: self.create_input_ui())
        btn_layout.add_widget(correct_btn)
        btn_layout.add_widget(incorrect_btn)
        self.layout.add_widget(btn_layout)

    def show_detail_input(self, user_info, instance):
        self.layout.clear_widgets()
        self.user_info = user_info
      
        header_text = (f"客户号: {user_info.get('客户号', '')} | 用户名: {user_info.get('用户名', '')}\n"
                       f"原表资产号: {user_info.get('原表资产号', '')}")
        self.layout.add_widget(Label(text=header_text, size_hint_y=None, height=60))

        form_layout = GridLayout(cols=2, spacing=10, size_hint_y=0.8)
        self.inputs = {}
      
        fields = [
            ('原表表码', 'old_meter', str(user_info.get('原表表码', ''))),
            ('新资产号', 'new_asset', ''),
            ('铅封号', 'seal_number', ''),
            ('材料使用', 'material_usage', ''),
            ('备注', 'remark', '')
        ]
      
        for label_text, name, default in fields:
            form_layout.add_widget(Label(text=label_text))
            inp = TextInput(text=default, multiline=False)
            self.inputs[name] = inp
            form_layout.add_widget(inp)
          
        form_layout.add_widget(Label(text='表计类型'))
        self.inputs['meter_type'] = Spinner(text='单相表', values=('单相表', '三相表'), size_hint_y=None, height=44)
        form_layout.add_widget(self.inputs['meter_type'])
      
        form_layout.add_widget(Label(text='表箱类型'))
        self.inputs['box_type'] = Spinner(
            text='利旧未换', 
            values=('利旧未换', '单位', '双位', '双位单装'),
            size_hint_y=None, 
            height=44
        )
        form_layout.add_widget(self.inputs['box_type'])

        self.layout.add_widget(form_layout)
      
        btn_layout = BoxLayout(size_hint_y=0.1, spacing=10)
        submit_btn = Button(text='提交保存')
        submit_btn.bind(on_press=self.save_data)
        btn_layout.add_widget(submit_btn)
      
        back_btn = Button(text='返回上一步')
        back_btn.bind(on_press=lambda x: self.show_verification_screen(self.user_info))
        btn_layout.add_widget(back_btn)
        self.layout.add_widget(btn_layout)

    def get_output_path(self):
        """获取平台兼容的输出路径"""
        if platform == 'android':
            from jnius import autoclass
            Environment = autoclass('android.os.Environment')
            # 保存到公共的Downloads目录
            output_dir = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS).getAbsolutePath()
        else:
            # 桌面平台保存在当前工作目录
            output_dir = os.getcwd()

        if self.output_path is None or not os.path.dirname(self.output_path) == output_dir:
            now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_path = os.path.join(output_dir, f'录入结果_{now_str}.xlsx')
        
        return self.output_path

    def save_data(self, instance):
        data = {
            '客户号': self.user_info.get('客户号', ''), '用户名': self.user_info.get('用户名', ''),
            '原表资产号': self.user_info.get('原表资产号', ''), '原表表码': self.inputs['old_meter'].text,
            '新资产号': self.inputs['new_asset'].text, '铅封号': self.inputs['seal_number'].text,
            '表计类型': self.inputs['meter_type'].text, '表箱类型': self.inputs['box_type'].text,
            '安装人员': INSTALLER_NAMES,
            '材料使用': self.inputs['material_usage'].text, '备注': self.inputs['remark'].text,
            '录入时间': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.save_to_excel(data)

    def save_to_excel(self, data):
        output_file = self.get_output_path()
        try:
            new_row = pd.DataFrame([data])
            df = pd.read_excel(output_file) if os.path.exists(output_file) else pd.DataFrame()
            df = pd.concat([df, new_row], ignore_index=True)
          
            column_order = [
                '客户号', '用户名', '原表资产号', '原表表码', '新资产号',
                '表计类型', '铅封号', '表箱类型', '材料使用', '安装人员',
                '备注', '录入时间'
            ]
            df.reindex(columns=column_order).to_excel(output_file, index=False)

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


class ExcelDataEntryApp(App):
    def build(self):
        self.screen_manager = ScreenManager()
        self.screen_manager.add_widget(StartupScreen(name='start'))
        self.screen_manager.add_widget(MainScreen(name='main'))
        return self.screen_manager


if __name__ == '__main__':
    ExcelDataEntryApp().run()
