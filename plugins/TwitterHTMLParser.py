import os
import re
import shutil
import sys
import types
from datetime import datetime

import requests
import threading
from PIL import Image
from io import BytesIO
import hashlib
import imagehash
import tkinter as tk
from tkinter import ttk
from bs4 import BeautifulSoup

# 以下是 私有 文件
from main import db_obj, WorkDir
from utils.SingleClass import SingletonMeta

def twitter_exists(self, url: str):
    self.cursor.execute(f"""
        SELECT * FROM twitter WHERE img_url =?
""", (url,))
    return self.cursor.fetchone() is not None

db_obj.twitter_exists = types.MethodType(twitter_exists, db_obj)

shutil.rmtree(os.path.join(WorkDir, "twitter", ".new"), ignore_errors=True)
os.makedirs(os.path.join(WorkDir, "twitter"), exist_ok=True)
os.makedirs(os.path.join(WorkDir, "twitter", "fursuit"), exist_ok=True)

class Data:
    def __init__(self):
        self.url = ""
        self.img_url = ""
        self.time = ""
        self.author = ""
        self.pid = ""
        self.img_phash = ""
        self.img_hash = ""
        self.desc = ""
        self.tags = []

    def execute_image(self, save_type = "auto"):
        if DEBUG:print("url:", self.img_url)
        if not self.img_url:
            return
        ext = self.img_url.split(".")[-1]
        try:
            img_data = requests.get(self.img_url + ":orig").content
            img = Image.open(BytesIO(img_data))
            img_hash = hashlib.sha256(img_data).hexdigest()
            img_phash = imagehash.phash(img)
            self.img_hash = img_hash
            self.img_phash = str(img_phash)
            path = f"{WorkDir}/twitter/images/{self.author}/{img_hash}.{ext}"
            if save_type == "fursuit":
                path = f"{WorkDir}/twitter/fursuit/{self.author}/{self.img_hash}.jpg"
            os.makedirs(os.path.dirname(path), exist_ok=True)
            img.save(path)
            new_path = f"{WorkDir}/twitter/.new/{img_hash}.{ext}"
            os.makedirs(os.path.dirname(new_path), exist_ok=True)
            img.save(new_path)
        except Exception as e:
            print(e)

    def insert_type(self):
        return {
            "url": self.url,
            "img_url": self.img_url,
            "time": self.time,
            "author": self.author,
            "pid": self.pid,
            "img_phash": self.img_phash,
            "img_hash": self.img_hash,
            "desc": self.desc,
            "tags": self.tags.__str__()
        }

class DataTree:
    class InnerData:
        def __init__(self, time="", content="", img_urls=[]):
            self.time = time
            self.content = content
            self.img_urls = img_urls
        def dict(self):
            return {
                "time": self.time,
                "content": self.content,
                "url_num": len(self.img_urls),
                "img_urls": self.img_urls
            }
    def __init__(self):
        self.author = ""
        self.pid = ""
        self.len = 0
        self.parts = []

    def add_part(self, data: InnerData):
        self.parts.append(data.dict())
        self.len += 1

    def dict(self):
        return {
            "author": self.author,
            "pid": self.pid,
            "len": self.len,
            "parts": self.parts
        }

class TwitterShower(metaclass=SingletonMeta):
    def __init__(self, labelframe):
        self.labelframe = labelframe
        self.void_tree = {
            "author": "",
            "pid": "",
            "len": 1,
            "parts": [
                {
                    "time": "",
                    "content": "",
                    "url_num": 0,
                    "img_urls": [],
                }
            ],
        }
        self.tree = self.void_tree
        self.result_frame = self.labelframe
        self.author_entry = None
        self.pid_entry = None
        self.notebook = None
        self.init_top_widgets()
        self.init_notebook()

    def init_top_widgets(self):
        top_frame = ttk.Frame(self.result_frame)
        top_frame.pack(fill="x")
        # 创建两个子框架，各占 50% 宽度
        author_frame = ttk.Frame(top_frame, width=200)
        author_frame.pack(side="left", fill="x")
        pid_frame = ttk.Frame(top_frame, width=200)
        pid_frame.pack(side="right", fill="x")
        self.author_entry = self.create_entry(author_frame, "author", self.tree['author'])
        self.pid_entry = self.create_entry(pid_frame, "pid", self.tree['pid'])

    def create_entry(self, parent, label_text, value):
        frame = ttk.Frame(parent)
        frame.pack(pady=5)
        ttk.Label(frame, text=label_text + ": ").pack(side="top")
        if label_text == "content" or label_text == "time":
            text_widget = tk.Text(frame, height=2 if label_text != "content" else 5, width=20)
            text_widget.insert(tk.END, value)
            text_widget.configure(state="disabled")
            text_widget.pack(side="top")
            return text_widget
        else:
            entry = ttk.Entry(frame, width=20)
            entry.insert(0, value)
            entry.configure(state="readonly")
            entry.pack(side="top")
            return entry

    def init_notebook(self):
        self.notebook = ttk.Notebook(self.result_frame)
        self.notebook.pack(fill="both", expand=True)
        self.page_frames: list[ttk.Frame] = []
        for i in range(self.tree['len']):
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=f"Page {i + 1}")
            self.page_frames.append(frame)
            self.init_page_widgets(frame, i)

    def get_save_type(self, event=None) -> str:
        save_type = self.choice_save_type.get()
        return save_type if not event else None


    def init_page_widgets(self, frame, index):
        left_frame = ttk.Frame(frame)
        left_frame.pack(side="left", fill="y")
        self.create_entry(left_frame, "time", self.tree['parts'][index]['time'])
        self.create_entry(left_frame, "content", self.tree['parts'][index]['content'])

        self.choice_save_type = tk.StringVar()
        self.choice_save_type_list = ["auto", "images", "fursuit"]
        self.choice_save_type_box = ttk.Combobox(left_frame, values=self.choice_save_type_list, textvariable=self.choice_save_type, state="readonly")
        self.choice_save_type_box.set("auto")
        self.choice_save_type_box.pack(side="bottom", fill="x")
        self.choice_save_type_box.bind("<<ComboboxSelected>>", self.get_save_type)


        right_frame = ttk.Frame(frame)
        right_frame.pack(side="right", fill="y")

        treeview = ttk.Treeview(
            right_frame,
            columns=("img_urls",),
            show="headings",
            selectmode="browse",
            height=5
        )
        treeview.heading("img_urls", text="图片链接", anchor="w")
        treeview.column("img_urls", minwidth=150, stretch=False)

        scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=treeview.yview)
        treeview.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        treeview.pack(side="left", fill="y")

        self.page_frames[index].treeview = treeview
        for img_url in self.tree['parts'][index]['img_urls']:
            treeview.insert("", "end", values=(img_url,))

    def update_interface(self, new_tree):
        self.tree = new_tree
        print("draw author")
        self.author_entry.configure(state="normal")
        self.author_entry.delete(0, tk.END)
        self.author_entry.insert(0, self.tree['author'])
        self.author_entry.configure(state="readonly")

        print("draw pid")
        self.pid_entry.configure(state="normal")
        self.pid_entry.delete(0, tk.END)
        self.pid_entry.insert(0, self.tree['pid'])
        self.pid_entry.configure(state="readonly")

        # 清空现有的页面
        print("draw notebook")
        for frame in self.page_frames:
            self.notebook.forget(self.notebook.index(frame))
        self.page_frames = []

        print("draw notebook pages")
        for i in range(self.tree['len']):
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=f"Page {i + 1}")
            self.page_frames.append(frame)
            self.init_page_widgets(frame, i)
        return
    def show_info(self, info_dict: dict):
        # info_dict : datatree
        self.update_interface(info_dict)


DEBUG = True

class TwitterHTMLParser:
    # 常量定义
    TableName = "twitter"
    TableColumns = [
        ("url", "TEXT"),
        ("img_url", "TEXT"),
        ("time", "TEXT"),
        ("author", "TEXT"),
        ("pid", "TEXT"),
        ("img_phash", "TEXT"),
        ("img_hash", "TEXT"),
        ("desc", "TEXT"),
        ("tags", "TEXT")
    ]
    SitePatterns = [
        re.compile(r"https://x\.com/(\w+)/status/(\d+)(/photo/(\d+))?")
    ]

    # 变量定义
    url_pattern = re.compile(r"https://x\.com/(\w+)/status/(\d+)(/photo/(\d+))?")
    url_format = "https://x.com/{author}/status/{pid}"
    img_url_format = "https://pbs.twimg.com/media/{hash_key}.{ext}"
    img_url_pattern = re.compile(r"https://pbs\.twimg\.com/media/(.*?)\?format=(.*?)&name=(.*?)$")
    time_pattern = re.compile(r"\d{1,2}:\d{2} (AM|PM) · \w{3} \d{1,2}, \d{4}")
    tag_href_pattern = re.compile(r".*hashtag_click.*")

    def __init__(self):
        self.shower: TwitterShower|None = None
        self.shower = TwitterShower.get_instance(TwitterShower)
        self.data = Data()
        self.datatree = DataTree()
        self.after_info = None
        self.parsing = threading.Event()
        self.parsing.set()
        self.img_urls = []
        self.inner_data: list[tuple[datetime, str, list[str]]] = []


    def parse_time(self, time_str: str):
        if re.match(self.time_pattern, time_str):
            return datetime.strptime(time_str, "%I:%M %p · %b %d, %Y")
        else:
            try:
                return datetime.fromisoformat(time_str)
            except ValueError as e:
                print(f"时间解析错误: {e}")
                return None
    def debug_(self, *args, **kwargs):
        print(*args, **kwargs) if DEBUG else None

    def parse(self, html: str):
        self.parsing.clear()
        soup = BeautifulSoup(html, "html.parser")
        self.debug_("parse html to soup")
        url = soup.find("meta", attrs={"property": "og:url"})
        if not url:
            url = soup.find("link", attrs={"rel": "canonical"})
            if not url:
                return
            url = url.get("href")
        else:
            url = url.get("content")
        self.debug_("get url :", url)
        self.data.author = self.url_pattern.match(url).group(1)
        self.data.pid = self.url_pattern.match(url).group(2)
        self.data.url = self.url_format.format(
            author=self.data.author,
            pid=self.data.pid
        )
        self.datatree.author = self.data.author
        self.datatree.pid = self.data.pid

        self.debug_("info :", self.data.author, self.data.pid, self.data.url)
        for span in soup.find_all("span"):
            if span.text.strip() == "Discover more":
                self.after_info = span.sourceline
                break
        self.debug_("after_info line :", self.after_info)
        time_block = soup.find("a", attrs={"href": f"/{self.data.author}/status/{self.data.pid}"})
        if time_block:
            self.data.time = self.parse_time(time_block.text.strip())
        else:
            for time in soup.find_all("time"):
                if self.time_pattern.match(time.text.strip()):
                    self.data.time = self.parse_time(time.text.strip())
                    break

        self.debug_("time :", self.data.time)
        self.debug_("parse article...", "len = ", len(soup.find_all("article")))
        for article in soup.find_all("article"):
            self._parse_article(article)

        self.debug_("parse complete.")
        # 结束解析
        self.execute()
        self.debug_("execute complete.")
        self.parsing.set()

    def execute(self):
        self.debug_("execute...")
        self.shower.update_interface(self.datatree.dict())
        self.debug_("update interface...")
        for img_url in self.img_urls:
            self.debug_("execute url:", img_url)
            if db_obj.twitter_exists(img_url):
                continue
            self.data.img_url = img_url

            self.data.execute_image(self.shower.get_save_type())
            print(self.data.insert_type())
            db_obj.insert_data("twitter", self.data.insert_type())





    def _parse_article(self, article):
        if article.get("tabindex", "") == "-1" and article.get("data-testid", "") == "tweet":
            self._parse_main(article)
        else:
            if self.after_info is not None and article.sourceline > self.after_info:
                return
            else:
                self._parse_comment(article)

    def _parse_main(self, soup):
        def debug_(*args, **kwargs):
            print(*args, **kwargs) if DEBUG else None
        # soup.name == "article"
        inner_data = DataTree.InnerData()
        inner_data.time = self.data.time
        main_div_block = soup.find("div")
        debug_("main.div")
        main_div_block = main_div_block.find("div")
        debug_("main.div.div")
        tweet_block: BeautifulSoup = main_div_block.find_all("div", recursive=False)[2] if len(
            main_div_block.find_all("div", recursive=False)) > 2 else None
        debug_("main.div.div.div(3) or None", tweet_block is None)
        tweet_block = tweet_block.find("div")
        try:
            desc_block = tweet_block.find("div").find("div")
        except AttributeError:
            desc_block = None

        desc = ""
        if not desc_block:
            self.data.desc = ""
            self.data.tags = []
        else:
            for item in desc_block.find_all(recursive=False):
                a_s = item.find_all("a", attrs={"href": self.tag_href_pattern})
                if a_s:
                    self.data.tags.append(item.text.strip()[1:])
                else:
                    if item.name == "img":
                        desc += item.get("alt") if item.get("alt") != "Image" else ""
                    else:
                        desc += item.text.strip()
            self.data.desc = desc.strip()
        inner_data.content = self.data.desc
        img_block = tweet_block.find_next_sibling("div")
        if not img_block:
            return 5
        img_urls = img_block.find_all("img", {"src": self.img_url_pattern})
        self.img_urls = [self.parse_img_url(img_url.get("src")) for img_url in img_urls]
        inner_data.img_urls = self.img_urls
        self.datatree.add_part(inner_data)

    def parse_img_url(self, img_url: str):
        """
        解析图片链接
        """
        match = self.img_url_pattern.match(img_url)
        if match:
            return self.img_url_format.format(hash_key=match.group(1), ext=match.group(2))
        return img_url

    def _parse_comment(self, soup):
        print("_parse_comment")
        try:
            body = soup.find("div").find("div").find_all("div", recursive=False)[1]
            body = body.find_all(recursive=False)[1]
            info = body.find("div").find("div").find("div").find_all("div")[1].find_all("div", recursive=False)[1]
            author = info.find_all("a")[0].find("div").find("span").text.strip().strip("@")
            time_str = info.find_all("time")[0].get("datetime")
            content = body.find_all("div", recursive=False)[1].find("span").text.strip()
            img_urls = [img for img in body.find_all("img") if
                        self.img_url_pattern and self.img_url_pattern.match(img.get("src"))]
            if not img_urls:
                return
            if self.data.author == author:
                self.inner_data.append((self.parse_time(time_str), content,
                    [self.parse_img_url(img_url.get("src")) for img_url in img_urls]))
                self.datatree.add_part(DataTree.InnerData(time=self.parse_time(time_str).__str__(), content=content, img_urls=[self.parse_img_url(img_url.get("src")) for img_url in img_urls]))
        except (AttributeError, IndexError) as e:
            print(f"解析评论块时出错: {e}", f"line: {sys.exc_info()[-1].tb_lineno}",
                  "\n这一般是由于HTML结构不完整导致的，可以忽略。")

if __name__ == '__main__':
    parser = TwitterHTMLParser()
    with open("../debug.html", "r", encoding="utf-8") as f:
        html = f.read()
    parser.parse(html)














