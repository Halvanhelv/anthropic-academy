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


# === Test 1: PDF with citations ===
print("=" * 60)
print("Test 1: PDF citations (page numbers)")
print("=" * 60)

file_bytes = load_pdf_base64("earth.pdf")

messages = [{"role": "user", "content": [
    {
        "type": "document",
        "source": {"type": "base64", "media_type": "application/pdf", "data": file_bytes},
        "title": "earth.pdf",
        "citations": {"enabled": True},
    },
    {"type": "text", "text": "How were Earth's atmosphere and oceans formed?"},
]}]

response = chat(messages)

for block in response.content:
    if block.type == "text":
        print(f"\n[Text]: {block.text}")
        if hasattr(block, "citations") and block.citations:
            for cite in block.citations:
                print(f"  [{cite.document_title}] cited: \"{cite.cited_text[:80]}...\"")
                print(f"    pages {cite.start_page_number}-{cite.end_page_number}")


# === Test 2: Plain text with citations ===
print("\n" + "=" * 60)
print("Test 2: Plain text citations (character positions)")
print("=" * 60)

article_text = """Earth is the third planet from the Sun. It has a dynamic atmosphere composed primarily of nitrogen and oxygen. The planet's surface is 70.8% water. Earth's magnetic field protects it from solar wind. Life emerged approximately 3.7 billion years ago."""

messages = [{"role": "user", "content": [
    {
        "type": "document",
        "source": {"type": "text", "media_type": "text/plain", "data": article_text},
        "title": "earth_article",
        "citations": {"enabled": True},
    },
    {"type": "text", "text": "What protects Earth from solar wind and what is the atmosphere made of?"},
]}]

response = chat(messages)

for block in response.content:
    if block.type == "text":
        print(f"\n[Text]: {block.text}")
        if hasattr(block, "citations") and block.citations:
            for cite in block.citations:
                print(f"  [{cite.document_title}] cited: \"{cite.cited_text}\"")
                if hasattr(cite, "start_char_index"):
                    print(f"    chars {cite.start_char_index}-{cite.end_char_index}")
                elif hasattr(cite, "start_page_number"):
                    print(f"    pages {cite.start_page_number}-{cite.end_page_number}")
