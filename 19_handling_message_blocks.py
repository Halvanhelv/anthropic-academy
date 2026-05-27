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

# --- Step 1: Send message with tools ---
messages = [{"role": "user", "content": "What is the exact time, formatted as HH:MM:SS?"}]

response = client.messages.create(
    model=model,
    max_tokens=4096,
    tools=[get_current_datetime_schema],
    messages=messages,
)

# --- Step 2: Handle multi-block response ---
print("=== Response has multiple content blocks ===")
print(f"Stop reason: {response.stop_reason}")
print(f"Number of blocks: {len(response.content)}")
print()

for block in response.content:
    if block.type == "text":
        print(f"[Text Block] {block.text}")
    elif block.type == "tool_use":
        print(f"[ToolUse Block]")
        print(f"  id: {block.id}")
        print(f"  name: {block.name}")
        print(f"  input: {block.input}")

# --- Step 3: Add full assistant response to conversation history ---
# Must preserve ALL blocks (text + tool_use), not just text
messages.append({"role": "assistant", "content": response.content})

print()
print("=== Conversation history ===")
for msg in messages:
    print(f"  {msg['role']}: {type(msg['content']).__name__}")

# --- Step 4: Extract tool_use block and run function ---
tool_use_block = next(b for b in response.content if b.type == "tool_use")
tool_name = tool_use_block.name
tool_input = tool_use_block.input

print()
print(f"=== Executing tool: {tool_name} ===")
result = get_current_datetime(**tool_input)
print(f"Result: {result}")
