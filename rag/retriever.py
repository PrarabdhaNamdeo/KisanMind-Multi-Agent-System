import os
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

CHROMA_DIR = "data/chroma_db"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
TOP_K = 3  

_vector_store_cache = None  


def _chroma_store_is_empty(persist_dir: str) -> bool:
    """
    Checks if a usable ChromaDB already exists at persist_dir.
    Returns True if it's missing or empty (needs building).
    """
    if not os.path.isdir(persist_dir):
        return True
    
    return len(os.listdir(persist_dir)) == 0


def load_vector_store() -> Chroma:
    """
    Loads the ChromaDB vector store.
    If it doesn't exist yet (e.g. first run on a fresh deployment
    where data/chroma_db/ isn't committed to git), it builds it
    automatically from the PDFs in data/schemes/ before loading.
    """
    global _vector_store_cache
    if _vector_store_cache is not None:
        return _vector_store_cache

    if _chroma_store_is_empty(CHROMA_DIR):
        print(f"⚠️  No vector store found at {CHROMA_DIR} — building it now from PDFs...")
        
        from rag.ingest import ingest
        ingest()
        print("✅ Vector store built successfully.")

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )

    vector_store = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings
    )
    _vector_store_cache = vector_store
    return vector_store


def retrieve_schemes(query: str, top_k: int = TOP_K) -> list:
    """
    Main function called by SchemeAgent.

    Args:
        query: farmer's situation e.g.
               "tomato farmer in MP with Early Blight disease"
    Returns:
        List of dicts with 'content' and 'source' keys
    """
    vector_store = load_vector_store()

   
    results = vector_store.similarity_search(query, k=top_k)

    retrieved = []
    for doc in results:
        retrieved.append({
            "content": doc.page_content,
            "source": doc.metadata.get("scheme_name", "unknown")
        })

    return retrieved


def format_context(retrieved_chunks: list) -> str:
    """
    Format retrieved chunks into a clean string
    to pass as context to the LLM.
    """
    context = ""
    for i, chunk in enumerate(retrieved_chunks, 1):
        context += f"\n[Source: {chunk['source']}]\n"
        context += chunk['content']
        context += "\n" + "-"*40
    return context
