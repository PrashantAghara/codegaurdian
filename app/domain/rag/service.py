from astrapy import DataAPIClient
from langchain_huggingface import HuggingFaceEmbeddings

from app.core.config import settings

_embeddings = None
_collection = None


def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
    return _embeddings


def get_collection(name: str = "codeguardian_style_corpus"):
    global _collection
    if _collection is None:
        client = DataAPIClient(settings.astra_db_application_token)
        db = client.get_database(settings.astra_db_api_endpoint)
        _collection = db.get_collection(name)
    return _collection


def retrieve_style_context(diff_text: str, top_k: int = 5) -> str:
    embeddings = get_embeddings()
    collection = get_collection()
    query_vector = embeddings.embed_query(diff_text)
    results = collection.find(sort={"$vector": query_vector}, limit=top_k)
    return "\n\n".join(f"[{r['type']} — {r['source']}]\n{r['text']}" for r in results)
