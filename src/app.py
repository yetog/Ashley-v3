import sys
import os
import streamlit as st
from dotenv import load_dotenv
import logging

# Enhanced error handling and logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables (for security)
load_dotenv()

# More robust module import with error handling
try:
    # Dynamic path resolution
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    sys.path.insert(0, project_root)
    
    from src.backend import query_ionos
except ImportError as e:
    logger.error(f"Module Import Error: {e}")
    st.error(f"❌ Critical Error: Backend module not found. Please check your project structure.")
    
    # Fallback query function if import fails
    def query_ionos(input_text):
        return f"Error: Unable to process query - {input_text}"

class AshleyAIAssistant:
    def __init__(self):
        """
        Initialize the Streamlit application with enhanced configuration
        and session state management.
        """
        
        self._setup_page_config()
        self._initialize_session_state()
        self.quick_start_questions = [
            "What cloud services does IONOS offer?",
            "Can you help me set up a bidriectional firewall?",
            "What are the benefits of cloud computing?"
        ]
        
    def _setup_page_config(self):
        """Configure Streamlit page settings for better user experience."""
        st.set_page_config(
            page_title="Ashley - AI Cloud Assistant",
            page_icon="🚀",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
    def _initialize_session_state(self):
        """Initialize and manage session state variables."""
        session_defaults = {
            "messages": [],
            "conversation_tokens": 0,
            "max_tokens": 4000,
            "theme": "light",
            "last_quick_start_question": None
        }
        
        for key, default_value in session_defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
        
    def render_sidebar(self):
        """Create a comprehensive and interactive sidebar."""
        with st.sidebar:
            # Enhanced About Section
            with st.expander("👤 Meet Ashley", expanded=False):
                st.markdown("""
                **Ashley** is an intelligent AI assistant specialized in:
                - Cloud Consulting
                - Technical Problem Solving
                - AI-Powered Insights
                 """)

                st.markdown("""
                Developed by Isayah Young Burke IONOS US Cloud.
                **Ashley AI Chatbot Overview**

                            **Ashley AI Chatbot Overview**

                * **Core Technology:**
                    * LangChain-based chatbot.
                    * Utilizes the Meta-Llama-3.1-8B-Instruct model for intelligent responses.
                * **Frontend:**
                    * Implemented using Streamlit for a user-friendly interface.
                * **Backend Integration:**
                    * Integrates with the IONOS inference API for AI-generated responses.
                * **Functionality:**
                    * Provides intelligent responses to user queries.
                                """)
            
            # Quick Start Questions Section in an Expander
            with st.expander("🚀 Quick Start Questions", expanded=False):
                st.markdown("Click a question to get started:")
                for idx, question in enumerate(self.quick_start_questions):
                    # Create a unique key using index
                    button_key = f"quick_start_button_{idx}"
                    
                    # Check if this button was clicked
                    if st.button(question, key=button_key):
                        # Check if this is a new question to prevent duplicate processing
                        if st.session_state['last_quick_start_question'] != question:
                            st.session_state['last_quick_start_question'] = question
                            # Process the question directly
                            self.process_user_input(question)
            
            # Resources Section with Icons in an Expander
            with st.expander("🌐 Connect & Explore", expanded=False):
                st.markdown("### Explore More Resources")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("[LinkedIn 🔗](https://www.linkedin.com/in/young-burke/)")
                with col2:
                    st.markdown("[IONOS Cloud ☁️](https://cloud.ionos.com/compute/cloud-cubes)")
                
                # Additional resources
                st.markdown("### Additional Links")
                st.markdown("- [IONOS Documentation](https://docs.ionos.com)")
                st.markdown("- [API Documentation](http://api.ionos.com/docs/inference-openai/v1)")

            with st.expander("📌 Patch Notes", expanded=False):

                st.markdown("## 📌 Patch Notes v3 - Ashley AI Cloud Assistant")

                st.markdown("### 🔹 **Major Enhancements**")
                st.markdown("* **Refactored Architecture:** Introduced `AshleyAIAssistant` class for better modularity and scalability.")
                st.markdown("* **Robust Error Handling:** Added structured logging and dynamic error fallback for API failures.")

                st.markdown("### 🔹 **New Features**")
                st.markdown("* **🚀 Quick Start Questions:** Users can now click preset cloud-related questions for instant responses.")
                st.markdown("* **📌 Sidebar Improvements:** New expandable sections for AI overview, resources, and quick start interactions.")
                st.markdown("* **🌐 Resource Hub:** Direct access to IONOS Cloud, API documentation, and LinkedIn.")

                st.markdown("### 🔹 **Performance & UX Improvements**")
                st.markdown("* **Enhanced Session Management:** Tracks conversation history, token usage, and prevents redundant queries.")
                st.markdown("* **Smarter Input Handling:** Validates queries to ensure a smooth chat experience.")
                st.markdown("* **Improved Query Execution:** Optimized backend calls with error recovery mechanisms.")

                st.markdown("### 💡 **Upcoming Enhancements:**")
                st.markdown("* **Real-time AI Memory Optimization**")
                st.markdown("* **Interactive Charts & Visualizations**")
                st.markdown("* **Advanced Cloud Cost Estimator**")

                st.markdown("🚀 **Ashley is now more responsive, structured, and intuitive than ever!**")


    def process_user_input(self, user_input):
        """
        Process user input (either from chat input or quick start buttons)
        with enhanced error handling
        """
        # Validate input
        if not user_input or not isinstance(user_input, str):
            st.error("Invalid input. Please provide a valid query.")
            return
        
        # Save user input to chat history
        st.session_state["messages"].append({"role": "user", "content": user_input})
        
        with st.chat_message("user"):
            st.markdown(user_input)
        
        with st.chat_message("assistant"):
            try:
                # Call backend with enhanced error management
                with st.spinner("Ashley is thinking..."):
                    response = query_ionos(user_input)
                
                # Additional validation of response
                if not response:
                    response = "I couldn't generate a meaningful response. Please try again."
                
                st.markdown(response)
                
                # Update conversation state
                st.session_state["messages"].append({
                    "role": "assistant", 
                    "content": response
                })
                
                # Token tracking (placeholder - adjust based on actual token counting)
                st.session_state["conversation_tokens"] += len(response.split())
            
            except Exception as e:
                logger.error(f"Query Error: {e}")
                error_message = f"❌ Error processing your request: {str(e)}"
                st.error(error_message)
                st.session_state["messages"].append({
                    "role": "assistant", 
                    "content": error_message
                })
    
    def handle_chat_interaction(self):
        """
        Manage chat interactions with enhanced error handling
        and conversation tracking.
        """
        # Display existing chat history
        for message in st.session_state["messages"]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Handle new user input
        if user_input := st.chat_input("Ask Ashley anything about cloud consulting..."):
            self.process_user_input(user_input)
    
    def run(self):
        """Main method to run the Streamlit application."""
        # Render the title
        st.title("Your AI Cloud Assistant")
        
        # Render sidebar
        self.render_sidebar()
        
        # Handle chat interaction
        self.handle_chat_interaction()

def main():
    """Entry point for the Streamlit application."""
    assistant = AshleyAIAssistant()
    assistant.run()

if __name__ == "__main__":
    main()
