from dotenv import load_dotenv
load_dotenv()

from anthropic import Anthropic

client = Anthropic()
model = "claude-sonnet-4-6"


def add_user_message(messages, text):
    messages.append({"role": "user", "content": text})


def add_assistant_message(messages, text):
    messages.append({"role": "assistant", "content": text})


def chat(messages):
    message = client.messages.create(
        model=model,
        max_tokens=1000,
        messages=messages,
    )
    return message.content[0].text


messages = []

add_user_message(messages, "Define quantum computing in one sentence")
answer = chat(messages)
print("First response:", answer)

add_assistant_message(messages, answer)

add_user_message(messages, "Write another sentence")
final_answer = chat(messages)
print("Follow-up response:", final_answer)
