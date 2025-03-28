import requests

responseFileRequest = requests.get("http://localhost/mod/mokitul/download.php?id=34")

print(responseFileRequest)
