import importlib
from typing import Tuple, List, Optional, Set, Dict
import re
import os
import sys

import traceback
import tkinter as tk
import tkinter.ttk as ttk

from utils.info import log_info


class PluginManager:
    def __init__(self):
        self.plugins: dict[str, tuple] = {}  # 插件名称: (插件类，组件类)
        self.modules = list()
        self.Patterns: List[list[re.Pattern]] = []
        self.Tables: dict[str, dict[str, str]] = {}
        self.wait_for_init_plugins: List[str] = []
        self.widgets: dict[str, object] = {}

    def _import_plugin_module(self, plugin_name):
        try:
            return importlib.import_module(f'test_plugins.{plugin_name}')
        except ImportError as e:
            log_info(f"插件 {plugin_name} 导入失败: {e}", 'error')
            traceback.print_exc()
            return None

    def get_modules(self):
        """
        获取插件, 包括已加载的插件
        使用modules属性, 而非plugins属性
        在实例化插件类之前调用
        """
        return self.modules

    def load_plugins(self):
        """
        加载插件
        """
        plugin_dir = os.path.join(os.getcwd(), 'test_plugins')  # 假设当前工作目录为根目录，可根据实际情况修改
        if not os.path.exists(plugin_dir) or not os.path.isdir(plugin_dir):
            print("插件目录不存在或不是目录")
            return
        for file in os.listdir(plugin_dir):
            result = self._load_plugin(file)
            if result["Loaded"] or not result["can_load"]:
                continue
            elif result["can_load"]:
                self.wait_for_init_plugins.append(file[:-3])
                self.modules.append(file[:-3])
                self.Patterns.append([re.compile(pattern) for pattern in result["SitePatterns"]])
                self.Tables[result["TableName"]] = result["TableColumns"]
                log_info(f"插件 {file} 加载成功, 等待创建实例")
            else:
                print(f"插件 {file} 获取失败, 无法加载")

    def init_plugins(self, plugin: str, labelframe: ttk.Labelframe):
        log_info(f"插件{plugin}: 创建实例, 组件实例: {labelframe}")
        if plugin not in self.wait_for_init_plugins:
            return
        module = self._import_plugin_module(plugin)
        temp_list = [None,None]
        # 实例化插件类和组件类
        # 强烈建议不要在插件中调用其他插件的组件类, 否则会导致页面混乱
        for attr in dir(module):
            if attr.endswith("Shower"):
                log_info(f"插件{plugin}: 找到组件类 {attr}")
                shower_instance = getattr(module, attr)(labelframe)
                temp_list[1] = shower_instance
                self.widgets[plugin] = shower_instance
                break
        for attr in dir(module):
            if attr.endswith("HTMLParser"):
                parser = getattr(module, attr)()
                temp_list[0] = parser
                break
        self.plugins[plugin] = tuple(temp_list)
        self.wait_for_init_plugins.remove(plugin)

    def _load_plugin(self, file: str) -> dict:
        """
        加载单个插件
        """
        result = {
            "Loaded": False,
            "TableName": "",
            "TableColumns": [],
            "SitePatterns": [],
            "can_load": False,
        }
        if file.endswith('HTMLParser.py'):
            module_name = file[:-3]
            if module_name in self.modules:
                # 已经加载过该插件，跳过
                result["Loaded"] = True
                return result
            module = self._import_plugin_module(module_name)
            if module is None:
                return result
            html_parser_class = None
            shower_class = None
            for attr in dir(module):
                if attr.endswith("HTMLParser"):
                    html_parser_class = getattr(module, attr)
                    result["TableName"] = html_parser_class.TableName
                    result["TableColumns"] = html_parser_class.TableColumns
                    result["SitePatterns"] = html_parser_class.SitePatterns
                elif attr.endswith("Shower"):
                    shower_class = getattr(module, attr)
            if html_parser_class:
                result["can_load"] = True
        return result

    def parser(self, url: str) -> Optional[Dict]:
        """
        解析url, 返回 解析类实例 和 组件类实例 的元组
        """
        if not self.Patterns:
            print("该链接没有可用的插件")
            return None
        result = {
            "index": -1,
            "object": tuple()
        }
        for i, patterns in enumerate(self.Patterns):
            for pattern in patterns:
                if pattern.match(url):
                    plugin_name = list(self.plugins.keys())[i]
                    result["index"] = i
                    result["object"] = self.plugins[plugin_name]
                    return result
        return None

# 用于插件测试
class GUI:
    Manager = PluginManager()
    def __init__(self):
        self.master = tk.Tk()
        self.labelframe = ttk.LabelFrame(self.master, text="Plugin Test")
        self.labelframe.pack(padx=10, pady=10)
        self.Manager.load_plugins()
        self.Manager.init_plugins("test_plugin", self.labelframe)
        self.master.mainloop()


if __name__ == '__main__':
    GUI()