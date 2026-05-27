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

# --- Send to Claude with tools ---
messages = [{"role": "user", "content": "What is the current date and time?"}]

response = client.messages.create(
    model=model,
    max_tokens=4096,
    tools=[get_current_datetime_schema],
    messages=messages,
)

print("Stop reason:", response.stop_reason)
print()
for block in response.content:
    print(f"Type: {block.type}")
    if block.type == "tool_use":
        print(f"  Tool: {block.name}")
        print(f"  ID: {block.id}")
        print(f"  Input: {block.input}")
    elif block.type == "text":
        print(f"  Text: {block.text}")
