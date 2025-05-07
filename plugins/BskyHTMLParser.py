import re
import PIL
import types
import shutil
import hashlib
import os.path
import requests
import threading
import traceback
import imagehash
import tkinter as tk
from PIL import Image
from io import BytesIO
from tkinter import ttk
from datetime import datetime
from bs4 import BeautifulSoup
from main import db_obj, WorkDir
from utils.SingleClass import SingletonMeta, translation_table

def bsky_exists(self, url: str):
    self.cursor.execute(f"""
SELECT * FROM {self.TableName} WHERE url = ?
""", (url,))
    return self.cursor.fetchone() is not None

shutil.rmtree(os.path.join(WorkDir, "bsky", "new"), ignore_errors=True)

db_obj.bsky_exists = types.MethodType(bsky_exists, db_obj)

class DataTree:
    class InnerData:
        def __init__(self):
            self.time = ""
            self.content = ""
            self.img_urls = []

        def dict(self):
            return {
                "time": self.time,
                "content": self.content,
                "url_num": len(self.img_urls),
                "img_urls": self.img_urls
            }

        def __str__(self):
            string = [f"{k}: {str(v)}" for k, v in self.dict().items()]
            return "\n".join(string)

    def __init__(self):
        self.author = ""
        self.pid = ""
        self.inner_data = []

    def add_data(self, data: InnerData):
        self.inner_data.append(data.dict())

    def dict(self):
        return {
            "author": self.author,
            "pid": self.pid,
            "len": len(self.inner_data),
            "inner_data": self.inner_data
        }

    def __str__(self):
        string = ""
        string += f"author: {self.author}\n"
        string += f"pid: {self.pid}\n"
        string += f"len: {len(self.inner_data)}\n"
        string += f"inner_data:\n"
        for data in self.inner_data:
            inner_str = [f"\t{k}: {v}" for k, v in data.items()]
            string += "\n".join(inner_str)
            string += "\n"
        return string[:-1]



class Data:
    def __init__(self):
        self.author = ""
        self.desc = ""
        self.tags = []
        self.upload_time = ""
        self.url = ""
        self.img_url = ""
        self.img_hash = ""
        self.img_phash = ""
        self.save_path = os.path.join(WorkDir, "bsky")
        os.makedirs(self.save_path, exist_ok=True)

    def save_type(self) -> dict:
        return {
            "author": self.author,
            "desc": self.desc,
            "tags": ",".join(self.tags),
            "upload_time": self.upload_time,
            "url": self.url,
            "img_url": self.img_url,
            "img_hash": self.img_hash,
            "img_phash": self.img_phash
        }

    def fetch_image(self, img_url: str):
        try:
            response = requests.get(img_url)
            response.raise_for_status()  # 检查请求是否成功，失败则抛出异常
            return response.content
        except requests.RequestException as e:
            print(f"Error fetching image: {e}")
            traceback.print_exc()
            return None

    def process_image(self, img_data):
        try:
            img = Image.open(BytesIO(img_data))
            img_hash = hashlib.sha256(img_data).hexdigest()
            img_phash = str(imagehash.phash(img))
            return img, img_hash, img_phash
        except (PIL.UnidentifiedImageError, Exception) as e:
            print(f"Error processing image: {e}")
            traceback.print_exc()
            return None, None, None

    def save_image(self, img, save_path):
        try:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            img.save(save_path)
            return True
        except Exception as e:
            print(f"Error saving image: {e}")
            traceback.print_exc()
            return False

    def execute(self, img_url: str):
        img_data = self.fetch_image(img_url)
        if img_data:
            img, img_hash, img_phash = self.process_image(img_data)
            if img and img_hash and img_phash:
                save_path = os.path.join(self.save_path, self.author, img_hash + ".jpg")
                if self.save_image(img, save_path):
                    new_save_path = os.path.join(WorkDir, "bsky", "new", img_hash + ".jpg")
                    self.save_image(img, new_save_path)
                    self.img_url = img_url
                    self.img_hash = img_hash
                    self.img_phash = img_phash

class BskyShower(metaclass=SingletonMeta):
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

    def init_page_widgets(self, frame, index):
        left_frame = ttk.Frame(frame)
        left_frame.pack(side="left", fill="y")
        self.create_entry(left_frame, "time", self.tree['parts'][index]['time'])
        self.create_entry(left_frame, "content", self.tree['parts'][index]['content'])

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
        self.author_entry.delete(0, tk.END)
        self.author_entry.insert(0, self.tree['author'])
        self.pid_entry.delete(0, tk.END)
        self.pid_entry.insert(0, self.tree['pid'])

        # 清空现有的页面
        for frame in self.page_frames:
            self.notebook.forget(self.notebook.index(frame))
        self.page_frames = []

        for i in range(self.tree['len']):
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=f"Page {i + 1}")
            self.page_frames.append(frame)
            self.init_page_widgets(frame, i)

    def show_info(self, info_dict: dict):
        # info_dict : datatree
        self.update_interface(info_dict)





class BskyHTMLParser:
    # https://bsky.app/profile/leeeee.bsky.social/post/3loe2duqsos2z
    SitePatterns = [
        re.compile(r"^https?://bsky\.app/profile/(.*?)/post/(.*)$"),
    ]
    TableName = "bsky"
    TableColumns = [
        ("author", "TEXT"),
        ("desc", "TEXT"),
        ("tags", "TEXT"),
        ("upload_time", "TEXT"),
        ("url", "TEXT"),
        ("img_url", "TEXT"),
        ("img_hash", "TEXT"),
        ("img_phash", "TEXT")
    ]

    # 1 : orig, 2: got from html
    # https://cdn.bsky.app/img/feed_fullsize/plain/did:plc:s7zbntk5emwy67ebrvj7j262/bafkreidfkmtpaf3hpvenogifoheoc5liwkpsy3swjp6375pqsbkpmlx7xm@jpeg
    # https://cdn.bsky.app/img/feed_thumbnail/plain/did:plc:s7zbntk5emwy67ebrvj7j262/bafkreidfkmtpaf3hpvenogifoheoc5liwkpsy3swjp6375pqsbkpmlx7xm@jpeg

    full_size_format = "https://cdn.bsky.app/img/feed_fullsize/plain/{}"
    thumbnail_pattern = re.compile(
        r"https://cdn.bsky.app/img/feed_thumbnail/plain/(.*)$"
    )
    tag_pattern = re.compile(r"/hashtag/(.*?)$")

    def __init__(self):
        self.shower = None
        self.shower = BskyShower.get_instance(BskyShower)
        self.data = Data()
        self.data_tree = DataTree()

    def debug_output(self, *args, **kwargs):
        print("=" * 20, "BskyHTMLParser", "=" * 20)
        string = [f"{k}: {v}" for k, v in self.data.save_type().items()]
        print("\n".join(string))

    def parse(self, html: str):
        soup = BeautifulSoup(html, "html.parser")

        blocks = soup.find_all("div", {"data-testid": re.compile(r".*postThreadItem.*")})
        main_block = blocks[0]
        comments_block = blocks[1:]
        sub_blocks = main_block.find_all(recursive=False) # 2
        author_block = sub_blocks[0]
        tweet_block = sub_blocks[1]
        author = author_block.find_all('div', {"dir": "auto"})[1].text.strip()[2:-1]
        self.data.author = author
        self.data_tree.author = author

        autos = tweet_block.find_all('div', {"dir": "auto"})

        links = autos[0].find_all('a')
        tags_blocks = [link for link in links if link.get('href') and self.tag_pattern.search(link.get('href'))]

        for tag in tags_blocks:
            tag_name = self.tag_pattern.search(tag.get('href')).group(1)
            self.data.tags.append(tag_name)


        desc = "\n".join([part.strip() for part in autos[0].text.strip().split("\n") if part.strip()])
        self.data.desc = desc

        # time
        time_str = autos[1].text.strip()
        # time_str = '2025年5月4日 22:19'
        time_obj = datetime.strptime(time_str, '%Y年%m月%d日 %H:%M')
        self.data.upload_time = time_obj.strftime('%Y-%m-%d %H:%M:%S')

        # url
        url = soup.find('a', {"aria-label": time_str}).get('href')
        url = "https://bsky.app" + url
        self.data.url = url
        self.data_tree.pid = url.split("/")[-1]
        # images
        img_urls = []
        images = tweet_block.find_all('img')
        for img in images:
            img_url = self.full_size_format.format(
                self.thumbnail_pattern.search(img.get('src')).group(1)
            )
            img_urls.append(img_url)
        inner_data = DataTree.InnerData()
        inner_data.time = self.data.upload_time
        inner_data.content = desc
        inner_data.img_urls = img_urls
        self.data_tree.add_data(inner_data)
        self.parse_comments(comments_block)

        threading.Thread(target=self.download)

    def download(self):
        for item in self.data_tree.inner_data:
            for img_url in item["img_urls"]:
                try:
                    self.data.execute(img_url)
                    db_obj.insert_data(self.TableName, self.data.save_type())
                except Exception as e:
                    print(f"下载图片出错: {e}")


    def parse_comments(self, comments_block):
        for block in comments_block:
            try:
                self.parse_comment(block)
            except Exception as e:
                print(f"解析评论出错: {e}，通常是HTML未完全加载完成，可以忽略.")

    def parse_comment(self, block: BeautifulSoup):
        comment_block = block.find_all("div", recursive=False)[1]
        comment_block = comment_block.find_all("div", recursive=False)[1]
        author = comment_block.find_all('a')[1].text.strip()[2:-1]
        if self.data.author != author:
            return

        #  time: 2025年5月4日 22:19
        time_block: BeautifulSoup = comment_block.find("span").parent
        time_str = time_block.get("aria-label")
        if not time_str:
            time_str = time_block.get("data-tooltip")
        time_obj = datetime.strptime(time_str, '%Y年%m月%d日 %H:%M')
        self.data.upload_time = time_obj.strftime('%Y-%m-%d %H:%M:%S')

        # content
        content_block: BeautifulSoup = comment_block.find_all("div", recursive=False)[1]
        content = content_block.find("div").text.strip()

        img_block = comment_block.find_all("div", recursive=False)[2]
        # images
        img_urls = []
        images = img_block.find_all('img')
        for img in images:
            img_url = self.full_size_format.format(
                self.thumbnail_pattern.search(img.get('src')).group(1)
            )
            img_urls.append(img_url)
        inner_data = DataTree.InnerData()
        inner_data.time = self.data.upload_time
        inner_data.content = content
        inner_data.img_urls = img_urls
        self.data_tree.add_data(inner_data)

    def show_info(self):
        self.shower.show_info(self.data_tree.dict())























class TestGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry("400x300")
        self.root.title("BskyShower")
        self.labelframe = ttk.LabelFrame(self.root, text="BskyShower")
        self.labelframe.pack(fill="both")
        self.bsky_shower = BskyShower(self.labelframe)
        self.root.mainloop()

if __name__ == '__main__':
    # test_gui = TestGUI()
    obj = BskyHTMLParser()
    with open("debug.html", "r", encoding="utf-8") as f:
        html = f.read()
    obj.parse(html)
    print(obj.data_tree)
