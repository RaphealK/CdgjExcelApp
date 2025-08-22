import os
import pandas as pd
from datetime import datetime

# ==================== Kivy & Font Setup (No changes needed here) ====================
from kivy.core.text import LabelBase
from kivy.resources import resource_add_path
font_path = os.path.join(os.getcwd(), 'fonts')
if os.path.exists(font_path):
    resource_add_path(font_path)
    LabelBase.register(name='Roboto', fn_regular='msyh.ttc')
# ===================================================================================

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.spinner import Spinner

try:
    from plyer import filechooser
except ImportError:
    filechooser = None

# ==================== OPTIMIZATION: Global Constants ====================
# Define required columns for validation. Makes it easy to add more later.
REQUIRED_COLUMNS = ['客户号', '用户名', '原表资产号', '原表表码']
# Define default installers. Easy to update this list in one place.
INSTALLER_NAMES = '胡军明、胡柏兴、胡海亮、梁群平'
# ========================================================================


class AssetDatabase:
    def __init__(self, excel_path):
        try:
            self.df = pd.read_excel(excel_path, header=2)
        except FileNotFoundError:
            self.df = pd.DataFrame() 
            raise 

        # --- OPTIMIZATION: Stricter validation on startup ---
        # Check if all required columns exist in the loaded Excel file.
        missing_cols = [col for col in REQUIRED_COLUMNS if col not in self.df.columns]
        if missing_cols:
            raise KeyError(f"Excel文件缺少必要的列: {', '.join(missing_cols)}")

        # Clean data after validation
        self.df.dropna(subset=['原表资产号'], inplace=True)
        self.df['原表资产号'] = self.df['原表资产号'].astype(str).str.strip()
        
    def get_info_by_last_6_digits(self, last_6_digits):
        last_6_digits = str(last_6_digits).strip()
        if not last_6_digits:
            return []
        
        matches = self.df[self.df['原表资产号'].str.endswith(last_6_digits)].copy()
        return matches.to_dict('records')

class StartupScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
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
        
        # --- SIGNATURE ADDED ---
        layout.add_widget(Label(
            text="延寿供电所-K-2025年制", 
            font_size='12sp', 
            size_hint_y=None, 
            height=30, 
            color=(0.5, 0.5, 0.5, 1)
        ))
        
        self.add_widget(layout)
    
    def browse_file(self, instance):
        if filechooser:
            try:
                paths = filechooser.open_file(title="请选择台账Excel文件", filters=[("Excel Files", "*.xlsx", "*.xls")])
                if paths: self.excel_path_input.text = paths[0]
            except Exception as e:
                self.show_popup("错误", f"无法打开文件选择器: {e}")
        else:
            self.show_popup("功能缺失", "文件选择功能需要安装'plyer'库。\n请运行: pip install plyer")

    def start_app(self, instance):
        excel_path = self.excel_path_input.text.strip()
        if not os.path.exists(excel_path):
            self.show_popup("错误", f"文件不存在: {excel_path}")
            return
        
        app = App.get_running_app()
        try:
            app.asset_db = AssetDatabase(excel_path)
            # Switch to the main screen upon successful loading
            main_screen = self.manager.get_screen('main')
            main_screen.reset_session() # Reset counter for new session
            self.manager.current = 'main'
        except KeyError as e:
            self.show_popup("Excel读取错误", str(e))
        except Exception as e:
            self.show_popup("启动错误", f"加载Excel时发生未知错误: {str(e)}")

    def show_popup(self, title, message):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=message))
        btn = Button(text='关闭', size_hint_y=0.3)
        popup = Popup(title=title, content=content, size_hint=(0.8, 0.5))
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        popup.open()

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
        self.create_input_ui() # Rebuild UI to show 0
        
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

        # --- SIGNATURE ADDED ---
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
        
        # --- UX IMPROVEMENT: Clear input after submission ---
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
            btn.bind(on_press=lambda x, rec=record: self.select_duplicate(rec))
            content.add_widget(btn)

        self.popup = Popup(title="选择重复数据", content=content, size_hint=(0.9, 0.8))
        self.popup.open()
        
    def select_duplicate(self, record):
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
        correct_btn.bind(on_press=lambda x: self.show_detail_input(user_info))
        incorrect_btn = Button(text='错误，返回')
        incorrect_btn.bind(on_press=lambda x: self.create_input_ui())
        btn_layout.add_widget(correct_btn)
        btn_layout.add_widget(incorrect_btn)
        self.layout.add_widget(btn_layout)

    def show_detail_input(self, user_info):
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
            
        # Spinner for '表计类型'
        form_layout.add_widget(Label(text='表计类型'))
        self.inputs['meter_type'] = Spinner(text='单相表', values=('单相表', '三相表'), size_hint_y=None, height=44)
        form_layout.add_widget(self.inputs['meter_type'])
        
        # ==================== 修改开始 ====================
        # Spinner for '表箱类型' - Added '双位单装' to the values list
        form_layout.add_widget(Label(text='表箱类型'))
        self.inputs['box_type'] = Spinner(
            text='利旧未换', 
            values=('利旧未换', '单位', '双位', '双位单装'), # <--- 核心改动
            size_hint_y=None, 
            height=44
        )
        form_layout.add_widget(self.inputs['box_type'])
        # ==================== 修改结束 ====================

        self.layout.add_widget(form_layout)
        
        btn_layout = BoxLayout(size_hint_y=0.1, spacing=10)
        submit_btn = Button(text='提交保存')
        submit_btn.bind(on_press=self.save_data)
        btn_layout.add_widget(submit_btn)
        
        back_btn = Button(text='返回上一步')
        back_btn.bind(on_press=lambda x: self.show_verification_screen(self.user_info))
        btn_layout.add_widget(back_btn)
        self.layout.add_widget(btn_layout)

    def save_data(self, instance):
        data = {
            '客户号': self.user_info.get('客户号', ''), '用户名': self.user_info.get('用户名', ''),
            '原表资产号': self.user_info.get('原表资产号', ''), '原表表码': self.inputs['old_meter'].text,
            '新资产号': self.inputs['new_asset'].text, '铅封号': self.inputs['seal_number'].text,
            '表计类型': self.inputs['meter_type'].text, '表箱类型': self.inputs['box_type'].text,
            '安装人员': INSTALLER_NAMES, # Use constant
            '材料使用': self.inputs['material_usage'].text, '备注': self.inputs['remark'].text,
            '录入时间': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if self.output_path is None:
            now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_path = os.path.join(os.getcwd(), f'录入结果_{now_str}.xlsx')

        self.save_to_excel(data)
        
    def save_to_excel(self, data):
        try:
            new_row = pd.DataFrame([data])
            df = pd.read_excel(self.output_path) if os.path.exists(self.output_path) else pd.DataFrame()
            df = pd.concat([df, new_row], ignore_index=True)
            
            column_order = [
                '客户号', '用户名', '原表资产号', '原表表码', '新资产号',
                '表计类型', '铅封号', '表箱类型', '材料使用', '安装人员',
                '备注', '录入时间'
            ]
            df.reindex(columns=column_order).to_excel(self.output_path, index=False)

            # --- Move success logic here to ensure it only runs after successful save ---
            self.current_count += 1
            self.show_popup("成功", "数据已保存！")
            self.create_input_ui()
            self.stats_label.text = f'本轮已录入: {self.current_count}条'

        # --- OPTIMIZATION: Specific error for locked file ---
        except PermissionError:
            self.show_popup("保存错误", f"无法写入文件！\n请先关闭已打开的Excel文件:\n{self.output_path}")
        except Exception as e:
            self.show_popup("保存错误", f"保存数据时出错: {str(e)}")

    def export_data(self, instance):
        if self.output_path and os.path.exists(self.output_path):
            self.show_popup("导出成功", f"数据已保存到:\n{self.output_path}")
        else:
            self.show_popup("警告", "尚未录入任何数据，无文件可导出")

    def show_popup(self, title, message):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=message, size_hint=(1, 1)))
        btn = Button(text='关闭', size_hint_y=0.3)
        popup = Popup(title=title, content=content, size_hint=(0.8, 0.5))
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        popup.open()

class ExcelDataEntryApp(App):
    def build(self):
        self.screen_manager = ScreenManager()
        self.screen_manager.add_widget(StartupScreen(name='start'))
        self.screen_manager.add_widget(MainScreen(name='main'))
        return self.screen_manager

if __name__ == '__main__':
    ExcelDataEntryApp().run()