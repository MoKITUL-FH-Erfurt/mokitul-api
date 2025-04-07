from core.request_timer import RequestTimer
from core.singelton import SingletonMeta
from moodle.downloads import MoodleClient, MoodleFile


class MoodleUsecase(metaclass=SingletonMeta):
    _moodle_client: MoodleClient

    def __init__(self, moodle_client: MoodleClient) -> None:
        self._moodle_client = moodle_client

    @classmethod
    def create(cls, moodle_client: MoodleClient):
        if cls not in SingletonMeta._instances:
            return cls(moodle_client)
        else:
            raise RuntimeError("Singleton instance already created.")

    @classmethod
    def Instance(cls) -> "MoodleUsecase":
        if cls not in SingletonMeta._instances:
            raise RuntimeError(
                "Singleton instance has not been created yet. Call `create` first."
            )
        return SingletonMeta._instances[cls]

    def download_file(self, file_id: str) -> MoodleFile:
        timer = RequestTimer()
        timer.start("Download File form Moodle")
        file = self._moodle_client.download(file_id=file_id)
        timer.end()
        return file

    def get_file_ids_to_course(self, course_id: str) -> list[str]:
        timer = RequestTimer()
        timer.start("Download File form Moodle")
        result = self._moodle_client.get_file_ids_for_course(courseId=course_id)
        timer.end()
        return result
