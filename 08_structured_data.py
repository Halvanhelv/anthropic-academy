from dotenv import load_dotenv
load_dotenv()

import json
from anthropic import Anthropic

client = Anthropic()
model = "claude-sonnet-4-0"


def add_user_message(messages, text):
    messages.append({"role": "user", "content": text})


def add_assistant_message(messages, text):
    messages.append({"role": "assistant", "content": text})


def chat(messages, system=None, stop_sequences=None):
    params = {
        "model": model,
        "max_tokens": 1000,
        "messages": messages,
    }
    if system:
        params["system"] = system
    if stop_sequences:
        params["stop_sequences"] = stop_sequences
    message = client.messages.create(**params)
    return message.content[0].text


# Without prefilling — gets markdown + explanation
print("=== WITHOUT prefilling ===\n")
messages = []
add_user_message(messages, "Generate a very short EventBridge rule as JSON")
answer = chat(messages)
print(answer)

# With prefilling + stop sequence — clean JSON only
print("\n=== WITH prefilling + stop sequence ===\n")
messages = []
add_user_message(messages, "Generate a very short EventBridge rule as JSON")
add_assistant_message(messages, "```json")
raw = chat(messages, stop_sequences=["```"])

clean_json = json.loads(raw.strip())
print(json.dumps(clean_json, indent=2))
