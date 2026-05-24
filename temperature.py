from dotenv import load_dotenv
load_dotenv()

from anthropic import Anthropic

client = Anthropic()
model = "claude-sonnet-4-6"


def chat(messages, system=None, temperature=1.0):
    params = {
        "model": model,
        "max_tokens": 1000,
        "messages": messages,
        "temperature": temperature,
    }
    if system:
        params["system"] = system
    message = client.messages.create(**params)
    return message.content[0].text


prompt = "Give me a one-sentence movie idea."

for temp in [0.0, 0.5, 1.0]:
    print(f"=== Temperature {temp} ===")
    for i in range(3):
        messages = [{"role": "user", "content": prompt}]
        answer = chat(messages, temperature=temp)
        print(f"  {i+1}. {answer}")
    print()
