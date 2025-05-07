import os
import re
import json
import types

import requests
import threading
import tkinter as tk
from tkinter import ttk
from bs4 import BeautifulSoup
from dateutil.parser import parse

# 以下是 私有 文件
from utils.SingleClass import SingletonMeta
from main import WorkDir, db_obj

class Data:
    def __init__(self):
        self.view_key = ""
        self.title = ""
        self.tags = []
        self.author = ""
        self.view_count = 0
        self.rating = 0.0
        self.video_length = 0
        self.upload_time = ""
        self.up_count = 0
        self.down_count = 0
        self.fav_count = 0
        self.quality = ""

    def insert_type(self):
        return {
            "view_key": self.view_key,  # True
            "title": self.title,  # True
            "tags": ",".join(self.tags),  # True
            "author": self.author,  # True
            "view_count": self.view_count,  # True
            "rating": self.rating,  # True
            "video_length": self.video_length,  # True
            "upload_date": self.upload_time,  # True
            "up_count": self.up_count,  # True
            "down_count": self.down_count,  # True
            "fav_count": self.fav_count,  # True
            "quality": self.quality,  # True
        }


def pornhub_exists(self, view_key: str) -> bool:
    self.cursor.execute(f"""
SELECT * FROM {PornhubHTMLParser.TableName} WHERE view_key=?
""", (view_key,))
    return self.cursor.fetchone() is not None

db_obj.pornhub_exists = types.MethodType(pornhub_exists, db_obj)



class PornhubShower(metaclass=SingletonMeta):
    def __init__(self, labelframe):
        self.labelframe = labelframe
        self.ui()

    def ui(self):
        self.text_labels = {}
        self.info_frame = self.labelframe
        self.info_frame.pack(fill="both", expand=True, padx=5, pady=5)
        ttk.Label(self.info_frame, text="标题").grid(row=0, column=0, padx=5, pady=5)
        self.title_text_label = tk.Text(self.info_frame, width=20, height=1)
        self.title_text_label.grid(row=0, column=1, padx=5, pady=5, columnspan=2, sticky="w")
        self.title_text_label.config(state="disabled")
        self.text_labels["title"] = self.title_text_label

        ttk.Label(self.info_frame, text="标签").grid(row=1, column=0, padx=5, pady=5)
        self.tags_text_label = tk.Text(self.info_frame, width=50, height=1)
        self.tags_text_label.grid(row=1, column=1, padx=5, pady=5, columnspan=6)
        self.tags_text_label.config(state="disabled")
        self.text_labels["tags"] = self.tags_text_label

        ttk.Label(self.info_frame, text="作者").grid(row=0, column=3, padx=5, pady=5)
        self.author_text_label = tk.Text(self.info_frame, width=20, height=1)
        self.author_text_label.grid(row=0, column=4, padx=5, pady=5, columnspan=2)
        self.author_text_label.config(state="disabled")
        self.text_labels["author"] = self.author_text_label

        ttk.Label(self.info_frame, text="观看量").grid(row=2, column=0, padx=5, pady=5)
        self.video_url_text_label = tk.Text(self.info_frame, width=6, height=1)
        self.video_url_text_label.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        self.video_url_text_label.config(state="disabled")
        self.text_labels["view_count"] = self.video_url_text_label

        ttk.Label(self.info_frame, text="评分").grid(row=2, column=2, padx=5, pady=5)
        self.rating_text_label = tk.Text(self.info_frame, width=6, height=1)
        self.rating_text_label.grid(row=2, column=3, padx=5, pady=5, sticky="w")
        self.rating_text_label.config(state="disabled")
        self.text_labels["rating"] = self.rating_text_label

        ttk.Label(self.info_frame, text="时长").grid(row=2, column=4, padx=5, pady=5)
        self.video_length_text_label = tk.Text(self.info_frame, width=6, height=1)
        self.video_length_text_label.grid(row=2, column=5, padx=5, pady=5, sticky="w")
        self.video_length_text_label.config(state="disabled")
        self.text_labels["video_length"] = self.video_length_text_label

        ttk.Label(self.info_frame, text="上传日期").grid(row=3, column=0, padx=5, pady=5)
        self.upload_date_text_label = tk.Text(self.info_frame, width=30, height=1)
        self.upload_date_text_label.grid(row=3, column=1, padx=5, pady=5, columnspan=4, sticky="w")
        self.upload_date_text_label.config(state="disabled")
        self.text_labels["upload_date"] = self.upload_date_text_label

        ttk.Label(self.info_frame, text="点赞").grid(row=4, column=0, padx=5, pady=5)
        self.up_count_text_label = tk.Text(self.info_frame, width=6, height=1)
        self.up_count_text_label.grid(row=4, column=1, padx=5, pady=5, sticky="w")
        self.up_count_text_label.config(state="disabled")
        self.text_labels["up_count"] = self.up_count_text_label

        ttk.Label(self.info_frame, text="点踩").grid(row=4, column=2, padx=5, pady=5)
        self.down_count_text_label = tk.Text(self.info_frame, width=6, height=1)
        self.down_count_text_label.grid(row=4, column=3, padx=5, pady=5, sticky="w")
        self.down_count_text_label.config(state="disabled")
        self.text_labels["down_count"] = self.down_count_text_label

        ttk.Label(self.info_frame, text="收藏").grid(row=4, column=4, padx=5, pady=5)
        self.fav_count_text_label = tk.Text(self.info_frame, width=6, height=1)
        self.fav_count_text_label.grid(row=4, column=5, padx=5, pady=5, sticky="w")
        self.fav_count_text_label.config(state="disabled")
        self.text_labels["fav_count"] = self.fav_count_text_label

        ttk.Label(self.info_frame, text="清晰度").grid(row=3, column=4, padx=5, pady=5)
        self.quality_text_label = tk.Text(self.info_frame, width=10, height=1)
        self.quality_text_label.grid(row=3, column=5, padx=5, pady=5, sticky="w")
        self.quality_text_label.config(state="disabled")
        self.text_labels["quality"] = self.quality_text_label

        ttk.Label(self.info_frame, text="报错").grid(row=5, column=0, padx=5, pady=5)
        self.error_text_label = tk.Text(self.info_frame, width=50, height=5)
        self.error_text_label.grid(row=5, column=1, padx=5, pady=5, columnspan=6, rowspan=3)
        self.error_text_label.config(state="disabled")
        self.text_labels["error"] = self.error_text_label

        ttk.Label(self.info_frame, text="进度条").grid(row=8, column=0, padx=5, pady=5)
        self.progress_bar = ttk.Progressbar(self.info_frame, orient="horizontal", length=200, mode="determinate")
        self.progress_bar.grid(row=8, column=1, padx=5, pady=5, columnspan=4, sticky="w")
        self.progress_bar.config(value=0, maximum=100)

        ttk.Label(self.info_frame, text="数字进度").grid(row=8, column=4, padx=5, pady=5)
        self.progress_var = tk.StringVar()
        self.progress_var.set("0%")
        self.progress_label = ttk.Label(self.info_frame, textvariable=self.progress_var)
        self.progress_label.grid(row=8, column=5, padx=5, pady=5, sticky="w")
        self.progress_label.config(state="disabled")


    def show_info(self, info: dict):
        for key, value in info.items():
            if key in self.text_labels:
                self.text_labels[key].config(state="normal")
                self.text_labels[key].delete("1.0", "end")
                self.text_labels[key].insert("1.0", value)
                self.text_labels[key].config(state="disabled")
        if info.get("set_progress", 0) != 0:
            self.progress_bar.config(value=info["set_progress"])
            self.progress_var.set(f"0%")
        if info.get("update_progress", 0) != 0:
            self.progress_bar.update()
            self.progress_var.set(f"{(self.progress_bar['value'] / self.progress_bar['maximum'] * 100):.1f}%")
        if "release_parse" in info:
            pass
        if "rollback" in info:
            db_obj.rollback_new_data(PornhubHTMLParser.TableName)



class PornhubHTMLParser:
    TableName = "pornhub"
    TableColumns = [
        ("view_key", "TEXT PRIMARY KEY"),
        ("title", "TEXT"),
        ("tags", "TEXT"),
        ("author", "TEXT"),
        ("view_count", "INTEGER"),
        ("rating", "REAL"),
        ("video_length", "INTEGER"),
        ("upload_date", "TEXT"),
        ("up_count", "INTEGER"),
        ("down_count", "INTEGER"),
        ("fav_count", "INTEGER"),
        ("quality", "TEXT")
    ]
    SitePatterns = [
        re.compile(r"https?://\w{2,3}\.pornhub\.com/view_video\.php\?viewkey=(\w+)")
    ]
    media_info_p = re.compile(r'"mediaDefinitions":(\[.*?]),"is')
    unavailable_chars = r"""!"#$%&'()*+,/:;<=>?@[\]^`{|}~ """
    translation_table = str.maketrans(unavailable_chars, "_" * len(unavailable_chars))

    def __init__(self):
        self.shower : PornhubShower|None = None
        self.shower = PornhubShower.get_instance(PornhubShower)

        self.db_obj = db_obj
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
        }
        self.data = Data()

    @staticmethod
    def parse_iso8601_duration(duration_str) -> int:
        parts = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration_str)
        hours = int(parts.group(1)) if parts.group(1) else 0
        minutes = int(parts.group(2)) if parts.group(2) else 0
        seconds = int(parts.group(3)) if parts.group(3) else 0
        total_seconds = hours * 3600 + minutes * 60 + seconds
        return total_seconds

    def parse(self, html: str):
        soup = BeautifulSoup(html, "html.parser")
        orig_url = soup.find("meta", attrs={"property": "og:url"})["content"]
        self.data.view_key = self.SitePatterns[0].search(orig_url).group(1)
        # 标题
        self.data.title = soup.find("meta", attrs={"property": "og:title"})["content"]
        self.directory = self.data.title.translate(self.translation_table)
        # 标签
        self.data.tags = soup.find("meta", {"data-context-tag": re.compile(r".*")})["data-context-tag"].split(",")
        self.data.tags = list(set([tag.strip() for tag in self.data.tags]))
        # 作者
        json_data = json.loads(soup.find("script", {"type": "application/ld+json"}).string.strip())
        self.data.author = json_data["author"]
        # 观看量
        info: list[dict] = json_data["interactionStatistic"]
        self.data.view_count = int(info[0]["userInteractionCount"].replace(",", ""))
        # 评分
        self.data.rating = float(soup.find("span", class_="percent").text.strip().strip("%"))
        # 时长
        self.data.video_length = self.parse_iso8601_duration(json_data["duration"])
        # 上传日期
        upload_time = parse(json_data["uploadDate"])
        self.data.upload_time = upload_time.strftime("%Y-%m-%d %H:%M:%S")
        # 点赞
        self.data.up_count = int(info[1]["userInteractionCount"].replace(",", ""))
        # 点踩
        self.data.down_count = soup.find("span", class_="votesDown").text.strip()
        # 收藏
        self.data.fav_count = soup.find("span", class_="favoritesCounter").text.strip()
        # 清晰度
        js_div = soup.find("div", {"id": "player"})
        js_program = js_div.find("script", {"type": "text/javascript"})
        js_code = js_program.string.strip()
        match = self.media_info_p.search(js_code)
        if match:
            media_info = json.loads(match.group(1))
            quality = 0
            for index, item in enumerate(media_info):
                inner_quality = int(item.get("quality", 0) if isinstance(item.get("quality", 0), (str, int)) else 0)
                if inner_quality > quality:
                    quality = inner_quality
            self.data.quality = quality
        else:
            self.data.quality = "未知"
            self.shower.show_info({"error": "清晰度获取失败"})
        self.video_url = orig_url
        if self.db_obj.exists(self.TableName, self.data.view_key):
            return
        self.db_obj.insert_data(self.TableName, self.data.insert_type())
        if self.shower:
            self.shower.show_info(self.data.insert_type())

        threading.Thread(target=self.download)

    def download(self):
        if not self.video_url:
            return

        u = requests.get(self.video_url).text.split(
            '"format":"hls","videoUrl":"')[1].split('"')[0].replace("\\", "")
        videos = [i for i in requests.get(
            u.split("master")[0] + [i for i in requests.get(u).text.splitlines() if "?" in i][0]).text.splitlines()
                  if
                  "?" in i]
        self.shower.show_info({"set_progress_len": len(videos)})
        f = open(os.path.join(WorkDir, "pornhub", "videos", self.directory, "video.mp4"), "wb")
        index = 0
        for retry in range(len(videos) // 2):
            try:
                while index < len(videos):
                    video = videos[index]
                    index += 1
                    acc_url = u.split("master")[0] + video
                    video_data = requests.get(acc_url, headers=self.headers).content
                    f.write(video_data)
                    self.shower.show_info({"update_progress": 1})
            except requests.exceptions.RequestException:
                self.shower.show_info({"error": "下载失败, 重试{}次".format(retry + 1)})
            except OSError:
                self.shower.show_info({"error": "下载失败, 重试{}次".format(retry + 1)})
            except:
                self.shower.show_info({"error": "下载失败, 重试{}次".format(retry + 1)})
            break
        f.close()
        self.shower.show_info({"error": ""})
        if index != len(videos):
            self.shower.show_info({"error": "下载失败"})
        else:
            self.db_obj.insert_data(self.TableName, self.data.insert_type())










