from pinecone import Pinecone
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
import json
from pathlib import Path
import google.generativeai as genai 
import os
from dotenv import load_dotenv

load_dotenv()

def ingest_files_to_vector_db(folder_path: str) ->dict:
    """
    📂 Tool: Ingest File into Vector DB (Pinecone)

    This tool takes a folder path (e.g., `organized_docs/resumes/`) containing multiple PDF resumes,
    performs text extraction and chunking, and ingests the chunks into a Pinecone vector index for retrieval.

    🔁 Input:
        - folder_path (str): Path to the folder containing PDF resumes.

    ✅ Output:
        - status: "success" or "error"
        - ingested_files: list of file names successfully processed
        - total_chunks: total number of vector records inserted
        - error_message: (optional) if any issue occurred

    Typical use: Helps enable semantic search across all ingested resumes.
    """
    
    # --- Pinecone Setup --- #
    pc = Pinecone(api_key="pcsk_57AL2C_7hXUSPp2nUeWKqGFuEZRdE5RrSjbcirQNrXUQ4h3CGo55ZVq5KM5BXpTc6PSpsk")
    index_name = "hybrid-search-demo"
    namespace = "document-chunks"
    # --- Create index if needed --- #
    if not pc.has_index(index_name):
        pc.create_index_for_model(
            name=index_name,
            cloud="aws",
            region="us-east-1",
            embed={
            "model": "llama-text-embed-v2",
            "field_map": {"text": "chunk_text"}
            }
        )

    index = pc.Index(index_name)

    desc = index.describe_index_stats()
    print(desc)
    
    # --- Text Splitter --- #
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    
    # ------ Main Function  -----#
    folder = Path(folder_path)
    if not folder.exists():
        return {
            "status": "error",
            "ingested_files": [],
            "total_chunks": 0,
            "error_message": f"Folder not found: {folder_path}"
        }
        
    record_file = folder / ".ingested_files.json"
    if record_file.exists():
        with open(record_file, "r") as f:
            already_ingested = set(json.load(f))
    else:
        already_ingested = set()
    
    total_chunks = 0
    ingested_files = []


    try:
        for pdf_file in folder.glob("*.pdf"):
            if pdf_file.name in already_ingested:
                continue

            loader = PyPDFLoader(str(pdf_file))
            docs = loader.load()

            if not docs:
                continue

            chunks = splitter.split_documents(docs)
            records = [
                {
                    "_id": f"{pdf_file.stem}-chunk-{i}",
                    "chunk_text": chunk.page_content,
                    "category": "resumes"
                }
                for i, chunk in enumerate(chunks)
            ]

            index.upsert_records(namespace=namespace, records=records)
            total_chunks += len(records)
            ingested_files.append(pdf_file.name)
            already_ingested.add(pdf_file.name)

        # --- Save updated list of ingested files --- #
        with open(record_file, "w") as f:
            json.dump(sorted(list(already_ingested)), f)

        return {
            "status": "success",
            "ingested_files": ingested_files,
            "total_chunks": total_chunks,
            "error_message": None
        }

    except Exception as e:
        return {
            "status": "error",
            "ingested_files": ingested_files,
            "total_chunks": total_chunks,
            "error_message": str(e)
        }

def query_vector_db(query: str, top_k: int = 5) -> dict:
    """
    🤖 Tool: Query Vector DB and generate synthesized answer

    - Performs a semantic search over the vector DB
    - Sends top-k results to an LLM to generate a natural language answer
    """
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel("gemini-2.0-flash")
    # --- Pinecone Setup --- #
    
    pc = Pinecone(api_key="pcsk_57AL2C_7hXUSPp2nUeWKqGFuEZRdE5RrSjbcirQNrXUQ4h3CGo55ZVq5KM5BXpTc6PSpsk") 
    index_name = "hybrid-search-demo"
    namespace = "document-chunks"
    index = pc.Index(index_name)
    
    try:
        search_results = index.search(
            namespace=namespace,
            query={"top_k": top_k, "inputs": {"text": query}}
        )

        hits = search_results["result"]["hits"]
        if not hits:
            return {
                "status": "no_results",
                "answer": "No relevant information found.",
                "source_chunks": []
            }

        source_chunks = [hit["fields"]["chunk_text"] for hit in hits]
        context = "\n\n".join(source_chunks)

        prompt = f"""You are an expert assistant answering questions based on extracted  chunks.
Here is the question:
{query}

And here is the context:
{context}

Please answer concisely and accurately based only on the above context.
"""

        response = model.generate_content([prompt])
        parts = response.candidates[0].content.parts
        answer_text = parts[0].text if parts and hasattr(parts[0], 'text') else str(parts[0])
        
        return {
            "status": "success",
            "answer" : answer_text,
            "source_chunks": source_chunks
        }

    except Exception as e:
        return {
            "status": "error",
            "answer": None,
            "source_chunks": [],
            "error_message": str(e)
        }

