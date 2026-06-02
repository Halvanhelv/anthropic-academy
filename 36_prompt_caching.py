from dotenv import load_dotenv
load_dotenv()

from anthropic import Anthropic

client = Anthropic()
model = "claude-sonnet-4-0"

SYSTEM_PROMPT = """You are a senior software engineer and coding assistant.
You help users write clean, efficient, and well-documented code.
You follow best practices for the language being used.
You provide explanations for your code suggestions.
You can review code for bugs, performance issues, and security vulnerabilities.
When asked about architecture, you consider scalability, maintainability, and testability.
You are familiar with common design patterns and can suggest appropriate ones.
You write unit tests when asked and follow TDD principles.
You can explain complex concepts in simple terms.
You are patient and thorough in your responses.""" * 5

TOOLS = [
    {
        "name": "get_current_datetime",
        "description": "Returns the current date and time in the specified format.",
        "input_schema": {
            "type": "object",
            "properties": {
                "format": {
                    "type": "string",
                    "description": "The format string for the datetime output.",
                    "enum": ["%Y-%m-%d", "%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%B %d, %Y"],
                }
            },
            "required": ["format"],
        },
    },
    {
        "name": "add_duration",
        "description": "Adds a duration to a given datetime string and returns the result.",
        "input_schema": {
            "type": "object",
            "properties": {
                "datetime_str": {"type": "string", "description": "The starting datetime."},
                "days": {"type": "integer", "description": "Number of days to add."},
                "hours": {"type": "integer", "description": "Number of hours to add."},
            },
            "required": ["datetime_str"],
        },
    },
    {
        "name": "set_reminder",
        "description": "Sets a reminder with specified content and timestamp. Returns confirmation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "The reminder text."},
                "timestamp": {"type": "string", "description": "When to trigger the reminder."},
            },
            "required": ["content", "timestamp"],
        },
    },
]


def chat(messages, system=None, tools=None):
    params = {"model": model, "max_tokens": 1024, "messages": messages}

    if system:
        params["system"] = [{
            "type": "text",
            "text": system,
            "cache_control": {"type": "ephemeral"},
        }]

    if tools:
        tools_clone = tools.copy()
        last_tool = tools_clone[-1].copy()
        last_tool["cache_control"] = {"type": "ephemeral"}
        tools_clone[-1] = last_tool
        params["tools"] = tools_clone

    response = client.messages.create(**params)
    return response


def print_usage(response, label):
    u = response.usage
    print(f"\n--- {label} ---")
    print(f"  input_tokens:          {u.input_tokens}")
    print(f"  output_tokens:         {u.output_tokens}")
    print(f"  cache_creation_tokens: {getattr(u, 'cache_creation_input_tokens', 0)}")
    print(f"  cache_read_tokens:     {getattr(u, 'cache_read_input_tokens', 0)}")


# === Test 1: First request — writes to cache ===
print("=" * 60)
print("Test 1: First request (cache WRITE)")
print("=" * 60)

messages = [{"role": "user", "content": "What time is it?"}]
response = chat(messages, system=SYSTEM_PROMPT, tools=TOOLS)
print(response.content[0].text if response.content[0].type == "text" else "(tool_use)")
print_usage(response, "First request")


# === Test 2: Same request — reads from cache ===
print("\n" + "=" * 60)
print("Test 2: Same context (cache READ)")
print("=" * 60)

messages = [{"role": "user", "content": "How do I write a Python decorator?"}]
response = chat(messages, system=SYSTEM_PROMPT, tools=TOOLS)
print(response.content[0].text[:200] + "...")
print_usage(response, "Second request")


# === Test 3: Changed system prompt — partial cache ===
print("\n" + "=" * 60)
print("Test 3: Changed system prompt (partial cache)")
print("=" * 60)

new_system = SYSTEM_PROMPT + "\nAlways respond in exactly 2 sentences."
messages = [{"role": "user", "content": "Explain recursion."}]
response = chat(messages, system=new_system, tools=TOOLS)
print(response.content[0].text[:200])
print_usage(response, "Changed system prompt")
