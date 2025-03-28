import os
from typing import Annotated, List, Optional
import logging

from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.readers.file.docs.base import Path
from api.chat_engine import get_chat_engine
from api.storage import get_chroma_index
from api.utils.chains import get_llm
from api.utils.downloads import download, get_file_ids_for_course
from bson import ObjectId
from definitions import DATA_DIR
from llama_index.core import SimpleDirectoryReader
from llama_index.core.chat_engine import SimpleChatEngine
from llama_index.core.chat_engine.types import ChatMode
from llama_index.readers.file import PDFReader, PyMuPDFReader
from pydantic import BaseModel, BeforeValidator, Field
from llama_index.core.vector_stores import MetadataFilter, MetadataFilters, FilterOperator




PyObjectId = Annotated[str, BeforeValidator(str)]

class Context(BaseModel):
    fileIds: List[str] = Field(default=[])
    courseId: str | None = Field(default=None)

class Message(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=ObjectId())
    role: str = Field(...)
    content: str = Field(...)
    # created_at: str = Field(default=datetime.now().isoformat())

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "role": "user",
                    "content": "Hello, how are you?",
                }
            ]
        }
    }

class Conversation(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user: str = Field(...)
    messages: List[Message] = Field(default=[])
    context: Context = Field(...)
    timestamp: str | None = Field(default=None)
    summary: str | None = Field(default=None)


    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user": "1",
                    "messages": [],
                    "context": {
                        "fileIds": ["2", "4"],
                        "courseId": "1"
                    }
                }
            ]
        }
    }

# ----------------------------------------
# ----------------------------------------


def map_message(message: Message):
    return ChatMessage(role=MessageRole(message.role), content=message.content, additional_kwargs={})


def map_messages(messages: list[Message]):
    return [map_message(message) for message in messages]

# v1 of the app

from fastapi import APIRouter
from api.database import database

conversations_collection = database.get_collection("conversations")

router = APIRouter()
@router.get("/")
async def get_conversation(user_id: str, course_id: str | None = None, file_id: str | None = None):
    if not course_id and not file_id:
        entities = conversations_collection.find({ "user": user_id })

    elif course_id and not file_id:
        entities = conversations_collection.find({ "context.courseId": course_id, "user": user_id })

    elif not course_id and file_id:
        entities = conversations_collection.find({ "user": user_id, "context.fileIds": str(file_id) })

    elif course_id and file_id:
        entities = conversations_collection.find({ "context.courseId": course_id, "user": user_id, "context.fileIds": str(file_id) })

    conversations = []
    async for conversation in entities:
        conversations.append(Conversation(**conversation))

    return conversations

@router.post("/")
async def create_conversation(conversation: Conversation):
    print(conversation)

    result = await conversations_collection.insert_one(conversation.model_dump(by_alias=True, exclude={"id"}))

    inserted_conversation_id: ObjectId = result.inserted_id

    return { 'id': inserted_conversation_id.__str__() }

@router.get("/{user_id}")
async def all_conversations(user_id: str):
    conversations = []

    async for conversation in conversations_collection.find({ "user": user_id }):
        conversations.append(Conversation(**conversation))

    return conversations

class MessageRequest(BaseModel):
    message: str = Field(...)

@router.put("/{conversation_id}")
async def update_conversation(conversation_id: str, conversation_update: dict):
    existing_conversation = await conversations_collection.find_one({ "_id": ObjectId(conversation_id) })

    if existing_conversation is None:
        return { 'error': 'Conversation not found' }

    update_data = {k: v for k, v in conversation_update.items() if k not in {"id", "_id"}}

    result = await conversations_collection.update_one(
        { "_id": ObjectId(conversation_id) },
        { "$set": update_data }
    )

    return { 'id': conversation_id, 'modified': result.modified_count == 1 }

@router.put("/{conversation_id}/message")
async def send_message(conversation_id: str, message: MessageRequest):
    conversation = await conversations_collection.find_one({ "_id": ObjectId(conversation_id) })

    if conversation is None:
        return { 'error': 'Conversation not found' }

    conversation = Conversation(**conversation)

    course_id = conversation.context.courseId

    file_ids = []
    if (course_id is not None):
        logging.info("Getting files for course: ", conversation.context.courseId)
        file_ids = get_file_ids_for_course(course_id)

    if (conversation.context.fileIds):
        # download the files
        file_ids = conversation.context.fileIds + file_ids

    file_ids = list(set(file_ids))
    logging.info(f"Ensuring File IDs: {file_ids}")

    index = get_chroma_index()

    try:
        file_ids.remove('')
    except Exception as e:
        logging.debug('did not find empty str')

    for file_id in file_ids:

        # download the file
        file_path = os.path.join(DATA_DIR, file_id + ".pdf")

        # check if file exists
        if (not os.path.exists(file_path)):
            logging.info(f"file does not exist - downloading: {file_id}")

            download(file_id, file_path)

            # read pdf file and convert to document
            reader = SimpleDirectoryReader(input_files=[file_path])
            documents = reader.load_data()
            for document in documents:
                if course_id is not None:
                    document.metadata['course_id'] = course_id

                document.metadata['file_id'] = file_id

                logging.info('Read Document : ',vars(document))

                index.insert(document)

    filters = MetadataFilters(
        filters = [
            MetadataFilter(
                key="file_id", operator=FilterOperator.IN, value=file_ids
            )
        ]
    )

    chat_engine = SimpleChatEngine.from_defaults(llm=get_llm()) if (len(file_ids) == 0) else index.as_chat_engine(llm=get_llm(),chat_mode=ChatMode.CONDENSE_PLUS_CONTEXT, filters=filters)

    response = chat_engine.chat(chat_history=map_messages(conversation.messages), message=message.message)

    user_message = Message(role="user", content=message.message)
    response_message = str(response)

    print("Response: ", response_message)
    print("User Message: ", user_message)

    result = await conversations_collection.update_one(
        { "_id": ObjectId(conversation_id) },
        { "$push": { "messages": { "$each": [user_message.model_dump(by_alias=True), Message(role="assistant", content=response_message).model_dump(by_alias=True)] } } }
    )

    return { 'id': conversation_id, 'modified': result.modified_count == 1, 'answer': response_message }

@router.delete("/{conversation_id}")
async def delete_all_conversations(conversation_id: str):
    result = await conversations_collection.delete_many({ "_id": ObjectId(conversation_id) })

    return { 'deleted_count': result.deleted_count }

@router.put("/{conversation_id}/context/course")
async def add_course_context(conversation_id: str, courseId: str):
    result = await conversations_collection.update_one(
        { "_id": ObjectId(conversation_id) },
        { "$set": { "context.courseId": courseId } }
    )

    return { 'id': conversation_id }
