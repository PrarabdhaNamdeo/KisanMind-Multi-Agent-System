from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

CHROMA_DIR = "data/chroma_db"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
TOP_K = 3   # return top 3 most relevant chunks


def load_vector_store() -> Chroma:
    """Load existing ChromaDB — must run ingest.py first."""
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )

    vector_store = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings
    )
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

    # similarity_search embeds the query and finds closest chunks
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