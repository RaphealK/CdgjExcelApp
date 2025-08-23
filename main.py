from kivy.app import App
from kivy.uix.button import Button
from android import activity
from jnius import autoclass, cast
from android.permissions import request_permissions, Permission

# 获取Java类引用
Intent = autoclass('android.content.Intent')
PythonActivity = autoclass('org.kivy.android.PythonActivity')
Uri = autoclass('android.net.Uri')
DocumentsContract = autoclass('android.provider.DocumentsContract')

class FileChooserApp(App):
    def build(self):
        # 请求存储权限（可选）
        request_permissions([Permission.READ_EXTERNAL_STORAGE])
        
        btn = Button(text='选择文件', size_hint=(0.5, 0.2))
        btn.bind(on_press=self.open_file_chooser)
        return btn

    def open_file_chooser(self, instance):
        # 创建文件选择Intent
        intent = Intent(Intent.ACTION_OPEN_DOCUMENT)
        intent.addCategory(Intent.CATEGORY_OPENABLE)
        intent.setType("*/*")  # 所有文件类型
        
        # 启动系统文件选择器
        current_activity = cast('android.app.Activity', PythonActivity.mActivity)
        current_activity.startActivityForResult(intent, 101)
        
        # 绑定结果回调
        activity.bind(on_activity_result=self.handle_file_result)

    def handle_file_result(self, request_code, result_code, intent):
        if request_code != 101 or result_code != -1:  # -1 = RESULT_OK
            return
            
        uri = intent.getData()
        if not uri:
            return
            
        try:
            # 获取真实路径（方法1：适用于普通文件）
            file_path = self.get_path_from_uri(uri)
            print("文件路径:", file_path)
            
            # 方法2：直接通过URI读取内容
            content = self.read_file_content(uri)
            print("文件内容:", content[:100] + "...")  # 打印前100字符
        except Exception as e:
            print("文件处理错误:", str(e))

    def get_path_from_uri(self, uri):
        """将Content URI转换为真实文件路径"""
        context = PythonActivity.mActivity.getApplicationContext()
        content_resolver = context.getContentResolver()
        
        # 检查URI类型
        if DocumentsContract.isDocumentUri(context, uri):
            doc_id = DocumentsContract.getDocumentId(uri)
            
            # 处理不同存储提供者的URI
            if "com.android.providers.media.documents" in uri.getAuthority():
                # 媒体存储文件
                id_part = doc_id.split(":")[1]
                where = "_id=?"
                uri = Uri.parse("content://media/external/images/media")
            else:
                # 其他文档提供者
                return self.copy_to_cache(uri)  # 无法直接获取路径时复制文件
                
        # 执行查询获取路径
        cursor = content_resolver.query(uri, None, None, None, None)
        if cursor:
            cursor.moveToFirst()
            path_index = cursor.getColumnIndex("_data")
            file_path = cursor.getString(path_index)
            cursor.close()
            return file_path
        return None

    def read_file_content(self, uri):
        """通过URI直接读取文件内容"""
        context = PythonActivity.mActivity.getApplicationContext()
        content_resolver = context.getContentResolver()
        
        input_stream = content_resolver.openInputStream(uri)
        from java.io import BufferedReader, InputStreamReader
        reader = BufferedReader(InputStreamReader(input_stream))
        
        content = []
        line = reader.readLine()
        while line:
            content.append(line)
            line = reader.readLine()
        reader.close()
        return "\n".join(content)

    def copy_to_cache(self, uri):
        """将文件复制到应用缓存目录"""
        context = PythonActivity.mActivity.getApplicationContext()
        content_resolver = context.getContentResolver()
        
        # 创建目标文件
        cache_dir = context.getCacheDir().getPath()
        file_name = "imported_file.tmp"
        dest_path = os.path.join(cache_dir, file_name)
        
        # 复制流
        input_stream = content_resolver.openInputStream(uri)
        with open(dest_path, "wb") as f:
            chunk = input_stream.read(1024)
            while chunk:
                f.write(chunk)
                chunk = input_stream.read(1024)
        input_stream.close()
        return dest_path

if __name__ == '__main__':
    FileChooserApp().run()
