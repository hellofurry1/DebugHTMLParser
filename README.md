# README

## 文件树

``` properties
.
├── README.md
├── requirements.txt
├── main.py
├── plugin_test.py
├── utils
│   ├── info.py
│   ├── SingletClass.py
│   └── taskkill.py
└── plugins
    ├── *HTMLParser.py
```

## 运行


1. 安装依赖

   ```
   pip install -r requirements.txt
   ```

2. 运行程序

   ```
   python main.py
   ```

## 插件开发

1. 编写插件

   参考 `plugins/*HTMLParser.py`

2. 可用方法

   参考 `plugin/Example.py`

3. 测试插件

   参考 `plugin_test.py`



