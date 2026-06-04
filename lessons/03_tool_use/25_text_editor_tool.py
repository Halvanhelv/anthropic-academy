from dotenv import load_dotenv
load_dotenv()

import os
import json
import shutil
from anthropic import Anthropic
from anthropic.types import Message

client = Anthropic()
model = "claude-sonnet-4-0"


# --- Helper functions ---
def add_user_message(messages, message):
    messages.append({
        "role": "user",
        "content": message.content if isinstance(message, Message) else message,
    })


def add_assistant_message(messages, message):
    messages.append({
        "role": "assistant",
        "content": message.content if isinstance(message, Message) else message,
    })


def chat(messages, system=None, temperature=1.0, stop_sequences=[], tools=None):
    params = {
        "model": model,
        "max_tokens": 4096,
        "messages": messages,
        "temperature": temperature,
        "stop_sequences": stop_sequences,
    }
    if tools:
        params["tools"] = tools
    if system:
        params["system"] = system
    return client.messages.create(**params)


def text_from_message(message):
    return "\n".join(block.text for block in message.content if block.type == "text")


# --- TextEditorTool implementation ---
class TextEditorTool:
    def __init__(self, base_dir=""):
        self.base_dir = base_dir or os.getcwd()
        self.backup_dir = os.path.join(self.base_dir, ".backups")
        os.makedirs(self.backup_dir, exist_ok=True)

    def _validate_path(self, file_path):
        abs_path = os.path.normpath(os.path.join(self.base_dir, file_path))
        if not abs_path.startswith(self.base_dir):
            raise ValueError(f"Access denied: Path '{file_path}' is outside allowed directory")
        return abs_path

    def _backup_file(self, file_path):
        if not os.path.exists(file_path):
            return ""
        file_name = os.path.basename(file_path)
        backup_path = os.path.join(self.backup_dir, f"{file_name}.{os.path.getmtime(file_path):.0f}")
        shutil.copy2(file_path, backup_path)
        return backup_path

    def _restore_backup(self, file_path):
        file_name = os.path.basename(file_path)
        backups = [f for f in os.listdir(self.backup_dir) if f.startswith(file_name + ".")]
        if not backups:
            raise FileNotFoundError(f"No backups found for {file_path}")
        latest_backup = sorted(backups, reverse=True)[0]
        shutil.copy2(os.path.join(self.backup_dir, latest_backup), file_path)
        return f"Successfully restored {file_path} from backup"

    def view(self, file_path, view_range=None):
        abs_path = self._validate_path(file_path)
        if os.path.isdir(abs_path):
            return "\n".join(os.listdir(abs_path))
        if not os.path.exists(abs_path):
            raise FileNotFoundError("File not found")
        with open(abs_path, "r", encoding="utf-8") as f:
            content = f.read()
        lines = content.split("\n")
        if view_range:
            start, end = view_range
            if end == -1:
                end = len(lines)
            lines = lines[start - 1:end]
            return "\n".join(f"{i}: {line}" for i, line in enumerate(lines, start))
        return "\n".join(f"{i}: {line}" for i, line in enumerate(lines, 1))

    def str_replace(self, file_path, old_str, new_str):
        abs_path = self._validate_path(file_path)
        if not os.path.exists(abs_path):
            raise FileNotFoundError("File not found")
        with open(abs_path, "r", encoding="utf-8") as f:
            content = f.read()
        match_count = content.count(old_str)
        if match_count == 0:
            raise ValueError("No match found for replacement.")
        elif match_count > 1:
            raise ValueError(f"Found {match_count} matches. Provide more context for unique match.")
        self._backup_file(abs_path)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content.replace(old_str, new_str))
        return "Successfully replaced text at exactly one location."

    def create(self, file_path, file_text):
        abs_path = self._validate_path(file_path)
        if os.path.exists(abs_path):
            raise FileExistsError("File already exists. Use str_replace to modify it.")
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(file_text)
        return f"Successfully created {file_path}"

    def insert(self, file_path, insert_line, new_str):
        abs_path = self._validate_path(file_path)
        if not os.path.exists(abs_path):
            raise FileNotFoundError("File not found")
        self._backup_file(abs_path)
        with open(abs_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if lines and not lines[-1].endswith("\n"):
            new_str = "\n" + new_str
        if insert_line == 0:
            lines.insert(0, new_str + "\n")
        elif 0 < insert_line <= len(lines):
            lines.insert(insert_line, new_str + "\n")
        else:
            raise IndexError(f"Line {insert_line} out of range. File has {len(lines)} lines.")
        with open(abs_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        return f"Successfully inserted text after line {insert_line}"

    def undo_edit(self, file_path):
        abs_path = self._validate_path(file_path)
        if not os.path.exists(abs_path):
            raise FileNotFoundError("File not found")
        return self._restore_backup(abs_path)


# --- Tool routing ---
text_editor = TextEditorTool()


def run_tool(tool_name, tool_input):
    if tool_name == "str_replace_based_edit_tool":
        command = tool_input["command"]
        if command == "view":
            return text_editor.view(tool_input["path"], tool_input.get("view_range"))
        elif command == "str_replace":
            return text_editor.str_replace(tool_input["path"], tool_input["old_str"], tool_input["new_str"])
        elif command == "create":
            return text_editor.create(tool_input["path"], tool_input["file_text"])
        elif command == "insert":
            return text_editor.insert(tool_input["path"], tool_input["insert_line"], tool_input["new_str"])
        elif command == "undo_edit":
            return text_editor.undo_edit(tool_input["path"])
        else:
            raise Exception(f"Unknown command: {command}")
    else:
        raise Exception(f"Unknown tool: {tool_name}")


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
                print(f"    [{block.input.get('command', '?')}] {block.input.get('path', '')} -> OK")
            except Exception as e:
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": f"Error: {e}",
                    "is_error": True,
                })
                print(f"    [{block.input.get('command', '?')}] ERROR: {e}")
    return tool_results


# --- Schema stub (Claude knows the full schema internally) ---
def get_text_edit_schema():
    return {
        "type": "text_editor_20250429",
        "name": "str_replace_based_edit_tool",
    }


# --- Conversation loop ---
def run_conversation(messages):
    turn = 0
    while True:
        turn += 1
        response = chat(messages, tools=[get_text_edit_schema()])
        add_assistant_message(messages, response)
        text = text_from_message(response)
        if text:
            print(f"  [Turn {turn}] {text}")
        if response.stop_reason != "tool_use":
            break
        print(f"  [Turn {turn}] Tool calls:")
        tool_results = run_tools(response)
        add_user_message(messages, tool_results)
    return messages


# === Test: Create main.py, then modify it ===
# Create a starter file
with open("main.py", "w") as f:
    f.write("def greeting():\n    pass\n")

print("=" * 60)
print("Test: Open main.py, add pi function, create test.py")
print("=" * 60)
messages = []
add_user_message(messages, (
    "Open the ./main.py file and replace the greeting function with a function "
    "to calculate pi to the 5th digit. Then create a ./test.py file to test it."
))
run_conversation(messages)

# Show results
print("\n=== main.py ===")
with open("main.py") as f:
    print(f.read())

if os.path.exists("test.py"):
    print("=== test.py ===")
    with open("test.py") as f:
        print(f.read())

# Cleanup
for f in ["main.py", "test.py"]:
    if os.path.exists(f):
        os.remove(f)
if os.path.exists(".backups"):
    shutil.rmtree(".backups")
