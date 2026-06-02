from dotenv import load_dotenv
load_dotenv()

from anthropic import Anthropic

client = Anthropic()
model = "claude-sonnet-4-0"


def upload(file_path):
    with open(file_path, "rb") as f:
        return client.beta.files.upload(file=f)


def download_file(file_id, output_path):
    data = client.beta.files.download(file_id)
    content = data.read()
    with open(output_path, "wb") as f:
        f.write(content)
    print(f"Downloaded: {output_path} ({len(content)} bytes)")


def chat(messages, tools=None):
    params = {"model": model, "max_tokens": 16000, "messages": messages}
    if tools:
        params["tools"] = tools
    return client.messages.create(**params)


# === Step 1: Upload CSV via Files API ===
print("=" * 60)
print("Step 1: Upload streaming.csv via Files API")
print("=" * 60)

file_metadata = upload("streaming.csv")
print(f"File ID: {file_metadata.id}")


# === Step 2: Analyze with code execution ===
print("\n" + "=" * 60)
print("Step 2: Ask Claude to analyze churn drivers")
print("=" * 60)

messages = [{"role": "user", "content": [
    {"type": "text", "text": (
        "Run a detailed analysis to determine major drivers of churn. "
        "Your final output should include at least one detailed plot "
        "summarizing your findings."
    )},
    {"type": "container_upload", "file_id": file_metadata.id},
]}]

response = chat(
    messages,
    tools=[{"type": "code_execution_20250522", "name": "code_execution"}],
)


# === Step 3: Process response blocks ===
print("\n" + "=" * 60)
print("Step 3: Response blocks")
print("=" * 60)

for block in response.content:
    if block.type == "text":
        print(f"\n[Text]: {block.text[:300]}...")
    elif block.type == "server_tool_use":
        code = block.input.get("code", "")
        print(f"\n[Code Execution]: {code[:150]}...")
    elif block.type == "code_execution_tool_result":
        result = block.content
        if result.stdout:
            print(f"\n[stdout]: {result.stdout[:200]}")
        if result.stderr:
            print(f"\n[stderr]: {result.stderr[:200]}")
        for item in result.content:
            if item.type == "code_execution_output":
                print(f"\n[Generated file]: {item.file_id}")
                download_file(item.file_id, "churn_analysis.png")


# === Step 4: Print final text summary ===
print("\n" + "=" * 60)
print("Step 4: Final analysis")
print("=" * 60)

for block in response.content:
    if block.type == "text" and len(block.text) > 100:
        print(block.text[:1000])
        break
