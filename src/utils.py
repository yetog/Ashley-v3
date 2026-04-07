import requests
from src.config import IONOS_CLOUD_USERNAME, IONOS_CLOUD_PASSWORD, CLOUD_API_BASE


def _auth():
    return (IONOS_CLOUD_USERNAME, IONOS_CLOUD_PASSWORD)


def _headers():
    return {"Content-Type": "application/json"}


def list_datacenters():
    resp = requests.get(f"{CLOUD_API_BASE}/datacenters", auth=_auth(), headers=_headers())
    if resp.status_code != 200:
        return f"Error fetching datacenters: {resp.status_code} {resp.text}"

    items = resp.json().get("items", [])
    if not items:
        return "No datacenters found."

    lines = ["**Your Datacenters:**"]
    for dc in items:
        props = dc.get("properties", {})
        lines.append(f"- **{props.get('name', 'Unnamed')}** | Location: {props.get('location')} | ID: `{dc['id']}`")
    return "\n".join(lines)


def list_servers(datacenter_id):
    resp = requests.get(
        f"{CLOUD_API_BASE}/datacenters/{datacenter_id}/servers",
        auth=_auth(), headers=_headers()
    )
    if resp.status_code != 200:
        return f"Error fetching servers: {resp.status_code} {resp.text}"

    items = resp.json().get("items", [])
    if not items:
        return f"No servers found in datacenter `{datacenter_id}`."

    lines = [f"**Servers in datacenter `{datacenter_id}`:**"]
    for s in items:
        props = s.get("properties", {})
        lines.append(
            f"- **{props.get('name', 'Unnamed')}** | "
            f"Cores: {props.get('cores')} | RAM: {props.get('ram')}MB | "
            f"State: {props.get('vmState', 'unknown')} | ID: `{s['id']}`"
        )
    return "\n".join(lines)


def list_all_servers():
    resp = requests.get(f"{CLOUD_API_BASE}/datacenters", auth=_auth(), headers=_headers())
    if resp.status_code != 200:
        return f"Error fetching datacenters: {resp.status_code} {resp.text}"

    datacenters = resp.json().get("items", [])
    if not datacenters:
        return "No datacenters found."

    all_lines = []
    for dc in datacenters:
        dc_name = dc.get("properties", {}).get("name", "Unnamed")
        result = list_servers(dc["id"])
        all_lines.append(f"### {dc_name}")
        all_lines.append(result)

    return "\n\n".join(all_lines)


def create_server(datacenter_id, name, cores=2, ram_mb=4096, cpu_family="INTEL_ICELAKE"):
    body = {
        "properties": {
            "name": name,
            "cores": cores,
            "ram": ram_mb,
            "cpuFamily": cpu_family
        }
    }
    resp = requests.post(
        f"{CLOUD_API_BASE}/datacenters/{datacenter_id}/servers",
        auth=_auth(), headers=_headers(), json=body
    )
    if resp.status_code in (200, 202):
        props = resp.json().get("properties", {})
        server_id = resp.json().get("id")
        return (
            f"Server **{props.get('name')}** is being created!\n"
            f"- ID: `{server_id}`\n"
            f"- Cores: {props.get('cores')} | RAM: {props.get('ram')}MB\n"
            f"- Datacenter: `{datacenter_id}`"
        )
    return f"Error creating server: {resp.status_code} {resp.text}"


def get_datacenter_id_by_name(name):
    resp = requests.get(f"{CLOUD_API_BASE}/datacenters", auth=_auth(), headers=_headers())
    if resp.status_code != 200:
        return None
    for dc in resp.json().get("items", []):
        if dc.get("properties", {}).get("name", "").lower() == name.lower():
            return dc["id"]
    return None
