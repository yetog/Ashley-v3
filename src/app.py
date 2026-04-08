import sys
import os
import uuid
import logging
import streamlit as st

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

try:
    from src.backend import stream_query_ionos
    from src.storage import ensure_bucket, save_conversation, load_conversation, list_conversations, upload_knowledge_doc
except ImportError as e:
    logger.error(f"Import error: {e}")
    st.error(f"Critical error: {e}")
    st.stop()


class AshleyAIAssistant:
    def __init__(self):
        self._setup_page_config()
        self._initialize_session_state()
        ensure_bucket()

    def _setup_page_config(self):
        st.set_page_config(
            page_title="Ashley v5 - AI Cloud Assistant",
            page_icon="🚀",
            layout="wide",
            initial_sidebar_state="expanded"
        )

    def _initialize_session_state(self):
        defaults = {
            "messages": [],
            "session_id": str(uuid.uuid4()),
            "conversation_tokens": 0,
        }
        for key, val in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = val

    def render_sidebar(self):
        with st.sidebar:
            with st.expander("👤 Meet Ashley", expanded=False):
                st.markdown("""
**Ashley v5** is your IONOS Cloud AI assistant. She can:
- Answer cloud and infrastructure questions
- List your datacenters and servers
- Create new servers on demand
- Remember your conversations
- Store and retrieve knowledge documents

Built by **Isayah Young-Burke** for IONOS US Cloud.
Powered by **Meta-Llama-3.3-70B** via IONOS AI Model Hub.
                """)

            with st.expander("🚀 Quick Actions", expanded=True):
                st.markdown("Click to run:")
                quick_actions = [
                    "List my datacenters",
                    "Show all my servers",
                    "What cloud services does IONOS offer?",
                    "List my knowledge base documents",
                ]
                for idx, question in enumerate(quick_actions):
                    if st.button(question, key=f"quick_{idx}"):
                        self.process_user_input(question)

            with st.expander("💾 Conversation History", expanded=False):
                st.markdown("**Current session:** `" + st.session_state["session_id"][:8] + "...`")
                if st.button("Save current conversation"):
                    save_conversation(st.session_state["session_id"], st.session_state["messages"])
                    st.success("Saved to Object Storage.")

                st.markdown("---")
                st.markdown("**Past sessions:**")
                sessions = list_conversations()
                if not sessions:
                    st.markdown("_No saved sessions yet._")
                else:
                    for s in sessions[:10]:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"`{s['session_id'][:8]}...` — {s['last_modified'][:10]}")
                        with col2:
                            if st.button("Load", key=f"load_{s['session_id']}"):
                                loaded = load_conversation(s["session_id"])
                                st.session_state["messages"] = loaded
                                st.session_state["session_id"] = s["session_id"]
                                st.rerun()

            with st.expander("📚 Knowledge Base", expanded=False):
                st.markdown("Upload documents for Ashley to reference:")
                uploaded = st.file_uploader("Upload a document", type=["txt", "md", "pdf"])
                if uploaded:
                    result = upload_knowledge_doc(uploaded.name, uploaded.read(), uploaded.type)
                    st.success(result)

            with st.expander("🌐 Resources", expanded=False):
                st.markdown("[LinkedIn](https://www.linkedin.com/in/young-burke/)")
                st.markdown("[IONOS Cloud](https://cloud.ionos.com)")
                st.markdown("[IONOS Docs](https://docs.ionos.com)")
                st.markdown("[API Docs](https://api.ionos.com/docs/inference-openai/v1)")

            with st.expander("📌 Patch Notes", expanded=False):
                st.markdown("## Ashley v5")
                st.markdown("### New in v5")
                st.markdown("* **Llama 3.3 70B** — upgraded from 8B for smarter responses")
                st.markdown("* **Tool Calling** — LLM decides when to call cloud APIs, no more regex")
                st.markdown("* **Streaming responses** — Ashley types in real time")
                st.markdown("* **Object Storage** — conversations saved to IONOS S3")
                st.markdown("* **Knowledge Base** — upload docs for Ashley to reference")
                st.markdown("* **Conversation History** — load previous sessions from sidebar")
                st.markdown("### v4")
                st.markdown("* IONOS Cloud API integration (list DCs, servers, create server)")
                st.markdown("* Secure .env credential management")
                st.markdown("### v3")
                st.markdown("* AshleyAIAssistant class, quick start questions, sidebar")

    def process_user_input(self, user_input):
        if not user_input or not isinstance(user_input, str):
            return

        st.session_state["messages"].append({"role": "user", "content": user_input})

        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            history = st.session_state["messages"][:-1]  # exclude current message
            response_chunks = []

            try:
                placeholder = st.empty()
                full_response = ""
                for chunk in stream_query_ionos(user_input, conversation_history=history):
                    full_response += chunk
                    placeholder.markdown(full_response + "▌")
                placeholder.markdown(full_response)
                response_chunks = full_response
            except Exception as e:
                full_response = f"Error: {str(e)}"
                st.error(full_response)

            st.session_state["messages"].append({"role": "assistant", "content": full_response})
            st.session_state["conversation_tokens"] += len(full_response.split())

            # Auto-save after every exchange
            save_conversation(st.session_state["session_id"], st.session_state["messages"])

    def handle_chat_interaction(self):
        for message in st.session_state["messages"]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if user_input := st.chat_input("Ask Ashley..."):
            self.process_user_input(user_input)

    def run(self):
        st.title("Ashley v5 — Your AI Cloud Assistant")
        self.render_sidebar()
        self.handle_chat_interaction()


def main():
    assistant = AshleyAIAssistant()
    assistant.run()


if __name__ == "__main__":
    main()
