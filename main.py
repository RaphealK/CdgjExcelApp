import os
import pandas as pd
from datetime import datetime
import traceback
from functools import partial

# ==================== Kivy & Font Setup ====================
from kivy.core.text import LabelBase
from kivy.resources import resource_add_path
from kivy.utils import platform, get_color_from_hex
from kivy.factory import Factory

# 动态添加字体路径
font_path = os.path.join(os.getcwd(), 'fonts')
if os.path.exists(font_path):
    resource_add_path(font_path)
    LabelBase.register(name='AppFont', fn_regular='msyh.ttc')

# ==================== Kivy Imports ====================
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.properties import StringProperty, ObjectProperty
from kivy.core.window import Window
from kivy.lang import Builder

# ==================== 全局字体样式规则 ====================
Builder.load_string('''
<Label,Button,TextInput,Spinner>:
    font_name: 'AppFont'
''')

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
    Context = autoclass('android.content.Context')
    PythonActivity = autoclass('org.kivy.android.PythonActivity')

# ==================== Global Constants & Theming ====================
REQUIRED_COLUMNS = ['客户号', '用户名', '原表资产号', '原表表码']
INSTALLER_NAMES = '胡军明、胡柏兴、胡海亮、梁群平'
DATA_COLUMN_ORDER = ['客户号', '用户名', '原表资产号', '原表表码', '新资产号', '表计类型', '铅封号', '表箱类型', '材料使用', '安装人员', '备注', '录入时间']


C = {
    "primary": get_color_from_hex("#3F51B5"), "accent": get_color_from_hex("#448AFF"),
    "background": get_color_from_hex("#F5F5F5"), "card": get_color_from_hex("#FFFFFF"),
    "text": get_color_from_hex("#212121"), "text_secondary": get_color_from_hex("#757575"),
    "divider": get_color_from_hex("#BDBDBD"), "error": get_color_from_hex("#D32F2F"),
}
Window.clearcolor = C["background"]

# --- Custom Widget Base Classes ---
class ThemedLabel(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.color = C["text"]

class ThemedButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = C["primary"]
        self.background_normal = ''

class ThemedTextInput(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (1, 1, 1, 0.8)
        self.foreground_color = C["text"]

class Card(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'; self.padding = '20dp'; self.spacing = '15dp'
        self.size_hint_y = None; self.bind(minimum_height=self.setter('height'))
        with self.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            Color(*C["card"])
            self.rect = RoundedRectangle(radius=[(10, 10)] * 4)
        self.bind(pos=self.update_rect, size=self.update_rect)
    def update_rect(self, *args):
        self.rect.pos = self.pos; self.rect.size = self.size

# ==================== Global Helper Functions ====================
def show_popup_global(title, message):
    content = BoxLayout(orientation='vertical', padding='10dp', spacing='10dp')
    msg_label = ThemedLabel(text=message, size_hint_y=None, halign='left', valign='top', color=C["text_secondary"])
    msg_label.bind(width=lambda *x: msg_label.setter('text_size')(msg_label, (msg_label.width, None)))
    msg_label.bind(texture_size=lambda *x: msg_label.setter('height')(msg_label, msg_label.texture_size[1]))
    scroll_view = ScrollView(size_hint=(1, 1)); scroll_view.add_widget(msg_label)
    btn = ThemedButton(text='关闭', size_hint_y=None, height='44dp')
    content.add_widget(scroll_view); content.add_widget(btn)
    popup = Popup(
        title=title, title_color=C["primary"], content=content, size_hint=(0.9, 0.6),
        separator_color=C["primary"], background='', background_color=C["card"]
    )
    btn.bind(on_press=popup.dismiss); popup.open()

# ==================== DataManager (New Addition) ====================
class DataManager:
    """Handles all logic related to reading from and writing to the daily Excel file."""
    def get_output_path(self):
        """Generates the file path for today's data file."""
        if platform == 'android':
            output_dir = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS).getAbsolutePath()
        else:
            output_dir = os.path.expanduser('~/Downloads')
        
        # 确保目录存在
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        today_str = datetime.now().strftime("%Y%m%d")
        return os.path.join(output_dir, f'录入结果_{today_str}.xlsx')

    def load_daily_data(self):
        """Loads data from today's file into a DataFrame."""
        output_file = self.get_output_path()
        if os.path.exists(output_file):
            return pd.read_excel(output_file, engine='openpyxl')
        return pd.DataFrame(columns=DATA_COLUMN_ORDER)

    def save_daily_data(self, df):
        """Saves the given DataFrame to today's file."""
        output_file = self.get_output_path()
        df = df.reindex(columns=DATA_COLUMN_ORDER)
        df.to_excel(output_file, index=False)
        
    def append_data(self, data_dict):
        """Appends a new row of data to today's file."""
        df = self.load_daily_data()
        new_row = pd.DataFrame([data_dict])
        df = pd.concat([df, new_row], ignore_index=True)
        self.save_daily_data(df)

# ==================== Database Class (Unchanged) ====================
class AssetDatabase:
    def __init__(self, excel_path):
        try:
            self.df = pd.read_excel(excel_path, header=2, engine='openpyxl')
        except FileNotFoundError:
            self.df = pd.DataFrame(); raise
        missing_cols = [col for col in REQUIRED_COLUMNS if col not in self.df.columns]
        if missing_cols: raise KeyError(f"Excel文件缺少必要的列: {', '.join(missing_cols)}")
        self.df.dropna(subset=['原表资产号'], inplace=True)
        self.df['原表资产号'] = self.df['原表资产号'].astype(str).str.strip()
    def get_info_by_last_6_digits(self, last_6_digits):
        last_6_digits = str(last_6_digits).strip()
        if not last_6_digits: return []
        matches = self.df[self.df['原表资产号'].str.endswith(last_6_digits)].copy()
        return matches.to_dict('records')

# ==================== UI Screens ====================
class StartupScreen(Screen):
    ACTIVITY_RESULT_FILE_PICKER = 101
    log_text = StringProperty("文件操作日志:\n")
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()
        if platform == 'android': self.android_init()
    def build_ui(self):
        root = BoxLayout(orientation='vertical', padding='20dp', spacing='20dp')
        header = BoxLayout(size_hint_y=None, height='60dp')
        header.add_widget(ThemedLabel(text="轮换表计录入系统", font_size='24sp', bold=True, halign='center'))
        root.add_widget(header)
        main_card = Card()
        main_card.add_widget(ThemedLabel(text="请选择包含客户数据的Excel台账文件 (.xlsx)", size_hint_y=None, height='30dp'))
        path_layout = BoxLayout(size_hint_y=None, height='44dp', spacing='10dp')
        self.excel_path_input = ThemedTextInput(
            hint_text="点击“浏览”选择文件...", text=os.path.join(os.getcwd(), 'assets', '轮换表计台账.xlsx'),
            readonly=True, font_size='12sp'
        )
        path_layout.add_widget(self.excel_path_input)
        browse_btn = ThemedButton(text="浏览", size_hint_x=0.25); browse_btn.bind(on_press=self.browse_file)
        path_layout.add_widget(browse_btn); main_card.add_widget(path_layout)
        start_btn = ThemedButton(text="启动系统", size_hint_y=None, height='44dp'); start_btn.bind(on_press=self.start_app)
        main_card.add_widget(start_btn); root.add_widget(main_card)
        log_card = Card(padding=('10dp', '10dp'))
        log_card.add_widget(ThemedLabel(text="操作日志", size_hint_y=None, height='30dp', color=C["text_secondary"]))
        log_scroll = ScrollView()
        self.log_textinput = ThemedTextInput(
            text=self.log_text, readonly=True, font_size='12sp', background_color=(0,0,0,0), padding_y='5dp'
        )
        log_scroll.add_widget(self.log_textinput); log_card.add_widget(log_scroll); root.add_widget(log_card)
        footer = ThemedLabel(text="延寿供电所 - K-2025年制", font_size='12sp', size_hint_y=None, height='30dp', color=C["text_secondary"])
        root.add_widget(footer); self.add_widget(root); self.add_log("系统初始化完成。")
    def add_log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S"); log_entry = f"[{timestamp}] {message}\n"
        self.log_text += log_entry; self.log_textinput.text = self.log_text
        self.log_textinput.cursor = (0, len(self.log_textinput.text))
    def android_init(self):
        activity.bind(on_activity_result=self.on_activity_result)
        self.request_android_permissions()
    def request_android_permissions(self):
        try:
            if platform != 'android': return
            if not check_permission(Permission.READ_EXTERNAL_STORAGE) or not check_permission(Permission.WRITE_EXTERNAL_STORAGE):
                request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
                self.add_log("已请求存储权限")
        except Exception as e:
            self.add_log(f"权限请求错误: {e}")
            Clock.schedule_once(lambda dt: self.show_popup("权限错误", f"无法请求安卓权限: {e}"))
    def browse_file(self, instance):
        if platform == 'android': self.open_android_file_chooser()
        else:
            try:
                from plyer import filechooser
                filechooser.open_file(on_selection=self.handle_selection, title="请选择台账Excel文件", filters=[("Excel Files", "*.xlsx", "*.xls")])
            except ImportError: self.show_popup("功能缺失", "文件选择功能需要安装'plyer'库。\n请运行: pip install plyer")
    def handle_selection(self, selection):
        if selection: self.excel_path_input.text = selection[0]
    def open_android_file_chooser(self):
        try:
            intent = Intent(Intent.ACTION_OPEN_DOCUMENT); intent.addCategory(Intent.CATEGORY_OPENABLE); intent.setType("*/*")
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION)
            PythonActivity.mActivity.startActivityForResult(intent, self.ACTIVITY_RESULT_FILE_PICKER)
        except Exception as e: self.show_popup("文件选择错误", f"无法打开文件选择器: {e}")
    def on_activity_result(self, request_code, result_code, intent):
        Clock.schedule_once(lambda dt: self._process_activity_result(request_code, result_code, intent))
    def _process_activity_result(self, request_code, result_code, intent):
        if request_code != self.ACTIVITY_RESULT_FILE_PICKER or result_code != -1: return
        try:
            uri = intent.getData()
            if not uri: return
            context = PythonActivity.mActivity.getApplicationContext()
            context.getContentResolver().takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION)
            self.copy_and_process_uri(uri)
        except Exception as e: self.show_popup("文件处理错误", f"处理文件URI时出错: {e}\n{traceback.format_exc()}")
    def copy_and_process_uri(self, uri):
        try:
            context = PythonActivity.mActivity.getApplicationContext()
            cache_dir = context.getCacheDir().getAbsolutePath()
            cursor = context.getContentResolver().query(uri, None, None, None, None)
            file_name = f"台账_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            if cursor and cursor.moveToFirst():
                name_index = cursor.getColumnIndex('_display_name')
                file_name = cursor.getString(name_index)
            if cursor: cursor.close()
            local_path = os.path.join(cache_dir, file_name)
            with context.getContentResolver().openInputStream(uri) as input_stream, FileOutputStream(local_path) as output_stream:
                buffer = bytearray(4096)
                while True:
                    length = input_stream.read(buffer)
                    if length == -1: break
                    output_stream.write(buffer, 0, length)
            self.excel_path_input.text = local_path
        except Exception as e: self.show_popup("文件复制错误", f"无法复制文件: {e}\n{traceback.format_exc()}")
    def start_app(self, instance):
        excel_path = self.excel_path_input.text.strip()
        if not os.path.exists(excel_path): self.show_popup("错误", f"文件不存在: {excel_path}"); return
        try:
            app = App.get_running_app()
            app.asset_db = AssetDatabase(excel_path)
            app.data_manager = DataManager() # 初始化DataManager
            self.manager.get_screen('main').reset_session()
            self.manager.current = 'main'
        except Exception as e: self.show_popup("启动错误", f"加载Excel时发生错误: {e}\n{traceback.format_exc()}")
    def show_popup(self, title, message): show_popup_global(title, message)

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_count = 0; self.state = 'INPUT'; self.user_info = {}
        self.layout = BoxLayout(orientation='vertical', padding='20dp', spacing='20dp')
        self.add_widget(self.layout)
    def on_enter(self, *args):
        # 每次进入界面时，都重新加载当日数据并更新UI
        self.reset_session()
        self.update_ui_for_state()
    def reset_session(self):
        self.state = 'INPUT'
        self.update_daily_count()
    def update_daily_count(self):
        """检查当日文件并更新计数"""
        try:
            df = App.get_running_app().data_manager.load_daily_data()
            self.current_count = len(df)
            if hasattr(self, 'stats_label'):
                self.stats_label.text = f'本日已录入: {self.current_count} 条'
        except Exception:
            self.current_count = 0

    def update_ui_for_state(self):
        self.layout.clear_widgets()
        header = BoxLayout(orientation='vertical', size_hint_y=None, height='60dp')
        title = ThemedLabel(text="数据录入", font_size='24sp', bold=True)
        self.stats_label = ThemedLabel(text=f'本日已录入: {self.current_count} 条', font_size='14sp', color=C["text_secondary"])
        header.add_widget(title); header.add_widget(self.stats_label); self.layout.add_widget(header)
        
        if self.state == 'INPUT': self.build_input_ui()
        elif self.state == 'VERIFY': self.build_verification_ui()
        elif self.state == 'FORM': self.build_form_ui()
        
        footer_layout = BoxLayout(size_hint_y=None, height='44dp', spacing='10dp')
        back_to_start_btn = ThemedButton(text="返回首页"); back_to_start_btn.bind(on_press=self.back_to_start)
        footer_layout.add_widget(back_to_start_btn)
        
        # 新增“管理数据”按钮
        edit_data_btn = ThemedButton(text="管理当日数据"); edit_data_btn.bind(on_press=self.go_to_edit_screen)
        footer_layout.add_widget(edit_data_btn)
        
        self.layout.add_widget(footer_layout)
        
    def build_input_ui(self):
        scroll_view = ScrollView(size_hint=(1, 1)); card = Card()
        card.add_widget(ThemedLabel(text="输入原表资产号后6位进行查询:", size_hint_y=None, height='30dp'))
        self.asset_input = ThemedTextInput(multiline=False, size_hint_y=None, height='44dp', hint_text='例如: 123456', font_size='16sp')
        self.asset_input.focus = True; card.add_widget(self.asset_input)
        submit_btn = ThemedButton(text='提交查询', size_hint_y=None, height='44dp'); submit_btn.bind(on_press=self.check_asset)
        card.add_widget(submit_btn); scroll_view.add_widget(card); self.layout.add_widget(scroll_view)
    def build_verification_ui(self):
        scroll_view = ScrollView(size_hint=(1, 1)); card = Card()
        user_text = (f"[b]客户号:[/b] {self.user_info.get('客户号', 'N/A')}\n"
                     f"[b]用户名:[/b] {self.user_info.get('用户名', 'N/A')}\n"
                     f"[b]原表资产号:[/b] {self.user_info.get('原表资产号', 'N/A')}")
        info_label = ThemedLabel(text=user_text, markup=True, line_height=1.5, size_hint_y=None)
        info_label.bind(width=lambda *x: info_label.setter('text_size')(info_label, (info_label.width, None)))
        info_label.bind(texture_size=lambda *x: info_label.setter('height')(info_label, info_label.texture_size[1]))
        card.add_widget(info_label)
        card.add_widget(ThemedLabel(text='请核对以上信息是否正确?', color=C["accent"], bold=True, size_hint_y=None, height='44dp'))
        btn_layout = BoxLayout(size_hint_y=None, height='44dp', spacing='10dp')
        correct_btn = ThemedButton(text='正确, 下一步'); correct_btn.bind(on_press=lambda x: self.change_state('FORM'))
        incorrect_btn = Button(text='错误, 返回', background_color=C["text_secondary"], background_normal=''); incorrect_btn.bind(on_press=lambda x: self.change_state('INPUT'))
        btn_layout.add_widget(correct_btn); btn_layout.add_widget(incorrect_btn); card.add_widget(btn_layout)
        scroll_view.add_widget(card); self.layout.add_widget(scroll_view)

    def build_form_ui(self):
        form_container = BoxLayout(orientation='vertical', spacing='10dp')
        scroll_view = ScrollView(size_hint=(1, 1))
        card = Card()
        
        header_text = (f"正在为 [b]{self.user_info.get('用户名', '')}[/b] 录入新表信息\n"
                       f"原资产号: {self.user_info.get('原表资产号', 'N/A')}")
        card.add_widget(ThemedLabel(text=header_text, markup=True, size_hint_y=None, height='60dp', line_height=1.4))
        
        form_layout = GridLayout(cols=1, spacing='10dp', size_hint_y=None)
        form_layout.bind(minimum_height=form_layout.setter('height'))
        self.inputs = {}
        fields = [
            ('原表表码', 'old_meter', str(self.user_info.get('原表表码', ''))), ('新资产号', 'new_asset', ''),
            ('铅封号', 'seal_number', ''), ('材料使用', 'material_usage', ''), ('备注', 'remark', '')
        ]
        for label_text, name, default in fields:
            form_layout.add_widget(ThemedLabel(text=label_text, halign='left', size_hint_y=None, height='20dp'))
            inp = ThemedTextInput(text=default, multiline=False, size_hint_y=None, height='44dp')
            self.inputs[name] = inp
            form_layout.add_widget(inp)
        form_layout.add_widget(ThemedLabel(text='表计类型', halign='left', size_hint_y=None, height='20dp'))
        
        self.inputs['meter_type'] = Spinner(
            text='单相表', values=('单相表', '三相表'), size_hint_y=None, height='44dp', 
            background_color=C["accent"]
        )
        form_layout.add_widget(self.inputs['meter_type'])
      
        form_layout.add_widget(ThemedLabel(text='表箱类型', halign='left', size_hint_y=None, height='20dp'))
        self.inputs['box_type'] = Spinner(
            text='利旧未换', values=('利旧未换', '单位', '双位', '双位单装'),
            size_hint_y=None, height='44dp', background_color=C["accent"]
        )
        form_layout.add_widget(self.inputs['box_type'])
        
        card.add_widget(form_layout)
        scroll_view.add_widget(card)
        form_container.add_widget(scroll_view)
        btn_layout = BoxLayout(size_hint_y=None, height='44dp', spacing='10dp')
        submit_btn = ThemedButton(text='提交保存'); submit_btn.bind(on_press=self.save_data)
        btn_layout.add_widget(submit_btn)
        back_btn = Button(text='返回上一步', background_color=C["text_secondary"], background_normal=''); back_btn.bind(on_press=lambda x: self.change_state('VERIFY'))
        btn_layout.add_widget(back_btn)
        form_container.add_widget(btn_layout)
        self.layout.add_widget(form_container)

    def change_state(self, new_state):
        self.state = new_state
        self.update_ui_for_state()

    def go_to_edit_screen(self, instance):
        self.manager.current = 'edit'

    def back_to_start(self, instance): self.manager.current = 'start'
    def check_asset(self, instance):
        last_6_digits = self.asset_input.text.strip()
        if not last_6_digits: self.show_popup("输入错误", "资产号不能为空。"); return
        matches = App.get_running_app().asset_db.get_info_by_last_6_digits(last_6_digits)
        self.asset_input.text = ""
        if not matches: self.show_popup("未找到记录", f"数据库中不存在以 '{last_6_digits}' 结尾的资产号。")
        elif len(matches) == 1: self.user_info = matches[0]; self.change_state('VERIFY')
        else: self.show_duplicate_selection_popup(matches)
    def show_duplicate_selection_popup(self, matches):
        content = GridLayout(cols=1, spacing='10dp', size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))
        content.add_widget(ThemedLabel(text="发现多条重复数据，请选择正确的一条:", size_hint_y=None, height='44dp'))
        for record in matches:
            display_text = f"客户号: {record['客户号']} | 用户名: {record['用户名']}\n资产号: {record['原表资产号']}"
            btn = ThemedButton(text=display_text, size_hint_y=None, height='60dp', text_size=(Window.width * 0.7, None), halign='center')
            btn.bind(on_press=partial(self.select_duplicate, record)); content.add_widget(btn)
        scroll = ScrollView(); scroll.add_widget(content)
        self.popup = Popup(
            title="选择重复数据", title_color=C["primary"], content=scroll, size_hint=(0.9, 0.8),
            background='', background_color=C["card"]
        )
        self.popup.open()
    def select_duplicate(self, record, instance):
        self.popup.dismiss(); self.user_info = record; self.change_state('VERIFY')
        
    def save_data(self, instance):
        data = {'客户号': self.user_info.get('客户号', ''), '用户名': self.user_info.get('用户名', ''),
                '原表资产号': self.user_info.get('原表资产号', ''), '原表表码': self.inputs['old_meter'].text,
                '新资产号': self.inputs['new_asset'].text, '铅封号': self.inputs['seal_number'].text,
                '表计类型': self.inputs['meter_type'].text, '表箱类型': self.inputs['box_type'].text,
                '安装人员': INSTALLER_NAMES, '材料使用': self.inputs['material_usage'].text, '备注': self.inputs['remark'].text,
                '录入时间': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        
        dm = App.get_running_app().data_manager
        output_file = dm.get_output_path()

        try:
            dm.append_data(data)
            self.update_daily_count()
            self.show_popup("保存成功", f"数据已成功保存！\n文件路径:\n{output_file}")
            self.change_state('INPUT')
        except PermissionError: self.show_popup("保存错误", f"无法写入文件！\n请检查应用权限或关闭已打开的Excel文件:\n{output_file}")
        except Exception as e: self.show_popup("未知错误", f"保存数据时发生错误: {str(e)}")
        
    def show_popup(self, title, message): show_popup_global(title, message)


# ==================== EditScreen (New Screen) ====================
class EditScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding='20dp', spacing='20dp')
        self.data_grid = None
        self.add_widget(self.layout)

    def on_enter(self, *args):
        self.populate_data()

    def populate_data(self):
        self.layout.clear_widgets()

        header = BoxLayout(orientation='vertical', size_hint_y=None, height='60dp')
        title = ThemedLabel(text="管理当日数据", font_size='24sp', bold=True)
        header.add_widget(title)
        self.layout.add_widget(header)

        scroll_view = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        self.data_grid = GridLayout(cols=1, spacing='10dp', size_hint_y=None)
        self.data_grid.bind(minimum_height=self.data_grid.setter('height'))

        try:
            dm = App.get_running_app().data_manager
            df = dm.load_daily_data()

            if df.empty:
                self.data_grid.add_widget(ThemedLabel(text="今天还没有录入任何数据。", size_hint_y=None, height='50dp'))
            else:
                for index, row in df.iterrows():
                    record_card = self.create_record_card(index, row)
                    self.data_grid.add_widget(record_card)
        except Exception as e:
            self.data_grid.add_widget(ThemedLabel(text=f"加载数据失败: {e}", size_hint_y=None, height='50dp'))

        scroll_view.add_widget(self.data_grid)
        self.layout.add_widget(scroll_view)

        footer_layout = BoxLayout(size_hint_y=None, height='44dp', spacing='10dp')
        back_btn = ThemedButton(text="返回录入界面"); back_btn.bind(on_press=self.back_to_main)
        refresh_btn = ThemedButton(text="刷新列表"); refresh_btn.bind(on_press=lambda x: self.populate_data())
        footer_layout.add_widget(back_btn)
        footer_layout.add_widget(refresh_btn)
        self.layout.add_widget(footer_layout)

    def create_record_card(self, index, row):
        card = Card(padding='15dp')
        
        # 数据展示
        info_text = (f"[b]用户:[/b] {row.get('用户名', '')} ([b]原资产号:[/b] {row.get('原表资产号', '')})\n"
                     f"[b]新资产号:[/b] {row.get('新资产号', '')} | [b]铅封号:[/b] {row.get('铅封号', '')}")
        info_label = ThemedLabel(text=info_text, markup=True, size_hint_y=None)
        info_label.bind(width=lambda *x: info_label.setter('text_size')(info_label, (info_label.width, None)))
        info_label.bind(texture_size=lambda *x: info_label.setter('height')(info_label, info_label.texture_size[1]))
        card.add_widget(info_label)

        # 按钮
        btn_layout = BoxLayout(size_hint_y=None, height='40dp', spacing='10dp')
        edit_btn = ThemedButton(text="修改")
        edit_btn.bind(on_press=partial(self.show_edit_popup, index, row))
        delete_btn = Button(text="删除", background_color=C["error"], background_normal='')
        delete_btn.bind(on_press=partial(self.confirm_delete, index))
        btn_layout.add_widget(edit_btn)
        btn_layout.add_widget(delete_btn)
        card.add_widget(btn_layout)

        return card
        
    def show_edit_popup(self, index, row, instance):
        content = BoxLayout(orientation='vertical', spacing='10dp', padding='10dp')
        
        # 创建一个可滚动的表单
        form_scroll = ScrollView(size_hint=(1, 1))
        form_layout = GridLayout(cols=1, spacing='10dp', size_hint_y=None)
        form_layout.bind(minimum_height=form_layout.setter('height'))
        
        inputs = {}
        # 注意：这里我们使用DATA_COLUMN_ORDER来确保顺序，并排除一些不需要编辑的字段
        editable_fields = ['原表表码', '新资产号', '铅封号', '材料使用', '备注']
        spinner_fields = {'表计类型': ('单相表', '三相表'), '表箱类型': ('利旧未换', '单位', '双位', '双位单装')}

        for field in DATA_COLUMN_ORDER:
            if field in editable_fields:
                form_layout.add_widget(ThemedLabel(text=field, halign='left', size_hint_y=None, height='20dp'))
                inp = ThemedTextInput(text=str(row.get(field, '')), multiline=False, size_hint_y=None, height='44dp')
                inputs[field] = inp
                form_layout.add_widget(inp)
            elif field in spinner_fields:
                form_layout.add_widget(ThemedLabel(text=field, halign='left', size_hint_y=None, height='20dp'))
                spinner = Spinner(
                    text=str(row.get(field, spinner_fields[field][0])), 
                    values=spinner_fields[field], 
                    size_hint_y=None, height='44dp', 
                    background_color=C["accent"]
                )
                inputs[field] = spinner
                form_layout.add_widget(spinner)
        
        form_scroll.add_widget(form_layout)
        content.add_widget(form_scroll)

        btn_layout = BoxLayout(size_hint_y=None, height='44dp', spacing='10dp')
        save_btn = ThemedButton(text='保存修改')
        cancel_btn = Button(text='取消', background_color=C["text_secondary"], background_normal='')
        btn_layout.add_widget(save_btn)
        btn_layout.add_widget(cancel_btn)
        content.add_widget(btn_layout)

        popup = Popup(title=f"修改 {row.get('用户名', '')} 的数据", content=content, size_hint=(0.9, 0.8),
                      title_color=C["primary"], separator_color=C["primary"],
                      background='', background_color=C["card"])
        
        save_btn.bind(on_press=lambda x: self.save_edit(index, inputs, popup))
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()

    def save_edit(self, index, inputs, popup):
        try:
            dm = App.get_running_app().data_manager
            df = dm.load_daily_data()
            
            for field, widget in inputs.items():
                df.loc[index, field] = widget.text
                
            dm.save_daily_data(df)
            popup.dismiss()
            self.populate_data() # 刷新列表
            show_popup_global("成功", "数据修改已保存。")
        except Exception as e:
            show_popup_global("错误", f"保存修改失败: {e}")

    def confirm_delete(self, index, instance):
        content = BoxLayout(orientation='vertical', padding='10dp', spacing='10dp')
        content.add_widget(ThemedLabel(text="您确定要删除这条记录吗？\n此操作无法撤销。"))
        btn_layout = BoxLayout(size_hint_y=None, height='44dp', spacing='10dp')
        
        confirm_btn = Button(text='确认删除', background_color=C["error"], background_normal='')
        cancel_btn = ThemedButton(text='取消')
        btn_layout.add_widget(confirm_btn)
        btn_layout.add_widget(cancel_btn)
        content.add_widget(btn_layout)
        
        popup = Popup(title="确认删除", content=content, size_hint=(0.8, 0.4), title_color=C["error"])
        
        confirm_btn.bind(on_press=lambda x: self.delete_record(index, popup))
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()
        
    def delete_record(self, index, popup):
        try:
            dm = App.get_running_app().data_manager
            df = dm.load_daily_data()
            df = df.drop(index).reset_index(drop=True)
            dm.save_daily_data(df)
            popup.dismiss()
            self.populate_data() # 刷新列表
            show_popup_global("成功", "记录已删除。")
        except Exception as e:
            show_popup_global("错误", f"删除记录失败: {e}")


    def back_to_main(self, instance):
        self.manager.current = 'main'
        
class ExcelDataEntryApp(App):
    asset_db = ObjectProperty(None)
    data_manager = ObjectProperty(None)
    
    def build(self):
        self.screen_manager = ScreenManager(transition=NoTransition())
        self.screen_manager.add_widget(StartupScreen(name='start'))
        self.screen_manager.add_widget(MainScreen(name='main'))
        self.screen_manager.add_widget(EditScreen(name='edit')) # 添加新屏幕
        return self.screen_manager

if __name__ == '__main__':
    ExcelDataEntryApp().run()
