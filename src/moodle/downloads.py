from abc import ABC, abstractmethod
import re
import logging
import os
from typing import Optional
import requests
from pydantic import BaseModel
from requests.models import Response
from textwrap import wrap


logger = logging.getLogger(__name__)

API_KEY_QUERY_PARAMETER = "api_key"
FILE_ID_QUERY_PARAMETER = "file_id"


class MoodleConfig(BaseModel):
    moodle_host: str
    api_key: str
    file_store_location: str
    timeout: float


class MoodleFile(BaseModel):
    id: str
    org_filename: Optional[str]
    local_filename: str
    has_been_downloaded: bool


class MoodleClient(ABC):
    """
    Interface for Moodle client.
    This interface defines the methods for downloading files from Moodle and getting file IDs for a course.
    Can be extended in the future to support other Moodle operations.
    """

    @abstractmethod
    def download(self, file_id: str) -> MoodleFile:
        pass

    @abstractmethod
    def get_file_ids_for_course(self, courseId: str) -> list[str]:
        pass


class MoodleClientImplementation(MoodleClient):
    """
    Implementation of the Moodle client.
    """
    _config: MoodleConfig

    def __init__(self, config) -> None:
        self._config = config

    def _build_moodle_download_url(self, id) -> str:
        return f"{self._config.moodle_host}/local/mokitul/api/download.php?{FILE_ID_QUERY_PARAMETER}={id}&{API_KEY_QUERY_PARAMETER}={self._config.api_key}"

    def _throw_from_http_request(self, response: Response):
        raise Exception(
            f"Failed to request file {response.status_code}, {response.raw._body}"
        )

    def download(self, file_id: str) -> MoodleFile:
        downloadUrl = self._build_moodle_download_url(file_id)
        file = os.path.join(self._config.file_store_location, f"{file_id}.pdf")

        if os.path.exists(file):
            logger.info(f"File with FileID{file_id} already downloaded")
            return MoodleFile(
                id=file_id,
                local_filename=file,
                org_filename="",
                has_been_downloaded=False,
            )

        responseFileRequest = requests.get(
            url=downloadUrl, verify=False, timeout=self._config.timeout
        )
        filenameHeader = responseFileRequest.headers["content-disposition"]
        match = re.search(r'"(.*?)"', filenameHeader)
        if match:
            filenameHeader = match.group(1)

        with open(file,"wb") as writer:
            writer.write(responseFileRequest.content)

        return MoodleFile(
            id=file_id,
            local_filename=file,
            org_filename=filenameHeader,
            has_been_downloaded=True,
        )

    def get_file_ids_for_course(self, courseId: str) -> list[str]:
        response = requests.get(
            url=f"{self._config.moodle_host}/local/mokitul/api/files.php?course_id={courseId}&{API_KEY_QUERY_PARAMETER}={self._config.api_key}",
            verify=False,
            timeout=self._config.timeout,
        )
        if response.ok:
            return response.json()
        self._throw_from_http_request(response=response)
