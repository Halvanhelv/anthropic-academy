from dotenv import load_dotenv
load_dotenv()

from datetime import datetime
from anthropic import Anthropic
from anthropic.types import ToolParam

client = Anthropic()
model = "claude-sonnet-4-0"


# --- Tool Function ---
def get_current_datetime(date_format="%Y-%m-%d %H:%M:%S"):
    if not date_format:
        raise ValueError("date_format cannot be empty")
    return datetime.now().strftime(date_format)


# --- Tool Schema ---
get_current_datetime_schema = ToolParam(
    name="get_current_datetime",
    description=(
        "Returns the current date and time formatted according to the specified format string. "
        "Use this tool whenever a user asks about the current date, time, or day of the week. "
        "The tool returns a string with the formatted current datetime. "
        "The format parameter uses Python's strftime format codes such as %Y for year, %m for month, "
        "%d for day, %H for hour, %M for minute, %S for second, and %A for day of week."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "date_format": {
                "type": "string",
                "description": (
                    "A Python strftime format string specifying the output format. "
                    "Common formats: '%Y-%m-%d %H:%M:%S' for full datetime, "
                    "'%Y-%m-%d' for date only, '%H:%M' for time only, "
                    "'%A' for day of week. Defaults to '%Y-%m-%d %H:%M:%S'."
                ),
            }
        },
        "required": [],
    },
)

tools = [get_current_datetime_schema]

# === FULL TOOL USE CYCLE ===

# Step 1: Send user message
messages = [{"role": "user", "content": "What is the exact time right now, formatted as HH:MM:SS?"}]

print("=== Step 1: Send user message ===")
response = client.messages.create(
    model=model,
    max_tokens=4096,
    tools=tools,
    messages=messages,
)
print(f"Stop reason: {response.stop_reason}")

# Step 2: Add assistant response to history (preserve all blocks)
messages.append({"role": "assistant", "content": response.content})

# Step 3: Extract tool_use block and execute function
tool_use_block = next(b for b in response.content if b.type == "tool_use")
print(f"\n=== Step 2: Claude wants to call {tool_use_block.name} ===")
print(f"Input: {tool_use_block.input}")

result = get_current_datetime(**tool_use_block.input)
print(f"Function returned: {result}")

# Step 4: Send tool result back to Claude
print("\n=== Step 3: Send tool_result back ===")
messages.append({
    "role": "user",
    "content": [{
        "type": "tool_result",
        "tool_use_id": tool_use_block.id,
        "content": str(result),
        "is_error": False,
    }],
})

# Step 5: Get final response (must still include tools param)
final_response = client.messages.create(
    model=model,
    max_tokens=4096,
    tools=tools,
    messages=messages,
)

print(f"Stop reason: {final_response.stop_reason}")
print(f"\n=== Final response ===")
for block in final_response.content:
    if block.type == "text":
        print(block.text)

# Show full conversation history
print("\n=== Message history ===")
for i, msg in enumerate(messages):
    role = msg["role"]
    content = msg["content"]
    if isinstance(content, str):
        print(f"  [{i}] {role}: {content[:80]}")
    elif isinstance(content, list):
        types = [b["type"] if isinstance(b, dict) else b.type for b in content]
        print(f"  [{i}] {role}: blocks={types}")
