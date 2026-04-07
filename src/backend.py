import re
import requests
from src.config import IONOS_API_TOKEN, MODEL_NAME, ENDPOINT
from src.utils import list_datacenters, list_all_servers, list_servers, create_server, get_datacenter_id_by_name

CLOUD_INTENTS = {
    "list_datacenters": [
        r"list\s+data\s*centers?", r"show\s+data\s*centers?", r"what\s+data\s*centers?",
        r"my\s+data\s*centers?", r"datacenters?"
    ],
    "list_servers": [
        r"list\s+servers?", r"show\s+servers?", r"what\s+servers?",
        r"my\s+servers?", r"all\s+servers?"
    ],
    "create_server": [
        r"create\s+(?:a\s+)?server", r"spin\s+up\s+(?:a\s+)?server",
        r"new\s+server", r"launch\s+(?:a\s+)?server", r"deploy\s+(?:a\s+)?server"
    ],
}


def detect_intent(text):
    lower = text.lower()
    for intent, patterns in CLOUD_INTENTS.items():
        for pattern in patterns:
            if re.search(pattern, lower):
                return intent
    return None


def handle_cloud_intent(intent, user_input):
    if intent == "list_datacenters":
        return list_datacenters()

    if intent == "list_servers":
        # Check if user mentioned a specific datacenter name
        dc_match = re.search(r"in\s+['\"]?([a-zA-Z0-9 _-]+)['\"]?", user_input, re.IGNORECASE)
        if dc_match:
            dc_name = dc_match.group(1).strip()
            dc_id = get_datacenter_id_by_name(dc_name)
            if dc_id:
                return list_servers(dc_id)
            return f"Couldn't find a datacenter named '{dc_name}'. Try asking me to list your datacenters first."
        return list_all_servers()

    if intent == "create_server":
        # Parse name
        name_match = re.search(r"(?:named?|called)\s+['\"]?([a-zA-Z0-9_-]+)['\"]?", user_input, re.IGNORECASE)
        name = name_match.group(1) if name_match else "ashley-server"

        # Parse datacenter
        dc_match = re.search(r"in\s+['\"]?([a-zA-Z0-9 _-]+)['\"]?", user_input, re.IGNORECASE)
        dc_id = None
        if dc_match:
            dc_name = dc_match.group(1).strip()
            dc_id = get_datacenter_id_by_name(dc_name)

        if not dc_id:
            return (
                "Which datacenter should I create the server in? "
                "Ask me to **list your datacenters** to see your options."
            )

        # Parse cores and RAM
        cores_match = re.search(r"(\d+)\s*cores?", user_input, re.IGNORECASE)
        ram_match = re.search(r"(\d+)\s*(?:gb|gib)", user_input, re.IGNORECASE)
        cores = int(cores_match.group(1)) if cores_match else 2
        ram_mb = int(ram_match.group(1)) * 1024 if ram_match else 4096

        return create_server(dc_id, name, cores=cores, ram_mb=ram_mb)

    return None


def query_ionos(prompt):
    intent = detect_intent(prompt)
    if intent:
        return handle_cloud_intent(intent, prompt)

    headers = {
        "Authorization": f"Bearer {IONOS_API_TOKEN}",
        "Content-Type": "application/json"
    }
    body = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are Ashley, an intelligent AI assistant for IONOS Cloud. "
                    "You help users with cloud infrastructure, server management, networking, and technical questions. "
                    "You can also help users spin up servers, list datacenters, and manage their IONOS cloud resources. "
                    "Be concise, helpful, and professional."
                )
            },
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 512
    }

    response = requests.post(ENDPOINT, json=body, headers=headers)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    return f"Error {response.status_code}: {response.text}"
