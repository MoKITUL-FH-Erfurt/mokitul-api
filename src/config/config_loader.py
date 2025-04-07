import os
from typing import Dict
from typing_extensions import Optional

from core import Result


class ConfigLoader:
    """
    Loads the configuration from the environment variables.
    """

    _instance = None
    config: Dict[str, str] = {}

    def __new__(cls, attributes: Optional[Dict[str, Optional[str]]] = None):
        if cls._instance is None:
            assert attributes is not None, (
                "Enviroment variables must be provided for the first initialization."
            )
            cls._instance = super().__new__(cls)
            result = cls._instance._load_config(attributes=attributes)
            assert result.is_ok()
        return cls._instance

    @staticmethod
    def load_config(attributes: Dict[str, Optional[str]]):
        ConfigLoader(attributes)

    @staticmethod
    def get_instance() -> "ConfigLoader":
        return ConfigLoader()

    def load_env(self, attribute: str) -> Optional[str]:
        return os.environ.get(attribute)

    def _load_config(self, attributes: Dict[str, Optional[str]]) -> Result[None]:
        config: Dict[str, str] = {}
        print(attributes)
        for key in attributes.keys():
            default_value = attributes[key]

            value = self.load_env(key)
            print(key)
            print(value)
            print("______________________")
            if value is not None:
                config[key] = value
                continue

            if default_value is not None:
                config[key] = default_value
                continue

            return Result.Err(Exception(f"No Value for Key {key} set"))
        self.config = config
        return Result.Ok()

    def get_value(self, key: str) -> str:
        return self.config.get(key, "")
