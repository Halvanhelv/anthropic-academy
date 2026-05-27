from dotenv import load_dotenv
load_dotenv()

from datetime import datetime, timedelta
from anthropic import Anthropic

client = Anthropic()
model = "claude-sonnet-4-0"


def add_user_message(messages, text):
    messages.append({"role": "user", "content": text})


def add_assistant_message(messages, text):
    messages.append({"role": "assistant", "content": text})


def chat(messages, system=None, temperature=1.0, stop_sequences=[]):
    params = {
        "model": model,
        "max_tokens": 4096,
        "messages": messages,
        "temperature": temperature,
        "stop_sequences": stop_sequences,
    }
    if system:
        params["system"] = system
    message = client.messages.create(**params)
    return message.content[0].text


# --- Tool Function #1: Get current datetime ---
def get_current_datetime(date_format="%Y-%m-%d %H:%M:%S"):
    if not date_format:
        raise ValueError("date_format cannot be empty")
    return datetime.now().strftime(date_format)


# --- Test the function ---
print("Default format:", get_current_datetime())
print("Date only:", get_current_datetime("%Y-%m-%d"))
print("Time only:", get_current_datetime("%H:%M"))
print("Day of week:", get_current_datetime("%A, %B %d, %Y"))

# Validation test
try:
    get_current_datetime("")
except ValueError as e:
    print(f"Validation works: {e}")
