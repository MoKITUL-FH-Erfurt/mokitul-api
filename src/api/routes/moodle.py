import os
from typing import List
from api.chat_engine import get_query_engine_memoized
from api.utils.chains import get_llm
from api.utils.downloads import build_moodle_download_url, download, download_file
from definitions import DATA_DIR
from fastapi import APIRouter
from pydantic import BaseModel, Field

from llama_index.core.chat_engine import CondenseQuestionChatEngine,SimpleChatEngine

from llama_index.core.query_engine import BaseQueryEngine

from llama_index.core.indices.base_retriever import BaseRetriever

from llama_index.core import (
    Settings,
)

from llama_index.core import (
    SimpleDirectoryReader,

)
router = APIRouter()

class SummarizeFileRequest(BaseModel):
    message: str = Field(...)

def split_into_chunks(text, max_length):
    # Split the text into words
    words = text.split()
    chunks = []
    current_chunk = []

    current_length = 0
    for word in words:
        # Check if adding the next word would exceed the max_length
        if current_length + len(word) + 1 > max_length:  # +1 for space
            # If so, join the current_chunk into one string and add to chunks
            chunks.append(' '.join(current_chunk))
            # Start a new chunk
            current_chunk = [word]
            current_length = len(word)
        else:
            # If not, add the word to the current_chunk
            current_chunk.append(word)
            current_length += len(word) + 1  # +1 for space

    # Add the last chunk if it's not empty
    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks

@router.get("/summary/{fileId}")
async def summarize_single_file_from_moodle(fileId: str):
    file_path = os.path.join(DATA_DIR, fileId + ".pdf")

    # check if file exists
    if (not os.path.exists(file_path)):
        print("file does not exist")
        print("downloading file...")

        download(fileId, file_path)

    documents = SimpleDirectoryReader(input_files=[file_path]).load_data()

    document = documents[0]

    context_length_limit = 4069

    full_text = document.get_content()

    chunks = split_into_chunks(full_text, context_length_limit)

    Settings.llm = get_llm()

    chat_engine = SimpleChatEngine.from_defaults(system_prompt="""You are an excellent academic paper reviewer. You conduct paper summarization on the full paper text provided by the user, with following instructions:

REVIEW INSTRUCTION:

Summary of Academic Paper's Technical Approach use h1 tag

1. Title and authors of the Paper: use h3 tag
   Provide the title and authors of the paper.

2. Main Goal and Fundamental Concept: use h3 tag
   Begin by clearly stating the primary objective of the research presented in the academic paper. Describe the core idea or hypothesis that underpins the study in simple, accessible language.

3. Technical Approach: use h3 tag
   Provide a detailed explanation of the methodology used in the research. Focus on describing how the study was conducted, including any specific techniques, models, or algorithms employed. Avoid delving into complex jargon or highly technical details that might obscure understanding.

4. Distinctive Features: use h3 tag
   Identify and elaborate on what sets this research apart from other studies in the same field. Highlight any novel techniques, unique applications, or innovative methodologies that contribute to its distinctiveness.

5. Experimental Setup and Results: use h3 tag
   Describe the experimental design and data collection process used in the study. Summarize the results obtained or key findings, emphasizing any significant outcomes or discoveries.

6. Advantages and Limitations: use h3 tag
   Concisely discuss the strengths of the proposed app4. roach, including any benefits it offers over existing methods. Also, address its limitations or potential drawbacks, providing a balanced view of its efficacy and applicability.

7. Conclusion: use h3 tag
   Sum up the key points made about the paper's technical approach, its uniqueness, and its comparative advantages and limitations. Aim for clarity and succinctness in your summary.

OUTPUT INSTRUCTIONS:

1. Only use the headers provided in the instructions above.
2. Format your output in HTML using HTML-Elements (h1,h2,h3, ul,li, div, span, p).
3. Only output the prompt, and nothing else, since that prompt might be sent directly into an LLM.

PAPER TEXT INPUT:""")

    summaries = []
    for chunk in chunks:
        response = chat_engine.chat(message="Please provide a summary of the following piece of a document: " + chunk)

        summaries.append(response.__str__())

    response = chat_engine.chat(message="Please provide a single cohesive summary using the following summaries for chunks of a document: " + "".join(summaries))

    return { 'success': True, 'response': response.__str__()}
