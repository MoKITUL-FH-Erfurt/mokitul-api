import threading


class SingletonMeta(type):
    """
    A metaclass for creating Singleton classes.
    This ensures that only one instance of the class exists.
    """

    _instances = {}
    _lock = threading.Lock()  # A lock for thread-safe singleton

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            # If an instance does not exist, create it and store it
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class Singleton(metaclass=SingletonMeta):
    """
    Example class that uses the SingletonMeta metaclass.
    """

    _initialized = False

    def __init__(self, value=None):
        if not self._initialized:
            self.value = value
            self._initialized = True

    @classmethod
    def create(cls, *args, **kwargs):
        if cls not in SingletonMeta._instances:
            return cls(*args, **kwargs)
        else:
            raise RuntimeError("Singleton instance already created.")

    @classmethod
    def Instance(cls) -> "Singleton":
        if cls not in SingletonMeta._instances:
            raise RuntimeError(
                "Singleton instance has not been created yet. Call `create` first."
            )
        return SingletonMeta._instances[cls]
