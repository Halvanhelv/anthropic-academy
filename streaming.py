from dotenv import load_dotenv
load_dotenv()

from anthropic import Anthropic

client = Anthropic()
model = "claude-sonnet-4-6"

messages = [{"role": "user", "content": "Write a 1 sentence description of a fake database"}]

print("=== Streaming response ===\n")

with client.messages.stream(
    model=model,
    max_tokens=1000,
    messages=messages,
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)

    final_message = stream.get_final_message()

print("\n\n=== Final message metadata ===")
print(f"Model: {final_message.model}")
print(f"Stop reason: {final_message.stop_reason}")
print(f"Usage: {final_message.usage.input_tokens} in / {final_message.usage.output_tokens} out")
