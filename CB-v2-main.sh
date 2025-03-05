CB-v2-main

cd ~/Desktop/CB-v2-main
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install streamlit-drawable-canvas
pip install streamlit streamlit-navigation-bar openai streamlit requests pandas langchain-openai python-dotenv
streamlit run src/app.py


cd ~/Desktop/CB-v2-main
python3 -m venv venv
source venv/bin/activate
streamlit run src/app.py