from dotenv import load_dotenv
load_dotenv()

from anthropic import Anthropic

client = Anthropic()
model = "claude-sonnet-4-0"

REDACTED_THINKING_TRIGGER = "ANTHROPIC_MAGIC_STRING_TRIGGER_REDACTED_THINKING_46C9A13E193C177646C7398A98432ECCCE4C1253D5E2D82641AC0E52CC2876CB"


def chat(messages, system=None, thinking=False, thinking_budget=1024):
    params = {
        "model": model,
        "max_tokens": 4096,
        "messages": messages,
    }
    if thinking:
        params["thinking"] = {
            "type": "enabled",
            "budget_tokens": thinking_budget,
        }
    if system:
        params["system"] = system
    return client.messages.create(**params)


# === Test 1: Normal response (no thinking) ===
print("=" * 60)
print("Test 1: Without extended thinking")
print("=" * 60)
messages = [{"role": "user", "content": "What is 27 * 453?"}]
response = chat(messages)
print(f"Blocks: {len(response.content)}")
for block in response.content:
    print(f"  [{block.type}] {block.text[:200] if hasattr(block, 'text') else '(no text)'}")


# === Test 2: With extended thinking ===
print("\n" + "=" * 60)
print("Test 2: With extended thinking")
print("=" * 60)
messages = [{"role": "user", "content": "What is 27 * 453? Show your reasoning."}]
response = chat(messages, thinking=True, thinking_budget=2048)
print(f"Blocks: {len(response.content)}")
for block in response.content:
    if block.type == "thinking":
        print(f"  [thinking] {block.thinking[:300]}...")
    elif block.type == "text":
        print(f"  [text] {block.text[:300]}")
    elif block.type == "redacted_thinking":
        print(f"  [redacted_thinking] (encrypted, {len(block.data)} chars)")


# === Test 3: Redacted thinking (trigger) ===
print("\n" + "=" * 60)
print("Test 3: Redacted thinking (safety trigger)")
print("=" * 60)
messages = [{"role": "user", "content": REDACTED_THINKING_TRIGGER}]
response = chat(messages, thinking=True, thinking_budget=2048)
print(f"Blocks: {len(response.content)}")
for block in response.content:
    if block.type == "thinking":
        print(f"  [thinking] {block.thinking[:200]}...")
    elif block.type == "text":
        print(f"  [text] {block.text[:200]}")
    elif block.type == "redacted_thinking":
        print(f"  [redacted_thinking] (encrypted, {len(block.data)} chars)")
