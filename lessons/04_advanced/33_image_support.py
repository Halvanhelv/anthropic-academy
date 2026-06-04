from dotenv import load_dotenv
load_dotenv()

import base64
from anthropic import Anthropic

client = Anthropic()
model = "claude-sonnet-4-0"


def chat(messages, system=None):
    params = {
        "model": model,
        "max_tokens": 4096,
        "messages": messages,
    }
    if system:
        params["system"] = system
    return client.messages.create(**params)


def load_image_base64(path):
    with open(path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def make_image_message(image_path, text, media_type="image/png"):
    image_data = load_image_base64(image_path)
    return [{
        "type": "image",
        "source": {"type": "base64", "media_type": media_type, "data": image_data},
    }, {
        "type": "text",
        "text": text,
    }]


# === Test 1: Simple image description ===
print("=" * 60)
print("Test 1: Describe an image")
print("=" * 60)
messages = [{"role": "user", "content": make_image_message(
    "images/prop1.png", "What do you see in this image? Describe briefly."
)}]
response = chat(messages)
print(response.content[0].text[:500])


# === Test 2: Fire risk assessment with detailed prompt ===
print("\n" + "=" * 60)
print("Test 2: Fire risk assessment (structured prompt)")
print("=" * 60)

fire_risk_prompt = """
Analyze the attached satellite image of a property:

1. Residence identification: Locate the primary residence.
2. Tree overhang analysis: Estimate % of roof covered by branches (0-25%, 25-50%, 50-75%, 75%+).
3. Fire risk assessment: Evaluate wildfire vulnerability.
4. Defensible space: Assess vegetation structure around the home.
5. Fire risk rating (1-4):
   - 1 (Low): No overhang, good defensible space
   - 2 (Moderate): <25% overhang, some canopy separation
   - 3 (High): 25-50% overhang, connected canopies
   - 4 (Severe): >50% overhang, dense vegetation against structure

For each item (1-5), write one sentence. End with the numeric rating.
"""

messages = [{"role": "user", "content": make_image_message(
    "images/prop1.png", fire_risk_prompt
)}]
response = chat(messages)
print(response.content[0].text)


# === Test 3: Compare two images ===
print("\n" + "=" * 60)
print("Test 3: Compare two properties")
print("=" * 60)

img1 = load_image_base64("images/prop1.png")
img2 = load_image_base64("images/prop2.png")

messages = [{"role": "user", "content": [
    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img1}},
    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img2}},
    {"type": "text", "text": "Compare these two properties. Which has higher fire risk and why? Keep it under 3 sentences."},
]}]
response = chat(messages)
print(response.content[0].text)
