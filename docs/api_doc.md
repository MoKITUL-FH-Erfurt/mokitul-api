# 📘 MoKITUL API – v1

Welcome to the **MoKITUL API**, a conversation management backend with LLM integration, supporting file and course-based chat contexts.

> 🌐 Base URL: `http://127.0.0.1:8000/api/v1`

---

## 💬 Conversations API

### `GET /conversations/`

Retrieve a conversation using optional filters.

**Query Parameters:**
- `user_id` (string, required)
- `course_id` (string, optional)
- `file_id` (string, optional)
- `scope` (string, optional): one of `file`, `course`

**Curl:**
```bash
curl -X 'GET' \
  'http://127.0.0.1:8000/api/v1/conversations/?user_id=user_id&course_id=course_id&file_id=file_id&scope=file' \
  -H 'accept: application/json'
```

---

### `POST /conversations/`

Create a new conversation.

**Request Body (Conversation):**
```json
{
  "user": "1",
  "context": {
    "courseId": "1",
    "fileIds": ["2", "4"],
    "scope": "course"
  },
  "messages": []
}
```

**Curl:**
```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/api/v1/conversations/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "context": {
      "courseId": "1",
      "fileIds": ["2", "4"],
      "scope": "course"
    },
    "messages": [],
    "user": "1"
}'
```

---

### `GET /conversations/{user_id}`

Get all conversations for a user.

**Path Parameter:**
- `user_id` (string)

**Curl:**
```bash
curl -X 'GET' \
  'http://127.0.0.1:8000/api/v1/conversations/user_id' \
  -H 'accept: application/json'
```

---

### `PUT /conversations/{conversation_id}`

Update a conversation by ID.

**Request Body**: Partial or full `Conversation` object.

**Curl:**
```bash
curl -X 'PUT' \
  'http://127.0.0.1:8000/api/v1/conversations/conversation_id' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{}'
```

---

### `DELETE /conversations/{conversation_id}`

Delete a conversation.

**Curl:**
```bash
curl -X 'DELETE' \
  'http://127.0.0.1:8000/api/v1/conversations/conversation_id' \
  -H 'accept: application/json'
```

---

### `PUT /conversations/{conversation_id}/context/course`

Attach course context to a conversation.

**Query Parameter:**
- `courseId` (string)

**Curl:**
```bash
curl -X 'PUT' \
  'http://127.0.0.1:8000/api/v1/conversations/conversation_id/context/course?courseId=courseId' \
  -H 'accept: application/json'
```

---

## 💬 LLM Message API

> ⛔️ Requires `ENABLE_LLM_PATH=true` in config.

### `PUT /conversations/{conversation_id}/message`

Send a message to the LLM and receive a response.

**Request Body (MessageRequest):**
```json
{
  "message": "string",
  "model": "string"
}
```

**Response (ResponseMessage):**
```json
{
  "conversationId": "string",
  "response": "LLM response text",
  "timestamp": 1712547200.0,
  "nodes": [ /* list of Node objects */ ]
}
```

**Curl:**
```bash
curl -X 'PUT' \
  'http://127.0.0.1:8000/api/v1/conversations/sample_id/message' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "string",
    "model": "string"
}'
```

---

## 🧹 Data Models

### `Conversation`

```json
{
  "id": "string",
  "user": "string",
  "messages": [Message],
  "context": Context,
  "timestamp": "string",
  "summary": "string"
}
```

---

### `Context`

```json
{
  "fileIds": ["string"],
  "courseId": "string",
  "scope": "file | course"
}
```

**Enum: ChatScope**
- `file`: Conversation is scoped to specific files.
- `course`: Conversation uses all course files.

---

### 🔹 `Message`

```json
{
  "id": "string",
  "role": "user | assistant",
  "content": "Message text",
  "timestamp": 1712547200.0,
  "nodes": [Node]
}
```

---

### `MessageRequest`

```json
{
  "message": "User prompt string",
  "model": "LLM model name (e.g., gpt-4)"
}
```

---

### `ResponseMessage`

```json
{
  "conversationId": "string",
  "response": "Assistant's reply",
  "timestamp": 1712547200.0,
  "nodes": [Node]
}
```

### `Node`
```json
{
  "id": "string",
  "content": "string",
  "metadata": { "key": "value" },
  "relations": [], -> always empty
  "similarity_score": 0.97
}
```
