from dotenv import load_dotenv
load_dotenv()

import json
from anthropic import Anthropic

client = Anthropic()
model = "claude-sonnet-4-0"


def add_user_message(messages, text):
    messages.append({"role": "user", "content": text})


def add_assistant_message(messages, text):
    messages.append({"role": "assistant", "content": text})


def chat(messages, system=None, temperature=1.0, stop_sequences=[]):
    params = {
        "model": model,
        "max_tokens": 1000,
        "messages": messages,
        "temperature": temperature,
    }
    if system:
        params["system"] = system
    if stop_sequences:
        params["stop_sequences"] = stop_sequences
    message = client.messages.create(**params)
    return message.content[0].text


def generate_dataset():
    prompt = """
Generate an evaluation dataset for a prompt evaluation. The dataset will be used to evaluate prompts that generate Python, JSON, or Regex specifically for AWS-related tasks. Generate an array of JSON objects, each representing task that requires Python, JSON, or a Regex to complete.

Example output:
```json
[
  {
    "task": "Description of task",
  },
  ...additional
]
```

* Focus on tasks that can be solved by writing a single Python function, a single JSON object, or a single regex
* Focus on tasks that do not require writing much code

Please generate 3 objects.
"""
    messages = []
    add_user_message(messages, prompt)
    add_assistant_message(messages, "```json")
    text = chat(messages, stop_sequences=["```"])
    return json.loads(text)


# --- Step 1: Generate dataset ---
dataset = generate_dataset()
with open("dataset.json", "w") as f:
    json.dump(dataset, f, indent=2)
print("Dataset generated and saved.\n")


# --- Step 2: Eval pipeline ---
def run_prompt(test_case):
    prompt = f"""
Please solve the following task:

{test_case["task"]}
"""
    messages = []
    add_user_message(messages, prompt)
    return chat(messages)


def run_test_case(test_case):
    output = run_prompt(test_case)
    score = 10  # TODO: replace with real grading
    return {
        "output": output,
        "test_case": test_case,
        "score": score,
    }


def run_eval(dataset):
    results = []
    for test_case in dataset:
        result = run_test_case(test_case)
        results.append(result)
    return results


with open("dataset.json", "r") as f:
    dataset = json.load(f)

results = run_eval(dataset)
print(json.dumps(results, indent=2))
