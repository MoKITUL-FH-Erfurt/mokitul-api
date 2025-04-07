from datetime import datetime


def get_posix_timestamp() -> float:
    return datetime.now().timestamp()
