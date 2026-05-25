# Anthropic Academy — Building with the Claude API

Working through the [Anthropic Academy](https://academy.anthropic.com/) course "Building with the Claude API". Each lesson is a standalone .py file with a working example.

## Stack

- Python 3.9
- `anthropic` SDK
- `python-dotenv` for loading API key
- Virtual environment: `.venv/`

## File structure

Each lesson has both `.py` (run standalone) and `.ipynb` (interactive in VS Code) versions.

| # | File | Lesson |
|---|------|--------|
| 01 | `making_a_request` | First API request |
| 02 | `multi_turn` | Multi-turn conversations (message history) |
| 03 | `chatbot` | Interactive chat loop |
| 04 | `system_prompts` | System prompts (math tutor) |
| 05 | `system_prompts_exercise` | Comparing responses with/without system prompt |
| 06 | `temperature` | Temperature effect on creativity |
| 07 | `streaming` | Response streaming |
| 08 | `structured_data` | Structured data with prefill + stop sequence |
| 09 | `structured_data_exercise` | Prefill progression — clean commands |
| 10 | `prompt_evals` | Eval pipeline with model-based grading |

## Conventions

- Model: `claude-sonnet-4-0`
- API key in `.env` (do not commit)
- Each file is self-contained — run with `python3 <file>.py`

## Workflow

After completing each lesson:
1. Ask the user whether to commit and push now or wait
2. Only commit and push after explicit confirmation
3. This lets the user verify the code works before it goes to GitHub

Repo: https://github.com/Halvanhelv/anthropic-academy
