import os
import glob
from typing import List
from pathlib import Path

from langchain_community.document_loaders import Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ibm import WatsonxEmbeddings
# Fallback to OpenAI or HuggingFace if WatsonX fails/is missing
from langchain_community.embeddings import FakeEmbeddings 

from jarvis.config import (
    DATASETS_DIR, 
    RAW_DATASETS_DIR,
    VECTOR_STORE_PATH, 
    WATSONX_API_KEY, 
    WATSONX_URL, 
    WATSONX_PROJECT_ID
)

def get_embeddings():
    """
    Returns WatsonxEmbeddings if credentials exist, else FakeEmbeddings for testing.
    """
    if WATSONX_API_KEY and WATSONX_URL and WATSONX_PROJECT_ID:
        try:
            return WatsonxEmbeddings(
                model_id="intfloat/multilingual-e5-large",
                url=WATSONX_URL,
                apikey=WATSONX_API_KEY,
                project_id=WATSONX_PROJECT_ID,
                params={"truncate_input_tokens": 510}
            )
        except Exception as e:
            print(f"Warning: Failed to init WatsonxEmbeddings: {e}")
    
    print("Using FakeEmbeddings (Placeholder).")
    return FakeEmbeddings(size=1024)

def ingest_documents():
    """
    Ingests all .docx files from raw_datasets/ into the Vector Store.
    
    Expected structure:
    raw_datasets/
        *.docx (client documents)
    """
    embeddings = get_embeddings()
    vector_store = Chroma(
        collection_name="client_data",
        embedding_function=embeddings,
        persist_directory=str(VECTOR_STORE_PATH)
    )

    # Find all .docx files in raw_datasets
    docx_files = list(RAW_DATASETS_DIR.glob("*.docx"))
    
    if not docx_files:
        print(f"No .docx files found in {RAW_DATASETS_DIR}")
        return

    all_splits = []
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, add_start_index=True)
    
    print(f"Found {len(docx_files)} documents in raw_datasets/")
    
    for file_path in docx_files:
        try:
            # Extract client name from filename (remove .docx extension)
            client_name = file_path.stem
            
            loader = Docx2txtLoader(str(file_path))
            docs = loader.load()
            
            # Add metadata
            for doc in docs:
                doc.metadata["client"] = client_name
                doc.metadata["source_file"] = file_path.name
                doc.metadata["source_path"] = str(file_path.relative_to(RAW_DATASETS_DIR.parent))
            
            splits = text_splitter.split_documents(docs)
            all_splits.extend(splits)
            print(f"  ✓ {file_path.name} ({len(splits)} chunks)")
        except Exception as e:
            print(f"  ✗ Failed to process {file_path.name}: {e}")

    if all_splits:
        print(f"\n{'='*60}")
        print(f"Adding {len(all_splits)} total chunks to vector store...")
        vector_store.add_documents(documents=all_splits)
        print(f"✓ Successfully ingested into ChromaDB at: {VECTOR_STORE_PATH}")
        print(f"{'='*60}")
    else:
        print("\n⚠ No documents were successfully processed.")

def query_vector_store(query: str, k: int = 4):
    """
    Queries the vector store for relevant documents.
    """
    embeddings = get_embeddings()
    vector_store = Chroma(
        collection_name="client_data",
        embedding_function=embeddings,
        persist_directory=str(VECTOR_STORE_PATH)
    )
    
    results = vector_store.similarity_search(query, k=k)
    return results
