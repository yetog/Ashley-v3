# Ashley - AI Cloud Assistant v6

> An intelligent AI assistant for IONOS Cloud — built to chat, consult, and control your infrastructure.

---

## What's New in v6

Ashley v6 completes the core cloud control loop. She can now manage the full server lifecycle, spin up workloads from templates, and answer questions grounded in your own uploaded documents via RAG.

### v6 Highlights
- **RAG (Retrieval Augmented Generation)** — upload docs to the knowledge base, Ashley embeds them via `BAAI/bge-large-en-v1.5` and injects relevant context into every query
- **Full server lifecycle** — start, stop, and delete servers from chat by name
- **Server templates** — one-line provisioning for web, pentest, n8n, db, and dev workloads
- **Embedding model** — `BAAI/bge-large-en-v1.5` via IONOS AI Model Hub for semantic search

---

## What Ashley Can Do

### Chat (Llama 3.3 70B via IONOS AI Model Hub)
- Cloud consulting and architecture questions
- IONOS product guidance and troubleshooting
- Answers grounded in your uploaded knowledge base documents

### Cloud Actions (Live IONOS Cloud API)
| Say something like... | What happens |
|---|---|
| "list my datacenters" | Fetches all your DCs with location and ID |
| "show all my servers" | Lists servers across all datacenters |
| "list servers in App Testing" | Lists servers in a specific datacenter |
| "start web-server-01" | Starts a stopped server |
| "stop pentest-box" | Stops a running server |
| "delete dev-box" | Permanently deletes a server |
| "create a server named api-01 in App Testing" | Provisions a custom server |
| "spin up a pentest template in Pen Testing" | Creates a server from a preset template |
| "spin up an n8n template in N8N" | Creates an n8n automation server |
| "list my knowledge base documents" | Shows uploaded RAG documents |

### Server Templates
| Template | Cores | RAM | Use case |
|---|---|---|---|
| `web` | 2 | 4 GB | nginx / Apache web server |
| `pentest` | 4 | 8 GB | Pen testing / security tooling |
| `n8n` | 2 | 4 GB | n8n workflow automation |
| `db` | 2 | 8 GB | Database server |
| `dev` | 1 | 2 GB | Dev / sandbox box |

---

## Project Structure

```
Ashley-v3/
├── src/
│   ├── app.py          # Streamlit UI, sidebar, streaming chat
│   ├── backend.py      # LLM tool calling, RAG injection, query routing
│   ├── config.py       # Loads all credentials from .env
│   ├── utils.py        # IONOS Cloud API (servers, datacenters, templates)
│   ├── storage.py      # IONOS Object Storage (S3) — sessions, knowledge base
│   ├── rag.py          # RAG pipeline: chunk → embed → index → retrieve
│   └── templates/      # UI components
├── .env                # Your secrets (never committed)
├── .env.example        # Template for setting up credentials
├── .gitignore          # Excludes .env, pycache, venv
└── README.md
```

---

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/yetog/Ashley-v3.git
cd Ashley-v3
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install streamlit openai boto3 requests python-dotenv
```

### 4. Configure credentials
```bash
cp .env.example .env
```

Edit `.env` with your values:
```env
# IONOS AI Model Hub (inference)
IONOS_API_TOKEN=your_inference_api_token

# IONOS Cloud API (server management)
IONOS_CLOUD_USERNAME=your@email.com
IONOS_CLOUD_PASSWORD=yourpassword

# IONOS Object Storage (S3-compatible)
S3_ACCESS_KEY=your_s3_access_key
S3_SECRET_KEY=your_s3_secret_key
S3_ENDPOINT=https://s3.eu-central-2.ionoscloud.com
S3_BUCKET=ashley-memory

# Model config
MODEL_NAME=meta-llama/Llama-3.3-70B-Instruct
EMBEDDING_MODEL=BAAI/bge-large-en-v1.5
ENDPOINT=https://openai.inference.de-txl.ionos.com/v1/chat/completions
```

> **Never commit `.env` to git.** It is already listed in `.gitignore`.

### 5. Run Ashley
```bash
python -m streamlit run src/app.py
```

Ashley will be available at `http://localhost:8501`

---

## Technologies

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| LLM | `meta-llama/Llama-3.3-70B-Instruct` via IONOS AI Model Hub |
| Embeddings | `BAAI/bge-large-en-v1.5` via IONOS AI Model Hub |
| Cloud API | IONOS Cloud REST API v6 |
| Object Storage | IONOS S3-compatible Object Storage (boto3) |
| Config | python-dotenv |
| Language | Python 3.11+ |

---

## Available Models on IONOS AI Model Hub

| Model | Use |
|---|---|
| `meta-llama/Llama-3.3-70B-Instruct` | Ashley's main LLM (default) |
| `meta-llama/Meta-Llama-3.1-8B-Instruct` | Lightweight alternative |
| `meta-llama/Meta-Llama-3.1-405B-Instruct-FP8` | Highest capability |
| `BAAI/bge-large-en-v1.5` | English embeddings (RAG) |
| `BAAI/bge-m3` | Multilingual embeddings |
| `black-forest-labs/FLUX.1-schnell` | Image generation |

---

## Known Issues

- **Model ID must be exact** — use `meta-llama/Llama-3.3-70B-Instruct`, not `Meta-Llama-3.3-70B-Instruct`
- **boto3 version** — if S3 calls fail, pin `boto3==1.35.99` or set env vars:
  ```bash
  AWS_REQUEST_CHECKSUM_CALCULATION=when_required
  AWS_RESPONSE_CHECKSUM_VALIDATION=when_required
  ```

---

## Roadmap

- [ ] **Image generation** — FLUX.1-schnell integration for architecture diagrams
- [ ] **IP & network management** — reserve IPs, configure NICs from chat
- [ ] **Deployment automation** — run scripts on newly created servers via SSH
- [ ] **Cost estimation** — show pricing before provisioning
- [ ] **Multi-language support** — swap to `BAAI/bge-m3` for multilingual knowledge base

---

## Security

- API credentials are stored in `.env` and never committed to version control
- `.gitignore` excludes `.env`, `__pycache__`, and virtual environments
- If you previously had tokens hardcoded in `config.py`, rotate them in your IONOS DCD portal under **Profile > API Keys**

---

## License

Built by Isayah Young-Burke for IONOS US Cloud.
Powered by IONOS AI Model Hub and DCD.
