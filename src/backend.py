import json
import logging
from openai import OpenAI
from src.config import IONOS_API_TOKEN, MODEL_NAME, ENDPOINT
from src.utils import (
    list_datacenters, list_all_servers, list_servers,
    create_server, get_datacenter_id_by_name
)
from src.storage import list_knowledge_docs

logger = logging.getLogger(__name__)

client = OpenAI(api_key=IONOS_API_TOKEN, base_url="https://openai.inference.de-txl.ionos.com/v1")

SYSTEM_PROMPT = """You are Ashley, an intelligent AI assistant for IONOS Cloud built by Isayah Young-Burke.
You help users manage cloud infrastructure, answer technical questions, and take real actions on their IONOS account.
You have access to tools that let you list datacenters, list servers, and create servers.
When a user asks you to perform a cloud action, use the appropriate tool rather than just describing it.
Be concise, professional, and helpful. When returning infrastructure data, format it clearly in markdown."""

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
                        "description": "Name of the datacenter (optional). If omitted, lists servers in all datacenters.",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_server",
            "description": "Create a new server in a specified datacenter",
            "parameters": {
                "type": "object",
                "properties": {
                    "datacenter_name": {
                        "type": "string",
                        "description": "Name of the datacenter to create the server in",
                    },
                    "server_name": {
                        "type": "string",
                        "description": "Name for the new server",
                    },
                    "cores": {
                        "type": "integer",
                        "description": "Number of CPU cores (default: 2)",
                    },
                    "ram_gb": {
                        "type": "integer",
                        "description": "RAM in GB (default: 4)",
                    },
                },
                "required": ["datacenter_name", "server_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_knowledge_docs",
            "description": "List documents stored in Ashley's knowledge base in Object Storage",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]


def _dispatch_tool(name, args):
    """Execute a tool call and return the result as a string."""
    if name == "list_datacenters":
        return list_datacenters()

    if name == "list_servers":
        dc_name = args.get("datacenter_name")
        if dc_name:
            dc_id = get_datacenter_id_by_name(dc_name)
            if not dc_id:
                return f"Datacenter '{dc_name}' not found. Try asking to list your datacenters."
            return list_servers(dc_id)
        return list_all_servers()

    if name == "create_server":
        dc_name = args.get("datacenter_name")
        dc_id = get_datacenter_id_by_name(dc_name)
        if not dc_id:
            return f"Datacenter '{dc_name}' not found. Try asking to list your datacenters first."
        return create_server(
            dc_id,
            name=args.get("server_name", "ashley-server"),
            cores=args.get("cores", 2),
            ram_mb=args.get("ram_gb", 4) * 1024,
        )

    if name == "list_knowledge_docs":
        return list_knowledge_docs()

    return f"Unknown tool: {name}"


def query_ionos(prompt, conversation_history=None):
    """
    Send a prompt to the IONOS AI Model Hub (Llama 3.3 70B) with tool calling.
    Handles multi-turn conversation history and returns the final response string.
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if conversation_history:
        messages.extend(conversation_history)

    messages.append({"role": "user", "content": prompt})

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=1024,
        )

        message = response.choices[0].message

        # Handle tool calls
        while message.tool_calls:
            tool_results = []
            for tc in message.tool_calls:
                args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                result = _dispatch_tool(tc.function.name, args)
                tool_results.append({
                    "tool_call_id": tc.id,
                    "role": "tool",
                    "content": result,
                })

            # Feed tool results back to the model
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

        return message.content or "I couldn't generate a response. Please try again."

    except Exception as e:
        logger.error(f"LLM query error: {e}")
        return f"Error communicating with AI Model Hub: {str(e)}"


def stream_query_ionos(prompt, conversation_history=None):
    """
    Streaming version of query_ionos. Yields text chunks as they arrive.
    Note: tool calling runs non-streamed first, then streams the final answer.
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if conversation_history:
        messages.extend(conversation_history)

    messages.append({"role": "user", "content": prompt})

    try:
        # First pass: check for tool calls (non-streamed)
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=1024,
        )

        message = response.choices[0].message

        # Resolve any tool calls before streaming
        while message.tool_calls:
            tool_results = []
            for tc in message.tool_calls:
                args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                result = _dispatch_tool(tc.function.name, args)
                tool_results.append({
                    "tool_call_id": tc.id,
                    "role": "tool",
                    "content": result,
                })

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

        # If no more tool calls, stream the final response
        if not message.tool_calls:
            messages.append({"role": "assistant", "content": message.content})
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
