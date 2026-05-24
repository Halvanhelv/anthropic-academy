from dotenv import load_dotenv
load_dotenv()

from anthropic import Anthropic

client = Anthropic()
model = "claude-sonnet-4-6"


def add_user_message(messages, text):
    messages.append({"role": "user", "content": text})


def chat(messages, system=None):
    params = {
        "model": model,
        "max_tokens": 1000,
        "messages": messages,
    }
    if system:
        params["system"] = system
    message = client.messages.create(**params)
    return message.content[0].text


prompt = "Write a Python function that checks a string for duplicate characters."

# Without system prompt
print("=== WITHOUT system prompt ===\n")
messages = []
add_user_message(messages, prompt)
answer = chat(messages)
print(answer)

# With system prompt
print("\n=== WITH system prompt ===\n")
messages = []
add_user_message(messages, prompt)
answer = chat(messages, system="You are a Python engineer who writes very concise code")
print(answer)
