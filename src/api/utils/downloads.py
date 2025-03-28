
import os
from api.settings import MOODLE_URL
from definitions import DATA_DIR
import requests

moodle_url = MOODLE_URL

# OMITTED
#
# This function is not used anymore.
def build_moodle_download_url(id: str):
    return f"{moodle_url}/mod/mokitul/download.php?id={id}"

def build_moodle_v1_download_url(id):
    # concat id with base api url
    #
    api_key = "6ed36077-6d13-419c-89b7-f6af233294d3"

    return f"{moodle_url}/local/mokitul/api/download.php?file_id={id}&api_key={api_key}"


def download_file(url: str, id: str, courseId: str):
    try:
        responseFileRequest = requests.get(url=url)

        print(responseFileRequest)
        print(responseFileRequest.headers)

        filenameHeader = responseFileRequest.headers["content-disposition"]

        filetype = filenameHeader.split(".")[-1].replace('"','')
        filename =  id + "." + filetype
        filedir = os.path.join(DATA_DIR, courseId)

        os.makedirs(filedir, exist_ok=True)

        file_path = os.path.join(filedir, filename)
        with open(file_path, 'wb') as writer:
            writer.write(responseFileRequest.content)
    except Exception as e:
        print(e)
        return False
    return True

def download(file_id: str, file_path: str) -> None:
    if (file_id is None or file_id == "" ):
        return

    downloadUrl = build_moodle_v1_download_url(file_id)

    print("downloading file from: ", downloadUrl)

    if (not os.path.exists(DATA_DIR)):
        os.makedirs(DATA_DIR)

    try:
        responseFileRequest = requests.get(url=downloadUrl, verify=False)

        with open(file_path, 'wb') as writer:
            writer.write(responseFileRequest.content)

    except Exception as e:
        print(e)

def get_file_ids_for_course(courseId: str):
    course_files = []
    try:
        response = requests.get(url=f"{moodle_url}/local/mokitul/api/files.php?course_id={courseId}", verify=False)

        print(response)

        course_files = response.json()
    except Exception as e:
        print(e)
    return course_files
