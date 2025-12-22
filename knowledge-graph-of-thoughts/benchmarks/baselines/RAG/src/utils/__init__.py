






import asyncio
import os
import pickle
import random
import re
import textwrap
from enum import Enum
from typing import List
import fitz
import numpy as np
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAIEmbeddings
from openai import RateLimitError
from pydantic import BaseModel, Field
from rank_bm25 import BM25Okapi
from benchmarks.baselines.RAG.src.utils.simplified_utils import get_model_configurations
def replace_t_with_space(list_of_documents):
    Replaces all tab characters ('\t') with spaces in the page content of each document
    Args:
        list_of_documents: A list of document objects, each with a 'page_content' attribute.
    Returns:
        The modified list of documents with tab characters replaced by spaces.
    for doc in list_of_documents:
        doc.page_content = doc.page_content.replace('\t', ' ')
    return list_of_documents
def text_wrap(text, width=120):
    Wraps the input text to the specified width.
    Args:
        text (str): The input text to wrap.
        width (int): The width at which to wrap the text.
    Returns:
        str: The wrapped text.
    return textwrap.fill(text, width=width)
def encode_pdf(path, chunk_size=1000, chunk_overlap=200):
    Encodes a PDF book into a vector store using OpenAI embeddings.
    Args:
        path: The path to the PDF file.
        chunk_size: The desired size of each text chunk.
        chunk_overlap: The amount of overlap between consecutive chunks.
    Returns:
        A FAISS vector store containing the encoded book content.

    load_dotenv()

    loader = PyPDFLoader(path)
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap, length_function=len
    )
    texts = text_splitter.split_documents(documents)
    cleaned_texts = replace_t_with_space(texts)

    config = get_model_configurations('openai-embedding')
    embeddings = OpenAIEmbeddings(**config)
    vectorstore = FAISS.from_documents(cleaned_texts, embeddings)
    return vectorstore
def encode_from_string(content, chunk_size=1000, chunk_overlap=200):
    Encodes a string into a vector store using OpenAI embeddings.
    Args:
        content (str): The text content to be encoded.
        chunk_size (int): The size of each chunk of text.
        chunk_overlap (int): The overlap between chunks.
    Returns:
        FAISS: A vector store containing the encoded content.
    Raises:
        ValueError: If the input content is not valid.
        RuntimeError: If there is an error during the encoding process.

    load_dotenv()
    if not isinstance(content, str) or not content.strip():
        raise ValueError("Content must be a non-empty string.")
    if not isinstance(chunk_size, int) or chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer.")
    if not isinstance(chunk_overlap, int) or chunk_overlap < 0:
        raise ValueError("chunk_overlap must be a non-negative integer.")
    try:

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )
        chunks = text_splitter.create_documents([content])

        for chunk in chunks:
            chunk.metadata['relevance_score'] = 1.0

        config = get_model_configurations('openai-embedding')
        embeddings = OpenAIEmbeddings(**config)
        vectorstore = FAISS.from_documents(chunks, embeddings)
    except Exception as e:
        raise RuntimeError(f"An error occurred during the encoding process: {str(e)}")
    return vectorstore
def retrieve_context_per_question(question, chunks_query_retriever):
    Retrieves relevant context and unique URLs for a given question using the chunks query retriever.
    Args:
        question: The question for which to retrieve context and URLs.
    Returns:
        A tuple containing:
        - A string with the concatenated content of relevant documents.
        - A list of unique URLs from the metadata of the relevant documents.

    docs = chunks_query_retriever.get_relevant_documents(question)

    context = [doc.page_content for doc in docs]
    return context
class QuestionAnswerFromContext(BaseModel):
    Model to generate an answer to a query based on a given context.

    Attributes:
        answer_based_on_content (str): The generated answer based on the context.
    answer_based_on_content: str = Field(description="Generates an answer to a query based on a given context.")
def create_question_answer_from_context_chain(llm):

    question_answer_from_context_llm = llm

    For the question below, provide a concise but suffice answer based ONLY on the provided context:
    {context}
    Question
    {question}

    question_answer_from_context_prompt = PromptTemplate(
        template=question_answer_prompt_template,
        input_variables=["context", "question"],
    )

    question_answer_from_context_cot_chain = question_answer_from_context_prompt | question_answer_from_context_llm.with_structured_output(
        QuestionAnswerFromContext)
    return question_answer_from_context_cot_chain
def answer_question_from_context(question, context, question_answer_from_context_chain):
    Answer a question using the given context by invoking a chain of reasoning.
    Args:
        question: The question to be answered.
        context: The context to be used for answering the question.
    Returns:
        A dictionary containing the answer, context, and question.
    input_data = {
        "question": question,
        "context": context
    }
    print("Answering the question from the retrieved context...")
    output = question_answer_from_context_chain.invoke(input_data)
    answer = output.answer_based_on_content
    return {"answer": answer, "context": context, "question": question}
def show_context(context):
    Display the contents of the provided context list.
    Args:
        context (list): A list of context items to be displayed.
    Prints each context item in the list with a heading indicating its position.
    for i, c in enumerate(context):
        print(f"Context {i + 1}:")
        print(c)
        print("\n")
def read_pdf_to_string(path):
    Read a PDF document from the specified path and return its content as a string.
    Args:
        path (str): The file path to the PDF document.
    Returns:
        str: The concatenated text content of all pages in the PDF document.
    The function uses the 'fitz' library (PyMuPDF) to open the PDF document, iterate over each page,
    extract the text content from each page, and append it to a single string.

    doc = fitz.open(path)
    content = ""

    for page_num in range(len(doc)):

        page = doc[page_num]

        content += page.get_text()
    return content
def bm25_retrieval(bm25: BM25Okapi, cleaned_texts: List[str], query: str, k: int = 5) -> List[str]:
    Perform BM25 retrieval and return the top k cleaned text chunks.
    Args:
        bm25 (BM25Okapi): Pre-computed BM25 index.
        cleaned_texts (List[str]): List of cleaned text chunks corresponding to the BM25 index.
        query (str): The query string.
        k (int): The number of text chunks to retrieve.
    Returns:
        List[str]: The top k cleaned text chunks based on BM25 scores.

    query_tokens = query.split()

    bm25_scores = bm25.get_scores(query_tokens)

    top_k_indices = np.argsort(bm25_scores)[::-1][:k]

    top_k_texts = [cleaned_texts[i] for i in top_k_indices]
    return top_k_texts
async def exponential_backoff(attempt):
    Implements exponential backoff with a jitter.

    Args:
        attempt: The current retry attempt number.

    Waits for a period of time before retrying the operation.
    The wait time is calculated as (2^attempt) + a random fraction of a second.

    wait_time = (2 ** attempt) + random.uniform(0, 1)
    print(f"Rate limit hit. Retrying in {wait_time:.2f} seconds...")

    await asyncio.sleep(wait_time)
async def retry_with_exponential_backoff(coroutine, max_retries=5):
    Retries a coroutine using exponential backoff upon encountering a RateLimitError.

    Args:
        coroutine: The coroutine to be executed.
        max_retries: The maximum number of retry attempts.

    Returns:
        The result of the coroutine if successful.

    Raises:
        The last encountered exception if all retry attempts fail.
    for attempt in range(max_retries):
        try:

            return await coroutine
        except RateLimitError as e:

            if attempt == max_retries - 1:
                raise e

            await exponential_backoff(attempt)

    raise Exception("Max retries reached")

class EmbeddingProvider(Enum):
    OPENAI = "openai"
    COHERE = "cohere"
    AMAZON_BEDROCK = "bedrock"

class ModelProvider(Enum):
    OPENAI = "openai"
    GROQ = "groq"
    ANTHROPIC = "anthropic"
    AMAZON_BEDROCK = "bedrock"
def get_langchain_embedding_provider(provider: EmbeddingProvider, model_id: str = None):
    Returns an embedding provider based on the specified provider and model ID.
    Args:
        provider (EmbeddingProvider): The embedding provider to use.
        model_id (str): Optional -  The specific embeddings model ID to use.
    Returns:
        A LangChain embedding provider instance.
    Raises:
        ValueError: If the specified provider is not supported.
    if provider == EmbeddingProvider.OPENAI:
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings()
    elif provider == EmbeddingProvider.COHERE:
        from langchain_cohere import CohereEmbeddings
        return CohereEmbeddings()
    elif provider == EmbeddingProvider.AMAZON_BEDROCK:
        from langchain_community.embeddings import BedrockEmbeddings
        return BedrockEmbeddings(model_id=model_id) if model_id else BedrockEmbeddings(model_id="amazon.titan-embed-text-v2:0")
    else:
        raise ValueError(f"Unsupported embedding provider: {provider}")
def encode_corpus_file(corpus_path, save_dir=None):
    Encodes a corpus text file into a vector store. Each chunk in the file is treated as a separate document.
    The chunks are separated by chunk headers in the format "--- Chunk X ---".

    Args:
        corpus_path (str): Path to the corpus file (corpus_?.txt)
        save_dir (str, optional): Directory to store (intermediate) results. If None, results won't be saved.

    Returns:
        FAISS: A vector store containing the encoded chunks.

    load_dotenv()

    print(f"Reading corpus file from {corpus_path}...")


    with open(corpus_path, 'r', encoding='utf-8') as f:
        content = f.read()



    pattern = r'--- Chunk \d+ ---\s*(.*?)(?=--- Chunk \d+ ---|$)'

    matches = re.findall(pattern, content, re.DOTALL)


    documents = []
    for chunk_num, chunk_content in enumerate(matches, 1):
        if chunk_content.strip():

            doc = Document(
                page_content=chunk_content.strip(),
                metadata={
                    'chunk_num': chunk_num,
                    'source': os.path.basename(corpus_path)
                }
            )
            documents.append(doc)

    print(f"Extracted {len(documents)} chunks from corpus file.")


    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
        corpus_filename = os.path.basename(corpus_path)
        documents_path = os.path.join(save_dir, f"{corpus_filename}_documents.pkl")
        with open(documents_path, 'wb') as f:
            pickle.dump(documents, f)
        print(f"Saved documents to {documents_path}")


    print("Generating embeddings...")
    config = get_model_configurations('openai-embedding')
    embeddings = OpenAIEmbeddings(**config)

    vectorstore = FAISS.from_documents(documents, embeddings)


    if save_dir:

        faiss_index_path = os.path.join(save_dir, f"{corpus_filename}_faiss_index")
        vectorstore.save_local(faiss_index_path)
        print(f"Saved FAISS index to {faiss_index_path}")

    return vectorstore