from dotenv import load_dotenv
load_dotenv()

from anthropic import Anthropic
from anthropic.types import Message

client = Anthropic()
model = "claude-sonnet-4-0"


# --- Helper functions ---
def add_user_message(messages, message):
    messages.append({
        "role": "user",
        "content": message.content if isinstance(message, Message) else message,
    })


def add_assistant_message(messages, message):
    messages.append({
        "role": "assistant",
        "content": message.content if isinstance(message, Message) else message,
    })


def chat(messages, system=None, temperature=1.0, stop_sequences=[], tools=None):
    params = {
        "model": model,
        "max_tokens": 4096,
        "messages": messages,
        "temperature": temperature,
        "stop_sequences": stop_sequences,
    }
    if tools:
        params["tools"] = tools
    if system:
        params["system"] = system
    return client.messages.create(**params)


def text_from_message(message):
    return "\n".join(block.text for block in message.content if hasattr(block, "text"))


# --- Web Search Schema ---
# Built-in tool: Claude handles search automatically, no implementation needed
web_search_schema = {
    "type": "web_search_20250305",
    "name": "web_search",
    "max_uses": 5,
}


# === Test 1: General web search ===
print("=" * 60)
print("Test 1: General web search")
print("=" * 60)
messages = []
add_user_message(messages, "What are the latest developments in quantum computing in 2026?")
response = chat(messages, tools=[web_search_schema])

print("\n--- Response blocks ---")
for block in response.content:
    block_type = block.type
    if block_type == "text":
        print(f"[text] {block.text[:200]}...")
    elif block_type == "server_tool_use":
        print(f"[server_tool_use] query: {block.input.get('query', 'N/A')}")
    elif block_type == "web_search_tool_result":
        for result in block.content:
            if result.type == "web_search_result":
                print(f"  [result] {result.title} — {result.url}")

print("\n--- Final text ---")
print(text_from_message(response))


# === Test 2: Domain-restricted search ===
print("\n" + "=" * 60)
print("Test 2: Search restricted to nih.gov")
print("=" * 60)

web_search_nih = {
    "type": "web_search_20250305",
    "name": "web_search",
    "max_uses": 5,
    "allowed_domains": ["nih.gov"],
}

messages = []
add_user_message(messages, "What's the best exercise for gaining leg muscle?")
response = chat(messages, tools=[web_search_nih])

print("\n--- Search results (nih.gov only) ---")
for block in response.content:
    if block.type == "server_tool_use":
        print(f"Query: {block.input.get('query', 'N/A')}")
    elif block.type == "web_search_tool_result":
        for result in block.content:
            if result.type == "web_search_result":
                print(f"  {result.title} — {result.url}")

print("\n--- Final text ---")
print(text_from_message(response))
