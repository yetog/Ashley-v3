import json
import logging
from datetime import datetime
from botocore.client import Config
from src.config import S3_ACCESS_KEY, S3_SECRET_KEY, S3_ENDPOINT, S3_BUCKET

logger = logging.getLogger(__name__)


def _get_client():
    import boto3
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
        config=Config(signature_version="s3v4"),
    )


def ensure_bucket():
    """Create the ashley-memory bucket if it doesn't exist."""
    try:
        client = _get_client()
        existing = [b["Name"] for b in client.list_buckets().get("Buckets", [])]
        if S3_BUCKET not in existing:
            client.create_bucket(Bucket=S3_BUCKET)
            logger.info(f"Created bucket: {S3_BUCKET}")
    except Exception as e:
        logger.warning(f"Could not ensure bucket exists: {e}")


def save_conversation(session_id, messages):
    """Persist a conversation to Object Storage."""
    try:
        client = _get_client()
        key = f"conversations/{session_id}.json"
        payload = {
            "session_id": session_id,
            "updated_at": datetime.utcnow().isoformat(),
            "messages": messages,
        }
        client.put_object(
            Bucket=S3_BUCKET,
            Key=key,
            Body=json.dumps(payload),
            ContentType="application/json",
        )
    except Exception as e:
        logger.warning(f"Could not save conversation: {e}")


def load_conversation(session_id):
    """Load a previous conversation from Object Storage."""
    try:
        client = _get_client()
        key = f"conversations/{session_id}.json"
        obj = client.get_object(Bucket=S3_BUCKET, Key=key)
        data = json.loads(obj["Body"].read())
        return data.get("messages", [])
    except Exception:
        return []


def list_conversations():
    """List all saved conversation sessions."""
    try:
        client = _get_client()
        resp = client.list_objects_v2(Bucket=S3_BUCKET, Prefix="conversations/")
        items = resp.get("Contents", [])
        return [
            {
                "key": obj["Key"],
                "session_id": obj["Key"].replace("conversations/", "").replace(".json", ""),
                "last_modified": obj["LastModified"].isoformat(),
                "size_kb": round(obj["Size"] / 1024, 1),
            }
            for obj in items
        ]
    except Exception as e:
        logger.warning(f"Could not list conversations: {e}")
        return []


def upload_knowledge_doc(filename, content_bytes, content_type="text/plain"):
    """Upload a document to the RAG knowledge base and index it for retrieval."""
    try:
        client = _get_client()
        key = f"knowledge/{filename}"
        client.put_object(
            Bucket=S3_BUCKET,
            Key=key,
            Body=content_bytes,
            ContentType=content_type,
        )
        # Index the document for RAG
        try:
            from src.rag import index_document
            text = content_bytes.decode("utf-8", errors="ignore")
            index_result = index_document(filename, text)
            return f"Uploaded `{filename}` to knowledge base. {index_result}"
        except Exception as e:
            return f"Uploaded `{filename}` but indexing failed: {e}"
    except Exception as e:
        return f"Upload failed: {e}"


def list_knowledge_docs():
    """List documents in the knowledge base."""
    try:
        client = _get_client()
        resp = client.list_objects_v2(Bucket=S3_BUCKET, Prefix="knowledge/")
        items = resp.get("Contents", [])
        if not items:
            return "No documents in knowledge base yet."
        lines = ["**Knowledge Base Documents:**"]
        for obj in items:
            name = obj["Key"].replace("knowledge/", "")
            lines.append(f"- {name} ({round(obj['Size']/1024, 1)} KB)")
        return "\n".join(lines)
    except Exception as e:
        return f"Could not list documents: {e}"
