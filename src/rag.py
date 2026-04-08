"""
RAG (Retrieval Augmented Generation) for Ashley.

Flow:
  upload doc → chunk → embed via IONOS AI Model Hub → store index in S3
  query      → embed query → cosine similarity → top-k chunks → inject as context
"""

import json
import math
import logging
from openai import OpenAI
from src.config import IONOS_API_TOKEN, EMBEDDING_MODEL, S3_BUCKET
from src.storage import _get_client

logger = logging.getLogger(__name__)

_embed_client = OpenAI(
    api_key=IONOS_API_TOKEN,
    base_url="https://openai.inference.de-txl.ionos.com/v1"
)

INDEX_KEY = "knowledge/embeddings_index.json"
CHUNK_SIZE = 400       # words per chunk
CHUNK_OVERLAP = 50     # words of overlap between chunks
TOP_K = 3              # chunks to inject per query


def _chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + size, len(words))
        chunks.append(" ".join(words[start:end]))
        start += size - overlap
    return chunks


def _embed(texts):
    """Embed a list of strings. Returns list of float vectors."""
    resp = _embed_client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in resp.data]


def _cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def _load_index():
    try:
        client = _get_client()
        obj = client.get_object(Bucket=S3_BUCKET, Key=INDEX_KEY)
        return json.loads(obj["Body"].read())
    except Exception:
        return []


def _save_index(index):
    try:
        client = _get_client()
        client.put_object(
            Bucket=S3_BUCKET,
            Key=INDEX_KEY,
            Body=json.dumps(index),
            ContentType="application/json",
        )
    except Exception as e:
        logger.warning(f"Could not save RAG index: {e}")


def index_document(filename, text):
    """
    Chunk a document, embed each chunk, and append to the S3 index.
    Call this after a file is uploaded to the knowledge base.
    """
    try:
        chunks = _chunk_text(text)
        if not chunks:
            return "Document appears to be empty."

        embeddings = _embed(chunks)
        index = _load_index()

        # Remove any existing entries for this file
        index = [entry for entry in index if entry.get("source") != filename]

        for chunk, embedding in zip(chunks, embeddings):
            index.append({
                "source": filename,
                "text": chunk,
                "embedding": embedding,
            })

        _save_index(index)
        return f"Indexed `{filename}` — {len(chunks)} chunks embedded and stored."
    except Exception as e:
        logger.error(f"Indexing error: {e}")
        return f"Could not index document: {e}"


def retrieve_context(query, top_k=TOP_K):
    """
    Embed a query and return the top-k most relevant chunks from the index.
    Returns a formatted string ready to inject into a system prompt.
    """
    try:
        index = _load_index()
        if not index:
            return None

        query_embedding = _embed([query])[0]

        scored = [
            (entry, _cosine_similarity(query_embedding, entry["embedding"]))
            for entry in index
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        top = scored[:top_k]

        # Only include chunks above a relevance threshold
        relevant = [(entry, score) for entry, score in top if score > 0.4]
        if not relevant:
            return None

        lines = ["**Relevant context from knowledge base:**"]
        for entry, score in relevant:
            lines.append(f"\n[Source: {entry['source']} | relevance: {score:.2f}]")
            lines.append(entry["text"])

        return "\n".join(lines)
    except Exception as e:
        logger.warning(f"RAG retrieval error: {e}")
        return None
