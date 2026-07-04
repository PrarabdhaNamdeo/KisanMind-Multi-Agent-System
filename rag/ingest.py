import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

SCHEMES_DIR = "data/schemes"
CHROMA_DIR = "data/chroma_db"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def load_pdfs(schemes_dir: str) -> list:
    """
    Load all PDFs from the schemes directory.
    Returns a list of Document objects (LangChain format).
    Each Document has .page_content (text) and .metadata (source file etc.)
    """
    all_documents = []

    pdf_files = [f for f in os.listdir(schemes_dir) if f.endswith(".pdf")]

    if not pdf_files:
        raise FileNotFoundError(f"No PDFs found in {schemes_dir}")

    print(f"📄 Found {len(pdf_files)} PDF files: {pdf_files}")

    for pdf_file in pdf_files:
        pdf_path = os.path.join(schemes_dir, pdf_file)
        print(f"  Loading: {pdf_file}")

        loader = PyPDFLoader(pdf_path)
        documents = loader.load()

        # Add scheme name to metadata so we know which PDF a chunk came from
        for doc in documents:
            doc.metadata["scheme_name"] = pdf_file.replace(".pdf", "")

        all_documents.extend(documents)

    print(f"\n✅ Loaded {len(all_documents)} pages total")
    return all_documents


def chunk_documents(documents: list) -> list:
    """
    Split documents into smaller chunks.

    WHY overlap? Imagine a sentence split across two chunks:
    Chunk 1: "...farmer must have valid Aadhaar"
    Chunk 2: "card and land records in their name..."

    Without overlap, both chunks lose context.
    With 50 char overlap, chunk 2 starts a bit earlier and keeps context.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " "]  
    )

    chunks = splitter.split_documents(documents)
    print(f"✂️  Split into {len(chunks)} chunks (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    return chunks


def create_vector_store(chunks: list) -> Chroma:
    """
    Convert chunks to embeddings and store in ChromaDB.

    HuggingFaceEmbeddings downloads the model locally on first run (~80MB).
    After that it's cached — no internet needed.
    """
    print(f"\n🔢 Loading embedding model: {EMBEDDING_MODEL}")
    print("   (First run downloads ~80MB — please wait)")

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},   
        encode_kwargs={"normalize_embeddings": True}
    )

    print(f"\n💾 Storing vectors in ChromaDB at: {CHROMA_DIR}")

    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DIR
    )

    print(f"✅ Vector store created with {vector_store._collection.count()} vectors")
    return vector_store


def ingest():
    print("🚀 Starting RAG ingestion pipeline...\n")

    documents = load_pdfs(SCHEMES_DIR)
    chunks = chunk_documents(documents)
    vector_store = create_vector_store(chunks)

    print("\n🎉 Ingestion complete! Knowledge base is ready.")
    print(f"   ChromaDB saved at: {CHROMA_DIR}")
    print("   Now run retriever.py to test queries.")