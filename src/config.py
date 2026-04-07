import os
from dotenv import load_dotenv

load_dotenv()

IONOS_API_TOKEN = os.getenv("IONOS_API_TOKEN")
IONOS_CLOUD_USERNAME = os.getenv("IONOS_CLOUD_USERNAME")
IONOS_CLOUD_PASSWORD = os.getenv("IONOS_CLOUD_PASSWORD")
MODEL_NAME = os.getenv("MODEL_NAME", "meta-llama/Meta-Llama-3.1-8B-Instruct")
ENDPOINT = os.getenv("ENDPOINT", "https://openai.inference.de-txl.ionos.com/v1/chat/completions")
CLOUD_API_BASE = "https://api.ionos.com/cloudapi/v6"
