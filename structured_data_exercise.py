from dotenv import load_dotenv
load_dotenv()

from anthropic import Anthropic

client = Anthropic()
model = "claude-sonnet-4-0"


def add_user_message(messages, text):
    messages.append({"role": "user", "content": text})


def add_assistant_message(messages, text):
    messages.append({"role": "assistant", "content": text})


def chat(messages, stop_sequences=None):
    params = {
        "model": model,
        "max_tokens": 1000,
        "messages": messages,
    }
    if stop_sequences:
        params["stop_sequences"] = stop_sequences
    message = client.messages.create(**params)
    return message.content[0].text


prompt = "Generate three different sample AWS CLI commands. Each should be very short."

# Attempt 1: no prefilling — gets explanations
print("=== Attempt 1: No prefilling ===\n")
messages = []
add_user_message(messages, prompt)
text = chat(messages)
print(text.strip())

# Attempt 2: prefill with ``` — still gets text before block
print("\n=== Attempt 2: Prefill with ``` ===\n")
messages = []
add_user_message(messages, prompt)
add_assistant_message(messages, "```")
text = chat(messages, stop_sequences=["```"])
print(text.strip())

# Attempt 3: prefill with ```bash — might get 1 command or comments
print("\n=== Attempt 3: Prefill with ```bash ===\n")
messages = []
add_user_message(messages, prompt)
add_assistant_message(messages, "```bash")
text = chat(messages, stop_sequences=["```"])
print(text.strip())

# Attempt 4: prefill with full sentence + ```bash — clean result
print("\n=== Attempt 4: Full sentence prefill ===\n")
messages = []
add_user_message(messages, prompt)
add_assistant_message(messages, "Here are all three commands in a single block without any comments:\n```bash")
text = chat(messages, stop_sequences=["```"])
print(text.strip())
