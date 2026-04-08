import json
import logging
from openai import OpenAI
from src.config import IONOS_API_TOKEN, MODEL_NAME
from src.utils import (
    list_datacenters, list_all_servers, list_servers,
    create_server, create_server_from_template, get_datacenter_id_by_name,
    start_server, stop_server, delete_server, find_server_across_datacenters,
    SERVER_TEMPLATES,
)
from src.storage import list_knowledge_docs
from src.rag import retrieve_context

logger = logging.getLogger(__name__)

client = OpenAI(api_key=IONOS_API_TOKEN, base_url="https://openai.inference.de-txl.ionos.com/v1")

BASE_SYSTEM_PROMPT = """You are Ashley, an intelligent AI assistant for IONOS Cloud built by Isayah Young-Burke.
You help users manage cloud infrastructure, answer technical questions, and take real actions on their IONOS account.
You have tools to list datacenters, list/start/stop/delete servers, create servers from scratch or from templates, and search the knowledge base.
When a user asks you to perform a cloud action, use the appropriate tool rather than just describing it.
Be concise, professional, and helpful. Format infrastructure data clearly in markdown."""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_datacenters",
            "description": "List all IONOS Cloud datacenters on the user's account",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_servers",
            "description": "List servers in a specific datacenter, or all servers if no datacenter specified",
            "parameters": {
                "type": "object",
                "properties": {
                    "datacenter_name": {
                        "type": "string",
                        "description": "Name of the datacenter. If omitted, lists servers across all datacenters.",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "start_server",
            "description": "Start a stopped server by name",
            "parameters": {
                "type": "object",
                "properties": {
                    "server_name": {"type": "string", "description": "Name of the server to start"},
                    "datacenter_name": {"type": "string", "description": "Datacenter name (optional — searched automatically if omitted)"},
                },
                "required": ["server_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "stop_server",
            "description": "Stop a running server by name",
            "parameters": {
                "type": "object",
                "properties": {
                    "server_name": {"type": "string", "description": "Name of the server to stop"},
                    "datacenter_name": {"type": "string", "description": "Datacenter name (optional)"},
                },
                "required": ["server_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_server",
            "description": "Permanently delete a server by name. This is irreversible.",
            "parameters": {
                "type": "object",
                "properties": {
                    "server_name": {"type": "string", "description": "Name of the server to delete"},
                    "datacenter_name": {"type": "string", "description": "Datacenter name (optional)"},
                },
                "required": ["server_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_server",
            "description": "Create a new server with custom specs in a specified datacenter",
            "parameters": {
                "type": "object",
                "properties": {
                    "datacenter_name": {"type": "string", "description": "Name of the datacenter"},
                    "server_name": {"type": "string", "description": "Name for the new server"},
                    "cores": {"type": "integer", "description": "Number of CPU cores (default: 2)"},
                    "ram_gb": {"type": "integer", "description": "RAM in GB (default: 4)"},
                },
                "required": ["datacenter_name", "server_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_server_from_template",
            "description": (
                f"Create a server using a preset template. "
                f"Available templates: {', '.join(SERVER_TEMPLATES.keys())}. "
                f"Each template has preset CPU/RAM for the workload type."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "datacenter_name": {"type": "string", "description": "Name of the datacenter"},
                    "template_name": {
                        "type": "string",
                        "enum": list(SERVER_TEMPLATES.keys()),
                        "description": "Template to use",
                    },
                    "custom_name": {"type": "string", "description": "Custom server name (optional)"},
                },
                "required": ["datacenter_name", "template_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_knowledge_docs",
            "description": "List documents stored in Ashley's knowledge base",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]


def _resolve_server(server_name, datacenter_name=None):
    """Return (dc_id, server_id) for a given server name."""
    if datacenter_name:
        dc_id = get_datacenter_id_by_name(datacenter_name)
        if not dc_id:
            return None, f"Datacenter '{datacenter_name}' not found."
        from src.utils import _get_server_id_by_name
        server_id = _get_server_id_by_name(dc_id, server_name)
        if not server_id:
            return None, f"Server '{server_name}' not found in '{datacenter_name}'."
        return (dc_id, server_id), None
    dc_id, server_id = find_server_across_datacenters(server_name)
    if not dc_id:
        return None, f"Server '{server_name}' not found in any datacenter."
    return (dc_id, server_id), None


def _dispatch_tool(name, args):
    if name == "list_datacenters":
        return list_datacenters()

    if name == "list_servers":
        dc_name = args.get("datacenter_name")
        if dc_name:
            dc_id = get_datacenter_id_by_name(dc_name)
            if not dc_id:
                return f"Datacenter '{dc_name}' not found."
            return list_servers(dc_id)
        return list_all_servers()

    if name == "start_server":
        ids, err = _resolve_server(args["server_name"], args.get("datacenter_name"))
        if err:
            return err
        return start_server(ids[0], ids[1])

    if name == "stop_server":
        ids, err = _resolve_server(args["server_name"], args.get("datacenter_name"))
        if err:
            return err
        return stop_server(ids[0], ids[1])

    if name == "delete_server":
        ids, err = _resolve_server(args["server_name"], args.get("datacenter_name"))
        if err:
            return err
        return delete_server(ids[0], ids[1])

    if name == "create_server":
        dc_id = get_datacenter_id_by_name(args["datacenter_name"])
        if not dc_id:
            return f"Datacenter '{args['datacenter_name']}' not found."
        return create_server(
            dc_id,
            name=args.get("server_name", "ashley-server"),
            cores=args.get("cores", 2),
            ram_mb=args.get("ram_gb", 4) * 1024,
        )

    if name == "create_server_from_template":
        dc_id = get_datacenter_id_by_name(args["datacenter_name"])
        if not dc_id:
            return f"Datacenter '{args['datacenter_name']}' not found."
        return create_server_from_template(
            dc_id,
            template_name=args["template_name"],
            custom_name=args.get("custom_name"),
        )

    if name == "list_knowledge_docs":
        return list_knowledge_docs()

    return f"Unknown tool: {name}"


def _build_messages(prompt, conversation_history=None):
    """Build the message list, injecting RAG context if relevant docs exist."""
    rag_context = retrieve_context(prompt)
    system_prompt = BASE_SYSTEM_PROMPT
    if rag_context:
        system_prompt += f"\n\n{rag_context}"

    messages = [{"role": "system", "content": system_prompt}]
    if conversation_history:
        messages.extend(conversation_history)
    messages.append({"role": "user", "content": prompt})
    return messages


def _run_tool_loop(messages):
    """Run the tool-calling loop until no more tool calls are needed. Returns final message."""
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
        max_tokens=1024,
    )
    message = response.choices[0].message

    while message.tool_calls:
        tool_results = []
        for tc in message.tool_calls:
            args = json.loads(tc.function.arguments) if tc.function.arguments else {}
            result = _dispatch_tool(tc.function.name, args)
            tool_results.append({"tool_call_id": tc.id, "role": "tool", "content": result})

        messages.append(message)
        messages.extend(tool_results)

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=1024,
        )
        message = response.choices[0].message

    return messages, message


def query_ionos(prompt, conversation_history=None):
    try:
        messages = _build_messages(prompt, conversation_history)
        messages, final_message = _run_tool_loop(messages)
        return final_message.content or "I couldn't generate a response. Please try again."
    except Exception as e:
        logger.error(f"LLM query error: {e}")
        return f"Error communicating with AI Model Hub: {str(e)}"


def stream_query_ionos(prompt, conversation_history=None):
    """Resolve tool calls first, then stream the final answer."""
    try:
        messages = _build_messages(prompt, conversation_history)
        messages, final_message = _run_tool_loop(messages)

        if not final_message.tool_calls:
            messages.append({"role": "assistant", "content": final_message.content})
            stream = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                stream=True,
                max_tokens=1024,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        yield f"Error: {str(e)}"
