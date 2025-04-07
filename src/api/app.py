from api.model import NotFoundException
from core import str_to_bool
from core.settings import ENABLE_LLM_PATH, ROOT_PATH
from config.config_loader import ConfigLoader
from fastapi import FastAPI, HTTPException, Request

from application_startup import Application
from api.routes.v1.conversations import (
    ConversationAPI,
    ConvesationAPIConfig,
)

Application.Instance().startup()
config_loader = ConfigLoader.get_instance()


tags_metadata = [
    {
        "name": "v1",
        "description": "API version 1, check link on the right",
        "externalDocs": {
            "description": "sub-docs",
            "url": "http://127.0.0.1:8000/api/v1/docs",
        },
    },
]

app = FastAPI(
    root_path=f"{config_loader.get_value(ROOT_PATH)}",
    openapi_tags=tags_metadata,
    title="MoKITUL API",
    version="0.1.0",
)

# PUBLISHED version 1 of the API
v1 = FastAPI()
conversationAPI = ConversationAPI(
    config=ConvesationAPIConfig(
        start_llm_path=str_to_bool(config_loader.get_value(ENABLE_LLM_PATH))
    )
)

v1.include_router(
    conversationAPI.get_rounter(), tags=["Conversation"], prefix="/conversations"
)
# v1.include_router(MoodleRouter, tags=["Moodle"], prefix="/moodle")

# mount the playground and v1 routers
app.mount("/v1", v1)


@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to this fantastic app!"}


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    try:
        raise exc
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=f"{str(e)}")
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing key: {str(e)}")
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=f"Permission denied: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
