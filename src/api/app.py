from fastapi import APIRouter, FastAPI

from api.routes.moodle import router as MoodleRouter

from api.routes.v1.conversations import router as ConversationRouterV1

import logging
logging.basicConfig(level=logging.DEBUG)

tags_metadata = [
    {
        'name': 'v1',
        "description": "API version 1, check link on the right",
        'externalDocs': {
            'description': 'sub-docs',
            'url': 'http://127.0.0.1:8000/api/v1/docs'
        }
    },
]

app = FastAPI(root_path="/api", openapi_tags=tags_metadata, title="MoKITUL API", version="0.1.0")

# PUBLISHED version 1 of the API
v1 = FastAPI()

v1.include_router(ConversationRouterV1, tags=["Conversation"], prefix="/conversations")
v1.include_router(MoodleRouter, tags=["Moodle"], prefix="/moodle")

# mount the playground and v1 routers
app.mount("/v1", v1)

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to this fantastic app!"}
