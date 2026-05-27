from dotenv import load_dotenv
load_dotenv()

import json
from anthropic import Anthropic
from anthropic.types import ToolParam

client = Anthropic()
model = "claude-sonnet-4-0"


# --- Helper functions ---
def add_user_message(messages, message):
    if isinstance(message, list):
        messages.append({"role": "user", "content": message})
    else:
        messages.append({"role": "user", "content": [{"type": "text", "text": message}]})


def add_assistant_message(messages, message):
    if isinstance(message, list):
        messages.append({"role": "assistant", "content": message})
    elif hasattr(message, "content"):
        content_list = []
        for block in message.content:
            if block.type == "text":
                content_list.append({"type": "text", "text": block.text})
            elif block.type == "tool_use":
                content_list.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })
        messages.append({"role": "assistant", "content": content_list})
    else:
        messages.append({"role": "assistant", "content": [{"type": "text", "text": message}]})


def chat_stream(messages, system=None, temperature=1.0, stop_sequences=[],
                tools=None, tool_choice=None, betas=[]):
    params = {
        "model": model,
        "max_tokens": 4096,
        "messages": messages,
        "temperature": temperature,
        "stop_sequences": stop_sequences,
    }
    if tool_choice:
        params["tool_choice"] = tool_choice
    if tools:
        params["tools"] = tools
    if system:
        params["system"] = system
    if betas:
        params["betas"] = betas
    return client.beta.messages.stream(**params)


# --- Tool ---
save_article_schema = ToolParam(
    name="save_article",
    description="Saves a scholarly journal article with abstract and metadata.",
    input_schema={
        "type": "object",
        "properties": {
            "abstract": {
                "type": "string",
                "description": "Abstract of the article. One short sentence max.",
            },
            "meta": {
                "type": "object",
                "properties": {
                    "word_count": {
                        "type": "integer",
                        "description": "Word count of the article.",
                    },
                    "review": {
                        "type": "string",
                        "description": "A short review of the paper.",
                    },
                },
                "required": ["word_count", "review"],
            },
        },
        "required": ["abstract", "meta"],
    },
)


def save_article(**kwargs):
    return "Article saved!"


def run_tool(tool_name, tool_input):
    if tool_name == "save_article":
        return save_article(**tool_input)


def run_tools(message):
    tool_results = []
    for block in message.content:
        if block.type == "tool_use":
            try:
                result = run_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                    "is_error": False,
                })
            except Exception as e:
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": f"Error: {e}",
                    "is_error": True,
                })
    return tool_results


# --- Conversation loop with streaming ---
def run_conversation(messages, tools=[], tool_choice=None, fine_grained=False):
    while True:
        with chat_stream(
            messages,
            tools=tools,
            betas=["fine-grained-tool-streaming-2025-05-14"] if fine_grained else [],
            tool_choice=tool_choice,
        ) as stream:
            for chunk in stream:
                if chunk.type == "text":
                    print(chunk.text, end="")

                if chunk.type == "content_block_start":
                    if chunk.content_block.type == "tool_use":
                        print(f'\n>>> Tool Call: "{chunk.content_block.name}"')

                if chunk.type == "input_json" and chunk.partial_json:
                    print(chunk.partial_json, end="")

                if chunk.type == "content_block_stop":
                    print()

            response = stream.get_final_message()

        add_assistant_message(messages, response)

        if response.stop_reason != "tool_use":
            break

        tool_results = run_tools(response)
        add_user_message(messages, tool_results)

        if tool_choice:
            break

    return messages


# === Test 1: Default streaming (with JSON validation) ===
print("=" * 60)
print("Test 1: Default tool streaming (buffered per top-level key)")
print("=" * 60)
messages = []
add_user_message(messages, "Generate and save a fake computer science article")
run_conversation(
    messages,
    tools=[save_article_schema],
    tool_choice={"type": "tool", "name": "save_article"},
)

# === Test 2: Fine-grained streaming (no buffering) ===
print("\n" + "=" * 60)
print("Test 2: Fine-grained streaming (chunks sent immediately)")
print("=" * 60)
messages = []
add_user_message(messages, "Generate and save a fake biology article about CRISPR")
run_conversation(
    messages,
    tools=[save_article_schema],
    tool_choice={"type": "tool", "name": "save_article"},
    fine_grained=True,
)
