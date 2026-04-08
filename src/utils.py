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


def _get_server_id_by_name(datacenter_id, server_name):
    resp = requests.get(
        f"{CLOUD_API_BASE}/datacenters/{datacenter_id}/servers",
        auth=_auth(), headers=_headers()
    )
    if resp.status_code != 200:
        return None
    for s in resp.json().get("items", []):
        if s.get("properties", {}).get("name", "").lower() == server_name.lower():
            return s["id"]
    return None


def start_server(datacenter_id, server_id):
    resp = requests.post(
        f"{CLOUD_API_BASE}/datacenters/{datacenter_id}/servers/{server_id}/start",
        auth=_auth(), headers=_headers()
    )
    if resp.status_code in (200, 202):
        return f"Server `{server_id}` is starting."
    return f"Error starting server: {resp.status_code} {resp.text}"


def stop_server(datacenter_id, server_id):
    resp = requests.post(
        f"{CLOUD_API_BASE}/datacenters/{datacenter_id}/servers/{server_id}/stop",
        auth=_auth(), headers=_headers()
    )
    if resp.status_code in (200, 202):
        return f"Server `{server_id}` is stopping."
    return f"Error stopping server: {resp.status_code} {resp.text}"


def delete_server(datacenter_id, server_id):
    resp = requests.delete(
        f"{CLOUD_API_BASE}/datacenters/{datacenter_id}/servers/{server_id}",
        auth=_auth(), headers=_headers()
    )
    if resp.status_code in (200, 202, 204):
        return f"Server `{server_id}` has been deleted."
    return f"Error deleting server: {resp.status_code} {resp.text}"


def find_server_across_datacenters(server_name):
    """Search all datacenters for a server by name. Returns (dc_id, server_id) or (None, None)."""
    resp = requests.get(f"{CLOUD_API_BASE}/datacenters", auth=_auth(), headers=_headers())
    if resp.status_code != 200:
        return None, None
    for dc in resp.json().get("items", []):
        server_id = _get_server_id_by_name(dc["id"], server_name)
        if server_id:
            return dc["id"], server_id
    return None, None


# Server templates: preset configs for common workloads
SERVER_TEMPLATES = {
    "web": {
        "description": "Web server — nginx/Apache ready",
        "cores": 2,
        "ram_gb": 4,
        "name_prefix": "web-server",
    },
    "pentest": {
        "description": "Pen test box — high CPU for tooling",
        "cores": 4,
        "ram_gb": 8,
        "name_prefix": "pentest-box",
    },
    "n8n": {
        "description": "n8n automation server",
        "cores": 2,
        "ram_gb": 4,
        "name_prefix": "n8n-server",
    },
    "db": {
        "description": "Database server — memory optimized",
        "cores": 2,
        "ram_gb": 8,
        "name_prefix": "db-server",
    },
    "dev": {
        "description": "Dev/sandbox box",
        "cores": 1,
        "ram_gb": 2,
        "name_prefix": "dev-box",
    },
}


def create_server_from_template(datacenter_id, template_name, custom_name=None):
    template = SERVER_TEMPLATES.get(template_name.lower())
    if not template:
        available = ", ".join(SERVER_TEMPLATES.keys())
        return f"Unknown template '{template_name}'. Available: {available}"

    name = custom_name or template["name_prefix"]
    return create_server(
        datacenter_id,
        name=name,
        cores=template["cores"],
        ram_mb=template["ram_gb"] * 1024,
    )
