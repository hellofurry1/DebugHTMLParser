import threading


class SingletonMeta(type):
    _instances = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                cls._instances[cls] = super().__call__(*args, **kwargs)
            return cls._instances[cls]

    @classmethod
    def get_instance(cls, target_cls):
        if isinstance(target_cls, type) and target_cls.__class__ == SingletonMeta:
            return cls._instances.get(target_cls, None)
        return None

unavailable_chars = r"""!"#$%&'()*+,/:;<=>?@[\]^`{|}~ """
translation_table = str.maketrans(unavailable_chars, "_" * len(unavailable_chars))

class Example(metaclass=SingletonMeta):
    def __init__(self, name):
        self.name = name
__all__ = ['SingletonMeta', "translation_table", "unavailable_chars"]




