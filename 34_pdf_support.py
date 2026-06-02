from dotenv import load_dotenv
load_dotenv()

import base64
from anthropic import Anthropic

client = Anthropic()
model = "claude-sonnet-4-0"


def chat(messages, system=None):
    params = {"model": model, "max_tokens": 4096, "messages": messages}
    if system:
        params["system"] = system
    return client.messages.create(**params)


def load_pdf_base64(path):
    with open(path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


# === Test 1: Summarize PDF ===
print("=" * 60)
print("Test 1: Summarize PDF in one sentence")
print("=" * 60)

file_bytes = load_pdf_base64("earth.pdf")

messages = [{"role": "user", "content": [
    {
        "type": "document",
        "source": {"type": "base64", "media_type": "application/pdf", "data": file_bytes},
    },
    {"type": "text", "text": "Summarize the document in one sentence."},
]}]

response = chat(messages)
print(response.content[0].text)


# === Test 2: Extract specific data ===
print("\n" + "=" * 60)
print("Test 2: Extract specific facts from PDF")
print("=" * 60)

messages = [{"role": "user", "content": [
    {
        "type": "document",
        "source": {"type": "base64", "media_type": "application/pdf", "data": file_bytes},
    },
    {"type": "text", "text": "List 5 key facts about Earth from this document. Keep each fact to one sentence."},
]}]

response = chat(messages)
print(response.content[0].text)
