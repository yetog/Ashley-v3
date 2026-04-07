# Ashley - AI Cloud Assistant v4

> An intelligent AI assistant for IONOS Cloud — built to chat, consult, and control your infrastructure.

---

## What's New in v4

Ashley v4 is a major upgrade from a conversational chatbot to a **cloud-capable AI assistant**. She can now talk to your IONOS infrastructure directly — listing servers, datacenters, and spinning up new machines — all from a natural language chat interface.

### v4 Highlights
- **IONOS Cloud API integration** — Ashley can manage real infrastructure, not just answer questions about it
- **Intent detection** — cloud commands are routed directly to the API without wasting LLM tokens
- **Secure credential management** — secrets moved from hardcoded config to `.env` (never committed to git)
- **IONOS-aware system prompt** — LLM responses are now grounded in cloud context

---

## What Ashley Can Do

### Chat (Powered by Meta-Llama-3.1-8B via IONOS Inference)
- Cloud consulting and architecture questions
- IONOS product guidance
- Technical troubleshooting

### Cloud Actions (Live IONOS Cloud API)
| Say something like... | What happens |
|---|---|
| "list my datacenters" | Fetches all your DCs with location and ID |
| "show my servers" | Lists servers across all datacenters |
| "list servers in App Testing" | Lists servers in a specific datacenter |
| "create a server named web-01 in App Testing" | Spins up a new server via the Cloud API |
| "create a 4 core 8GB server named dev-box in Pen Testing" | Creates server with custom specs |

---

## Project Structure

```
Ashley-v3/
├── src/
│   ├── app.py          # Streamlit UI and chat interface
│   ├── backend.py      # Intent detection + LLM query handler
│   ├── config.py       # Loads credentials from .env
│   ├── utils.py        # IONOS Cloud API functions
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
pip install -r requirements.txt
```

### 4. Configure credentials
```bash
cp .env.example .env
```

Edit `.env` with your values:
```env
IONOS_API_TOKEN=your_inference_api_token
IONOS_CLOUD_USERNAME=your@email.com
IONOS_CLOUD_PASSWORD=yourpassword
MODEL_NAME=meta-llama/Meta-Llama-3.1-8B-Instruct
ENDPOINT=https://openai.inference.de-txl.ionos.com/v1/chat/completions
```

> **Never commit `.env` to git.** It is already listed in `.gitignore`.

### 5. Run Ashley
```bash
streamlit run src/app.py
```

Ashley will be available at `http://localhost:8501`

---

## Technologies

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| LLM | Meta-Llama-3.1-8B-Instruct via IONOS Inference API |
| Cloud API | IONOS Cloud REST API v6 |
| Config | python-dotenv |
| Language | Python 3.11+ |

---

## Roadmap

- [ ] **Conversation memory** — multi-turn context so Ashley remembers earlier messages
- [ ] **Server templates** — pre-built configs for common use cases (web server, pen test box, n8n)
- [ ] **Start / stop / delete servers** from chat
- [ ] **Cost estimation** — show pricing before creating resources
- [ ] **IP and network management** — reserve IPs, configure NICs from chat
- [ ] **Deployment automation** — push code or run scripts on newly created servers

---

## Security

- API credentials are stored in `.env` and never committed to version control
- `.gitignore` is configured to exclude `.env`, `__pycache__`, and virtual environments
- If you previously had tokens hardcoded in `config.py`, rotate them in your IONOS DCD portal under **Profile > API Keys**

---

## License

Built by Isayah Young-Burke for IONOS US Cloud.  
Powered by IONOS AI Model Hub and DCD.
