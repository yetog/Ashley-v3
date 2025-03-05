# IONOS AI Chatbot Project v2

## Overview
The **IONOS AI Chatbot** is a LangChain-based chatbot that leverages the **IONOS Meta-Llama-3.1-8B-Instruct** model to provide intelligent responses to user queries. The chatbot is implemented using **Streamlit** for the frontend and integrates with the IONOS inference API for AI-generated responses.

## Features
- Interactive chat interface using **Streamlit**
- Stateless response handling
- Uses **LangChain** for structured LLM interaction
- Supports **IONOS AI inference API** integration
- Secure API token management

## Technologies Used
- **Python 3.13**
- **Streamlit** (UI Framework)
- **LangChain** (LLM Integration)
- **IONOS Inference API**
- **Thunder Client** (API Testing)

## Project Structure
```
IONOS-Chat-bot-project/
│── src/
│   ├── app.py            # Main Streamlit UI
│   ├── backend.py        # Query handler for IONOS API
│   ├── config.py         # Stores API tokens and model settings
│   ├── templates/        # UI templates
│   ├── utils.py          # Utility functions
│── venv/                 # Virtual environment
│── requirements.txt      # Project dependencies
│── README.md             # Project documentation
```

## Setup and Installation
### 1️⃣ Clone the Repository
```bash
cd ~/Desktop/
git clone https://github.com/your-repo/IONOS-Chat-bot-project.git
cd IONOS-Chat-bot-project
```

### 2️⃣ Set Up Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3️⃣ Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4️⃣ Configure API Access
Update `config.py` with your IONOS API token:
```python
IONOS_API_TOKEN = "your_token_here"
MODEL_NAME = "meta-llama/Meta-Llama-3.1-8B-Instruct"
ENDPOINT = "https://openai.inference.de-txl.ionos.com/v1/chat/completions"
```

### 5️⃣ Run the Chatbot
```bash
streamlit run src/app.py
```

## API Testing with Thunder Client
To verify API connectivity, use **Thunder Client**:
- **Endpoint**: `https://openai.inference.de-txl.ionos.com/v1/chat/completions`
- **Headers**:
  ```json
  {
    "Authorization": "Bearer your_token_here",
    "Content-Type": "application/json"
  }
  ```
- **Body**:
  ```json
  {
    "model": "meta-llama/Meta-Llama-3.1-8B-Instruct",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 1024
  }
  ```

## Troubleshooting
### 401 Unauthorized Error
- Ensure **API Token** is correct and active in `config.py`
- Check for typos or incorrect header formatting in API requests

### Streamlit Module Not Found
```bash
pip install streamlit
```

### Missing Dependencies
```bash
pip install -r requirements.txt
```

## Future Improvements
- Implement **session-based memory** for better conversational flow
- Enhance UI with **custom Streamlit components**
- Improve error handling and logging

## License
Made using IONOS AI Model Hub and DCD 
