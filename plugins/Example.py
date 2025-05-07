def doc(obj, doc_str):
    """
    用于文档说明，不影响代码运行。
    """
    try:
        obj.__doc__ = doc_str
    except:
        pass

from main import db_obj

doc(db_obj,
    """
    该对象为数据存储对象，用于存储插件运行时产生的数据。
    该对象提供了以下方法：
    - `create_table(table_name: str, columns: list[tuple]) -> None`: 创建数据表。
    - `insert_data(table_name: str, data: list | tuple | dict) -> None`: 插入数据。
    - `rollback_new_data(table_name: str) -> None`: 回滚最新插入的数据。
    - `rollback_with_condition(table_name: str, condition: str) -> None`: 回滚指定条件的数据。
    - `__del__(self) -> None`: 析构函数，用于关闭数据库连接。
    """
    )

from utils.info import log_info

doc(log_info,
    """
    该函数用于输出日志信息。
    该函数提供了以下参数：
    - `message`: 日志信息。
    - `level`: 日志级别，可选值为 `info`、`warning`、`error`。
    """
    )

from utils.taskkill import kill_process
doc(kill_process,
    """
    该函数用于杀死 Edge 进程, 并以调试模式启动 Edge。
    """
    )

from utils.SingleClass import SingletonMeta, unavailable_chars, translation_table

doc(SingletonMeta,
    """
    该类用于实现单例模式。
    使用该类作为元类，可以使得类的实例成为单例。
    该类提供了以下方法：
    - `__call__(cls, *args, **kwargs) -> object`: 用于创建类的实例。
    - `get_instance(target_cls) -> object`: 用于获取指定类的单例实例。
        如果该类尚未创建过实例，则返回 `None`。
    """
    )
doc(unavailable_chars,
    """
    该字符串包含了不可用字符。
    """
    )
doc(translation_table,
    """
    该字典用于将不可用字符转换为下划线。
    """
    )



