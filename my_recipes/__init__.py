from pythonforandroid.recipe import PythonRecipe

class NumpyRecipe(PythonRecipe):
    # 我们要手动指定的版本
    version = '1.24.4'

    # 我们手动提供的、保证正确的下载链接
    # 注意这里使用了 {version} 占位符，p4a会自动替换它
    url = 'https://files.pythonhosted.org/packages/a4/9b/027bec52c633f6556dba6b722d9a0befb40498b9ceddd29cbe67a45a127c/numpy-{version}.tar.gz'

    # Numpy 编译时需要的一些依赖和设置
    depends = ['hostpython3']
    
    # 避免使用 wheel，强制从源码编译
    install_kws = {'--no-use-pep517': ''}

    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        # 这个环境变量对于在安卓上成功编译Numpy非常重要
        env['NPY_DISABLE_SVML'] = '1'
        return env

# 创建配方实例，这是 p4a 加载配方所必需的
recipe = NumpyRecipe()
