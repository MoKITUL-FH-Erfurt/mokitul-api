from api.settings import PORT
import uvicorn

import logging


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    uvicorn.run("api.app:app", host="0.0.0.0", port=PORT, reload=True)
