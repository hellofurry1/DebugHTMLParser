import os
import re
import json
import sqlite3
import sys
import threading
import traceback
import requests
import importlib
import websocket
import tkinter as tk
from tkinter import ttk
from concurrent import futures
from typing import Tuple, List, Optional, Set, Dict

from bs4 import BeautifulSoup

from utils.taskkill import kill_process
from utils.info import log_info
WorkDir = os.path.dirname(os.path.abspath(__file__))

class first_using_windows:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("使用须知")
        self.root.geometry("800x600")
        self.root.resizable(False, False)
        self.init_ui()
        self.root.mainloop()
    def init_ui(self):
        self.label = tk.Label(self.root, text="使用提醒", font=("Arial", 20))
        self.text_var = tk.StringVar()
        self.text_label = tk.Label(self.root, textvariable=self.text_var, font=("Arial", 14))
        self.text_label.pack(pady=20)
        self.text_var.set("""
1. 本代码由 AI 辅助完成。
2. 本代码仅提供:
   - 窗口界面
   - 数据获取
   - 日志记录
   - 数据库操作
   - 插件加载
3. 本代码基于插件加载来实现功能扩展。
4. 插件开发需完成以下功能:
   - 实现HTMLParser类，用于解析网页内容
   - 实现Shower类，用于展示解析结果
   - 实现数据查询和判断逻辑
更多功能待开发...
""")

if not os.path.exists(os.path.join(WorkDir, 'data.db')):
    windows = first_using_windows()



class DataBase:
    def __init__(self):
        try:
            self.conn = sqlite3.connect(os.path.join(WorkDir, 'data.db'), check_same_thread=False)
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            log_info(f"数据库连接失败: {e}", 'error')

    def create_table(self, table_name: str, columns: list[tuple]):
        """
        创建表，columns为列名和数据类型元组的列表
        """
        # 更好的做法是将时间戳存储相关逻辑从这里分离
        columns.append(("now", "DATETIME DEFAULT current_timestamp"))  # 假设使用REAL类型存储时间戳数值
        try:
            # 更安全的表名处理方式可以考虑一些验证和转义逻辑
            self.cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join([f'{col[0]} {col[1]}' for col in columns])})")
            self.conn.commit()
        except sqlite3.Error as e:
            log_info(f"创建表 {table_name} 失败: {e}", 'error')

    def insert_data(self, table_name: str, data: list | tuple | dict):
        """
        插入数据，data为列表或元组
        """
        if isinstance(data, dict):
            data = [tuple(data.values())]
        try:
            self.cursor.executemany(f"INSERT INTO {table_name} VALUES ({', '.join(['?' for _ in range(len(data[0]))])})", data)
            self.conn.commit()
        except sqlite3.Error as e:
            log_info(f"插入数据 {data} 到表 {table_name} 失败: {e}", 'error')

    def rollback_new_data(self, table_name: str):
        """
        回滚最新插入的数据
        """
        try:
            self.cursor.execute(f"DELETE FROM {table_name} WHERE now = (SELECT MAX(now) FROM {table_name})")
            self.conn.commit()
        except sqlite3.Error as e:
            log_info(f"回滚最新插入的数据 {table_name} 失败: {e}", 'error')

    def rollback_with_condition(self, table_name: str, condition: str):
        """
        回滚指定条件的数据
        """
        try:
            self.cursor.execute(f"DELETE FROM {table_name} WHERE {condition}")
            self.conn.commit()
        except sqlite3.Error as e:
            log_info(f"回滚指定条件的数据 {table_name} 失败: {e}", 'error')

    def __del__(self):
        self.conn.commit()
        self.conn.close()


class PluginManager:
    def __init__(self):
        self.plugins: dict[str, tuple] = {}  # 插件名称: (插件类，组件类)
        self.modules = list()
        self.Patterns: List[list[re.Pattern]] = []
        self.Tables: dict[str, dict[str, str]] = {}
        self.wait_for_init_plugins: List[str] = []
        self.widgets: dict[str, ttk.Widget] = {}  # 假设Shower类实例化后是ttk.Widget的子类

    def _import_plugin_module(self, plugin_name):
        try:
            return importlib.import_module(f'plugins.{plugin_name}')
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
        plugin_dir = os.path.join(os.getcwd(), 'plugins')  # 假设当前工作目录为根目录，可根据实际情况修改
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
                    plugin_name = list(self.plugins.keys())[i]  # 假设插件名称顺序与Patterns一致
                    result["index"] = i
                    result["object"] = self.plugins[plugin_name]
                    return result
        return None

db_obj = DataBase()

class AppGUI:
    Manager = PluginManager()
    DataBase = db_obj

    def __init__(self, master):
        self.master = master
        master.title("Edge Operation")
        master.geometry("770x400")
        master.attributes("-topmost", True)
        self.parsing = threading.Event()
        self.parsing.set()  # 允许解析
        self.Manager.load_plugins()
        self.create_left_part()
        self.create_right_part()


    def create_left_part(self):
        """
        创建主窗口左侧部分的界面
        """
        self.left_frame = tk.Frame(self.master, width=325)
        self.left_frame.pack_propagate(False)  # 防止子组件改变框架大小
        self.left_frame.pack(side="left", fill="y")  # 让其在左侧填充y方向

        self.setting_frame = ttk.LabelFrame(self.left_frame, text="设置")
        self.setting_frame.pack(fill="none", padx=5, pady=5)

        ttk.Label(self.setting_frame, text="调试端口:").grid(row=0, column=0, padx=5, pady=5)
        self.debug_port_entry = ttk.Entry(self.setting_frame, width=10)
        self.debug_port_entry.insert(0, "9222")
        self.debug_port_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(self.setting_frame, text="超时时间:").grid(row=0, column=2, padx=5, pady=5)
        self.timeout_entry = ttk.Entry(self.setting_frame, width=10)
        self.timeout_entry.insert(0, "10")
        self.timeout_entry.grid(row=0, column=3, padx=5, pady=5)

        self.btn_frame = ttk.LabelFrame(self.left_frame)
        self.btn_frame.pack(fill="none", padx=5, pady=5)
        self.refresh_data_btn = ttk.Button(self.btn_frame, text="刷新数据", command=self.get_data)
        self.refresh_data_btn.pack(side="left", padx=5, pady=5)
        self.task_kill_btn = ttk.Button(self.btn_frame, text="重启Edge进程", command=self.start_task)
        self.task_kill_btn.pack(side="left", padx=5, pady=5)

        self.get_html_btn = ttk.Button(self.btn_frame, text="获取HTML", command=self.get_html_thread)
        self.get_html_btn.pack(side="left", padx=5, pady=5)

        self.data_shower_frame = ttk.LabelFrame(self.left_frame, text="数据展示")
        self.data_viewer_tree = ttk.Treeview(
            self.data_shower_frame, columns=("title", "url"),
            show="headings", height=5)
        self.data_viewer_tree.heading("title", text="标题")
        self.data_viewer_tree.heading("url", text="链接")
        self.data_viewer_tree.column("title", width=150, stretch=False)
        self.data_viewer_tree.column("url", width=150, stretch=False)
        self.data_viewer_tree.pack(fill="none", expand=True, padx=5, pady=5)
        self.data_shower_frame.pack(fill="none", expand=True, padx=5, pady=5)
        self.data_viewer_tree.bind("<Double-1>", self.get_html_thread)


        self.status_labelframe = ttk.LabelFrame(self.left_frame, text="状态")
        self.status_labelframe.pack(fill="x", padx=5, pady=5, side=tk.BOTTOM)

        self.status_var = tk.StringVar()
        self.status_var.set("状态栏")
        self.status_bar = ttk.Label(self.status_labelframe, textvariable=self.status_var)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.sub_status_var = tk.StringVar()
        self.sub_status_var.set("子状态栏")
        self.sub_status_bar = ttk.Label(self.status_labelframe, textvariable=self.sub_status_var)
        self.sub_status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def start_task(self):
        kill_process()

    def get_data(self):
        try:
            port = self.debug_port_entry.get()
            timeout = int(self.timeout_entry.get())
            response = requests.get(f"http://localhost:{port}/json", timeout=timeout)
            response.raise_for_status()
            self.tabs = response.json()
            self.master.after(0, self.refresh_data)
        except Exception as e:
            # 可以考虑记录日志或弹出提示框告知用户具体错误
            self.status_var.set("获取数据失败")

    def refresh_data(self):
        data = self.tabs
        self.data_viewer_tree.delete(*self.data_viewer_tree.get_children())
        count = 0
        for item in data:
            if item["type"] == "page" and item["url"].startswith("http"):
                count += 1
                title = item.get("title", "无标题")
                url = item.get("url", "")
                website = item.get("url", "").split("/")[2]
                self.data_viewer_tree.insert("",
                 "end", values=(title, url, website),
                 tags=(
                     "oddrow" if len(
                         self.data_viewer_tree.get_children()) % 2 == 0 else "evenrow"
                 ))
        self.status_var.set(f"找到{count}个链接")
        self.refresh_data_btn.config(state="normal")

    def get_html_thread(self, event=None):
        if not self.data_viewer_tree.selection():
            self.warning("请先选择一个链接")
            return
        self.get_html_btn.config(state="disabled")
        self.status_var.set("正在获取HTML")
        threading.Thread(target=self.get_html, daemon=True).start()

    def refresh_data_thread(self):
        self.status_var.set("正在刷新数据")
        self.refresh_data_btn.config(state="disabled")
        threading.Thread(target=self.get_data, daemon=True).start()

    def get_html(self):
        """
        获取HTML并解析
        """
        try:
            index = self.data_viewer_tree.selection()[0]
            item = self.data_viewer_tree.item(index, "values")
            url = item[1]

            exists: dict = next((t for t in self.tabs if t["url"] == url), None)
            if not exists:
                self.master.after(0, lambda: self.warning("找不到该链接"))
                return
            item = self.Manager.parser(url)
            if item:
                index = item["index"]
                parser = item["object"][0]
                shower = item["object"][1]
                shower.set_callback(self.callback)
                self.notebook.select(index)
            self.status_var.set(f"正在获取HTML")
            self.sub_status_var.set(f"正在获取{url}")
            timeout = int(self.timeout_entry.get() if self.timeout_entry.get().isdigit() else 10)
            ws = websocket.create_connection(
                exists["webSocketDebuggerUrl"],
                timeout=timeout,
                enable_multithread=True)
            try:
                command = {
                    "id": 1,
                    "method": "Runtime.evaluate",
                    "params": {
                        "expression": "document.documentElement.outerHTML",
                        "returnByValue": True
                    }
                }
                ws.send(json.dumps(command))
                response = json.loads(ws.recv())
                if "result" in response and "result" in response["result"]:
                    html = response["result"]["result"]["value"]

                    # 处理HTML，防止标签堆叠
                    soup = BeautifulSoup(html, "html.parser")
                    html = soup.prettify()
                    # 保存HTML, 方便调试
                    with open("debug.html", "w", encoding="utf-8") as f: f.write(html)
                    if not item:
                        self.master.after(0, lambda: self.warning("没有可用的插件"))
                        return
                    # 开始解析
                    self.parsing.clear()  # 禁止解析
                    self.status_var.set(f"正在解析")
                    self.sub_status_var.set(f"解析{url}")

                    executor = futures.ThreadPoolExecutor(max_workers=1)
                    future = executor.submit(parser.parse, html)
                    def finish_parse(future):
                        self.parsing.set()  # 允许解析
                        self.status_var.set(f"解析完成")
                        self.sub_status_var.set(f"解析{url}完成")
                    future.add_done_callback(finish_parse)

                else :
                    self.master.after(0, lambda: self.warning("获取HTML失败"))
            except Exception as e:
                self.master.after(0, lambda: self.warning("获取HTML失败"))
                print(f"获取HTML失败: {e}", sys.exc_info())
            finally:
                ws.close()
        except Exception as e:
            self.master.after(0, lambda: self.warning("获取HTML失败"))
            print(f"获取HTML失败: {e}", traceback.format_exc(), sys.exc_info())
        finally:
            self.get_html_btn.config(state="normal")








    def warning(self, message):
        self.status_var.set(message)
        self.get_html_btn.config(state="normal")

    def callback(self, data: dict):
        """
        主程序调用的回调函数
        """
        self.DataBase.insert_data(table_name=data["TableName"], data=data)
        self.show_status(f"已插入{data['title']}")


    def create_right_part(self):
        """
        创建主窗口右侧部分的界面
        """
        self.right_frame = tk.LabelFrame(self.master, text="插件")
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(self.right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)


        for module in self.Manager.get_modules():
            self.notebook.add(self.create_plugin_page(module), text=module[:-10])
            table_name = self.Manager.plugins[module][0].TableName
            self.DataBase.create_table(table_name, self.Manager.plugins[module][0].TableColumns)

    def create_plugin_page(self, module):
        """
        创建单个插件页面
        """
        page = ttk.LabelFrame(self.notebook)
        log_info(f"创建{module}插件页面，组件: {page}")
        page.pack(fill=tk.BOTH, expand=True)
        self.Manager.init_plugins(module, page)
        return page

    def go_to_page(self, page_name = "", page_index = 0):
        """
        跳转到指定页面
        """
        if page_name:
            for i in range(self.notebook.index("end")):
                if self.notebook.tab(i, "text") == page_name:
                    self.notebook.select(i)
                    break
        else:
            self.notebook.select(page_index)

    def show_status(self, message):
        """
        显示状态栏消息
        """
        self.status_bar.config(text=message)
    def show_sub_status(self, message):
        """
        显示子状态栏消息
        """
        self.sub_status_bar.config(text=message)

def main():
    root = tk.Tk()
    app = AppGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()








