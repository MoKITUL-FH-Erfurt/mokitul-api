from langchain.prompts import PromptTemplate
from langchain.chains.llm import LLMChain
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain.schema.document import Document
from typing import List
from langchain.llms import ollama



from langchain.agents.agent import LLMSingleActionAgent

class CustomRetriever(BaseRetriever):
    """Always return three static documents for testing."""

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        return [
            Document(page_content="Japan has a population of 126 million people.", metadata={"source": "https://en.wikipedia.org/wiki/Japan"}),
            Document(page_content="Japanese people are very polite.", metadata={"source": "https://en.wikipedia.org/wiki/Japanese_people"}),
            Document(page_content="United States has a population of 328 million people.", metadata={"source": "https://en.wikipedia.org/wiki/United_States"}),
            ]

prompt_template = """Use the following pieces of context to answer the question at the end. Please follow the following rules:
1. If the question is to request links, please only return the source links with no answer.
2. If you don't know the answer, don't try to make up an answer. Just say **I can't find the final answer but you may want to check the following links** and add the source links as a list.
3. If you find the answer, write the answer in a concise way and add the list of sources that are **directly** used to derive the answer. Exclude the sources that are irrelevant to the final answer.

{context}

Question: {question}
Helpful Answer:"""


def main():
    retriever = CustomRetriever()
    QA_CHAIN_PROMPT = PromptTemplate.from_template(prompt_template) # prompt_template defined above

    llm = ollama.Ollama(model="llama3", base_url="http://localhost:11434")

    llm_chain = LLMChain(llm=llm, prompt=QA_CHAIN_PROMPT, callbacks=None, verbose=True)
    document_prompt = PromptTemplate(
        input_variables=["page_content", "source"],
        template="Context:\ncontent:{page_content}\nsource:{source}",
    )
    combine_documents_chain = StuffDocumentsChain(
        llm_chain=llm_chain,
        document_variable_name="context",
        document_prompt=document_prompt,
        callbacks=None,
    )
    qa = RetrievalQA(
        combine_documents_chain=combine_documents_chain,
        callbacks=None,
        verbose=True,
        retriever=retriever,
        return_source_documents=True,
    )
    res=qa("Hey how are you?")
    print(res['result'])
    res = qa("How many people live in Japan?")
    print(res['result'])
    res = qa("How many people live in US?")
    print(res['result'])
    res = qa("How many people live in Singapore?")
    print(res['result'])

if __name__ == "__main__":
    main()
