from dotenv import load_dotenv
load_dotenv()

import json
from statistics import mean
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


def grade_by_model(test_case, output):
    eval_prompt = f"""
You are an expert code reviewer. Evaluate this AI-generated solution.

Task: {test_case["task"]}
Solution: {output}

Provide your evaluation as a structured JSON object with:
- "strengths": An array of 1-3 key strengths
- "weaknesses": An array of 1-3 key areas for improvement
- "reasoning": A concise explanation of your assessment
- "score": A number between 1-10
"""
    messages = []
    add_user_message(messages, eval_prompt)
    add_assistant_message(messages, "```json")
    eval_text = chat(messages, stop_sequences=["```"])
    return json.loads(eval_text)


def run_test_case(test_case):
    output = run_prompt(test_case)
    model_grade = grade_by_model(test_case, output)
    return {
        "output": output,
        "test_case": test_case,
        "score": model_grade["score"],
        "reasoning": model_grade["reasoning"],
    }


def run_eval(dataset):
    results = []
    for test_case in dataset:
        result = run_test_case(test_case)
        results.append(result)
    average_score = mean([r["score"] for r in results])
    print(f"Average score: {average_score}")
    return results


with open("dataset.json", "r") as f:
    dataset = json.load(f)

results = run_eval(dataset)
for r in results:
    print(f"\nTask: {r['test_case']['task'][:60]}...")
    print(f"Score: {r['score']}")
    print(f"Reasoning: {r['reasoning']}")
