from dotenv import load_dotenv
load_dotenv()

from datetime import datetime, timedelta
from anthropic import Anthropic
from anthropic.types import Message, ToolParam

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
    return "\n".join(block.text for block in message.content if block.type == "text")


# --- Tool Functions ---
def get_current_datetime(date_format="%Y-%m-%d %H:%M:%S"):
    if not date_format:
        raise ValueError("date_format cannot be empty")
    return datetime.now().strftime(date_format)


def add_duration_to_datetime(datetime_str, duration=0, unit="days", input_format="%Y-%m-%d"):
    date = datetime.strptime(datetime_str, input_format)
    if unit == "seconds":
        new_date = date + timedelta(seconds=duration)
    elif unit == "minutes":
        new_date = date + timedelta(minutes=duration)
    elif unit == "hours":
        new_date = date + timedelta(hours=duration)
    elif unit == "days":
        new_date = date + timedelta(days=duration)
    elif unit == "weeks":
        new_date = date + timedelta(weeks=duration)
    elif unit == "months":
        month = date.month + duration
        year = date.year + month // 12
        month = month % 12
        if month == 0:
            month = 12
            year -= 1
        day = min(
            date.day,
            [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
             31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1],
        )
        new_date = date.replace(year=year, month=month, day=day)
    elif unit == "years":
        new_date = date.replace(year=date.year + duration)
    else:
        raise ValueError(f"Unsupported time unit: {unit}")
    return new_date.strftime("%A, %B %d, %Y %I:%M:%S %p")


def set_reminder(content, timestamp):
    print(f"  ----\n  Setting the following reminder for {timestamp}:\n  {content}\n  ----")
    return f"Reminder set: '{content}' at {timestamp}"


# --- Tool Schemas ---
get_current_datetime_schema = ToolParam(
    name="get_current_datetime",
    description=(
        "Returns the current date and time formatted according to the specified format string. "
        "Use this tool whenever a user asks about the current date, time, or day of the week. "
        "The tool returns a string with the formatted current datetime. "
        "The format parameter uses Python's strftime format codes."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "date_format": {
                "type": "string",
                "description": "A Python strftime format string. Defaults to '%Y-%m-%d %H:%M:%S'.",
            }
        },
        "required": [],
    },
)

add_duration_to_datetime_schema = ToolParam(
    name="add_duration_to_datetime",
    description=(
        "Adds a specified duration to a datetime string and returns the resulting datetime. "
        "Use this tool to calculate future or past dates by adding or subtracting time. "
        "Handles seconds, minutes, hours, days, weeks, months, and years. "
        "Returns a detailed format like 'Thursday, April 03, 2025 10:30:00 AM'."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "datetime_str": {
                "type": "string",
                "description": "The input datetime string to add duration to.",
            },
            "duration": {
                "type": "number",
                "description": "Amount of time to add. Can be negative for past dates. Defaults to 0.",
            },
            "unit": {
                "type": "string",
                "description": "Time unit: 'seconds', 'minutes', 'hours', 'days', 'weeks', 'months', or 'years'. Defaults to 'days'.",
            },
            "input_format": {
                "type": "string",
                "description": "Format string for parsing datetime_str. Defaults to '%Y-%m-%d'.",
            },
        },
        "required": ["datetime_str"],
    },
)

set_reminder_schema = ToolParam(
    name="set_reminder",
    description=(
        "Creates a timed reminder that will notify the user at the specified time. "
        "Use this tool when a user wants to be reminded about something at a future time. "
        "The reminder system will store the content and trigger a notification at the timestamp. "
        "Reminders persist even if the application is closed."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "The message text for the reminder notification.",
            },
            "timestamp": {
                "type": "string",
                "description": "The date and time for the reminder, as ISO 8601 (YYYY-MM-DDTHH:MM:SS).",
            },
        },
        "required": ["content", "timestamp"],
    },
)

tools = [get_current_datetime_schema, add_duration_to_datetime_schema, set_reminder_schema]


# --- Tool routing ---
def run_tool(tool_name, tool_input):
    tool_functions = {
        "get_current_datetime": get_current_datetime,
        "add_duration_to_datetime": add_duration_to_datetime,
        "set_reminder": set_reminder,
    }
    if tool_name not in tool_functions:
        raise ValueError(f"Unknown tool: {tool_name}")
    return tool_functions[tool_name](**tool_input)


def run_tools(message):
    tool_results = []
    for block in message.content:
        if block.type == "tool_use":
            try:
                result = run_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(result),
                    "is_error": False,
                })
                print(f"    {block.name}({block.input}) -> {result}")
            except Exception as e:
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": f"Error: {e}",
                    "is_error": True,
                })
                print(f"    {block.name} ERROR: {e}")
    return tool_results


# --- Conversation loop ---
def run_conversation(messages):
    turn = 0
    while True:
        turn += 1
        response = chat(messages, tools=tools)
        add_assistant_message(messages, response)

        text = text_from_message(response)
        if text:
            print(f"  [Turn {turn}] Claude: {text}")

        if response.stop_reason != "tool_use":
            break

        print(f"  [Turn {turn}] Tool calls:")
        tool_results = run_tools(response)
        add_user_message(messages, tool_results)

    return messages


# === Test: Set reminder using multiple tools ===
print("=" * 60)
print("Set a reminder for my doctors appointment.")
print("Its 177 days after Jan 1st, 2050.")
print("=" * 60)
messages = []
add_user_message(messages, "Set a reminder for my doctors appointment. Its 177 days after Jan 1st, 2050.")
run_conversation(messages)
