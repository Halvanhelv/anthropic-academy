from dotenv import load_dotenv
load_dotenv()

import json
import concurrent.futures
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
        "max_tokens": 4096,
        "messages": messages,
        "temperature": temperature,
        "stop_sequences": stop_sequences,
    }
    if system:
        params["system"] = system
    message = client.messages.create(**params)
    return message.content[0].text


# --- HTML Report ---
def generate_report(results):
    total = len(results)
    scores = [r["score"] for r in results]
    avg = mean(scores) if scores else 0
    passing = 100 * len([s for s in scores if s >= 7]) / total if total else 0

    rows = ""
    for r in results:
        inputs_html = "<br>".join(
            f"<strong>{k}:</strong> {v}"
            for k, v in r["test_case"]["prompt_inputs"].items()
        )
        criteria_html = "<br>• ".join(r["test_case"]["solution_criteria"])
        sc = r["score"]
        cls = "score-high" if sc >= 8 else ("score-low" if sc <= 5 else "score-medium")
        rows += f"""<tr>
            <td>{r["test_case"]["scenario"]}</td>
            <td>{inputs_html}</td>
            <td>• {criteria_html}</td>
            <td class="output"><pre>{r["output"]}</pre></td>
            <td><span class="score {cls}">{sc}</span></td>
            <td>{r["reasoning"]}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Prompt Evaluation Report</title>
<style>
body{{font-family:Arial,sans-serif;padding:20px;color:#333}}
.stats{{display:flex;gap:10px;margin-bottom:20px}}
.stat{{background:#fff;border-radius:5px;padding:15px;box-shadow:0 2px 5px rgba(0,0,0,.1);flex:1}}
.stat-val{{font-size:24px;font-weight:bold;margin-top:5px}}
table{{width:100%;border-collapse:collapse;margin-top:20px}}
th{{background:#4a4a4a;color:white;text-align:left;padding:12px}}
td{{padding:10px;border-bottom:1px solid #ddd;vertical-align:top;width:20%}}
tr:nth-child(even){{background:#f9f9f9}}
.output pre{{background:#f5f5f5;border:1px solid #ddd;border-radius:4px;padding:10px;font-size:14px;white-space:pre-wrap;word-wrap:break-word}}
.score{{font-weight:bold;padding:5px 10px;border-radius:3px}}
.score-high{{background:#c8e6c9;color:#2e7d32}}
.score-medium{{background:#fff9c4;color:#f57f17}}
.score-low{{background:#ffcdd2;color:#c62828}}
</style></head><body>
<h1>Prompt Evaluation Report</h1>
<div class="stats">
<div class="stat"><div>Total Test Cases</div><div class="stat-val">{total}</div></div>
<div class="stat"><div>Average Score</div><div class="stat-val">{avg:.1f} / 10</div></div>
<div class="stat"><div>Pass Rate (≥7)</div><div class="stat-val">{passing:.1f}%</div></div>
</div>
<table><thead><tr><th>Scenario</th><th>Prompt Inputs</th><th>Solution Criteria</th><th>Output</th><th>Score</th><th>Reasoning</th></tr></thead>
<tbody>{rows}</tbody></table></body></html>"""


# --- PromptEvaluator ---
class PromptEvaluator:
    def __init__(self, max_concurrent_tasks=1):
        self.max_concurrent_tasks = max_concurrent_tasks

    def render(self, template, variables):
        result = template
        for k, v in variables.items():
            result = result.replace("{" + k + "}", str(v))
        return result.replace("{{", "{").replace("}}", "}")

    def generate_dataset(self, task_description, prompt_inputs_spec, num_cases=3, output_file="dataset.json"):
        ideas = self._generate_ideas(task_description, prompt_inputs_spec, num_cases)
        dataset = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_concurrent_tasks) as ex:
            futures = {
                ex.submit(self._generate_test_case, task_description, idea, prompt_inputs_spec): idea
                for idea in ideas
            }
            for f in concurrent.futures.as_completed(futures):
                dataset.append(f.result())
        with open(output_file, "w") as f:
            json.dump(dataset, f, indent=2)
        print(f"Generated {len(dataset)} test cases.")
        return dataset

    def _generate_ideas(self, task_description, prompt_inputs_spec, num_cases):
        spec_str = ", ".join(f'"{k}": {v}' for k, v in prompt_inputs_spec.items())
        prompt = f"""
Generate {num_cases} unique, diverse ideas for testing a prompt that accomplishes this task:

<task_description>
{task_description}
</task_description>

The prompt receives these inputs: {spec_str}

Output as JSON array of brief descriptions.
"""
        messages = []
        add_user_message(messages, prompt)
        add_assistant_message(messages, "```json")
        return json.loads(chat(messages, stop_sequences=["```"]))

    def _generate_test_case(self, task_description, idea, prompt_inputs_spec):
        keys = ", ".join(f'"{k}"' for k in prompt_inputs_spec.keys())
        example = "\n".join(f'    "{k}": "EXAMPLE_VALUE",' for k in prompt_inputs_spec.keys())
        prompt = f"""
Generate a single test case for evaluating a prompt.

Task: {task_description}
Idea: {idea}
Allowed input keys: {keys}

Output as JSON:
```json
{{
    "prompt_inputs": {{
{example}
    }},
    "solution_criteria": ["criterion 1", "criterion 2"]
}}
```

Requirements:
- Use ONLY the allowed input keys
- Include 1-4 concise, measurable solution criteria
- Keep it realistic and focused
"""
        messages = []
        add_user_message(messages, prompt)
        add_assistant_message(messages, "```json")
        tc = json.loads(chat(messages, stop_sequences=["```"], temperature=0.7))
        tc["task_description"] = task_description
        tc["scenario"] = idea
        return tc

    def run_evaluation(self, run_prompt_function, dataset_file, extra_criteria=None,
                       json_output_file="13_being_specific_output/output.json", html_output_file="13_being_specific_output/output.html"):
        with open(dataset_file) as f:
            dataset = json.load(f)
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_concurrent_tasks) as ex:
            futures = {
                ex.submit(self._run_and_grade, tc, run_prompt_function, extra_criteria): tc
                for tc in dataset
            }
            for f in concurrent.futures.as_completed(futures):
                results.append(f.result())
        avg = mean([r["score"] for r in results])
        passing = sum(1 for r in results if r["score"] >= 7)
        print(f"Average score: {avg:.1f}")
        print(f"Pass rate (>=7): {passing}/{len(results)}")
        with open(json_output_file, "w") as f:
            json.dump(results, f, indent=2)
        with open(html_output_file, "w") as f:
            f.write(generate_report(results))
        print(f"Report saved to {html_output_file}")
        return results

    def _run_and_grade(self, test_case, run_prompt_function, extra_criteria):
        output = run_prompt_function(test_case["prompt_inputs"])
        grade = self._grade(test_case, output, extra_criteria)
        return {
            "output": output,
            "test_case": test_case,
            "score": grade["score"],
            "reasoning": grade["reasoning"],
        }

    def _grade(self, test_case, output, extra_criteria):
        inputs_str = "\n".join(f'{k}: {v}' for k, v in test_case["prompt_inputs"].items())
        criteria_str = "\n".join(test_case["solution_criteria"])
        extra = ""
        if extra_criteria:
            extra = f"""
Mandatory Requirements - ANY VIOLATION MEANS AUTOMATIC FAILURE (score of 3 or lower):
<extra_criteria>
{extra_criteria}
</extra_criteria>
"""
        prompt = f"""
Evaluate this AI-generated solution with EXTREME RIGOR.

Original task:
<task>{test_case["task_description"]}</task>

Inputs:
<inputs>{inputs_str}</inputs>

Solution:
<solution>{output}</solution>

Criteria:
<criteria>{criteria_str}</criteria>

{extra}

Scoring: 1-3 fails mandatory, 4-6 meets mandatory but has issues, 7-8 good with minor issues, 9-10 meets all criteria.

Provide JSON with: "strengths" (array), "weaknesses" (array), "reasoning" (string), "score" (1-10).
"""
        messages = []
        add_user_message(messages, prompt)
        add_assistant_message(messages, "```json")
        return json.loads(chat(messages, stop_sequences=["```"], temperature=0.0))


# --- Run evaluation ---
evaluator = PromptEvaluator(max_concurrent_tasks=1)

dataset = evaluator.generate_dataset(
    task_description="Write a compact, concise 1 day meal plan for a single athlete",
    prompt_inputs_spec={
        "height": "Athlete's height in cm",
        "weight": "Athlete's weight in kg",
        "goal": "Goal of the athlete",
        "restrictions": "Dietary restrictions of the athlete",
    },
    output_file="13_being_specific_output/meal_plan_dataset.json",
    num_cases=3,
)


def run_prompt(prompt_inputs):
    prompt = f"""
Generate a one-day meal plan for an athlete that meets their dietary restrictions.

- Height: {prompt_inputs["height"]}
- Weight: {prompt_inputs["weight"]}
- Goal: {prompt_inputs["goal"]}
- Dietary restrictions: {prompt_inputs["restrictions"]}

Guidelines:
1. Include accurate daily calorie amount
2. Show protein, fat, and carb amounts
3. Specify when to eat each meal
4. Use only foods that fit restrictions
5. List all portion sizes in grams
6. Keep budget-friendly if mentioned
"""
    messages = []
    add_user_message(messages, prompt)
    return chat(messages)


results = evaluator.run_evaluation(
    run_prompt_function=run_prompt,
    dataset_file="13_being_specific_output/meal_plan_dataset.json",
    extra_criteria="""
The output should include:
- Daily caloric total
- Macronutrient breakdown
- Meals with exact foods, portions, and timing
""",
)
