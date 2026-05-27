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
| 11 | `prompt_engineering` | Prompt engineering baseline (meal plan) |
| 12 | `being_clear_and_direct` | Clear and direct prompts (~5.0) |
| 13 | `being_specific` | Specific guidelines (~5.3) |
| 14 | `xml_tags` | Structure with XML tags (~5.7) |
| 15 | `providing_examples` | One-shot prompting (~7.7) |
| 16 | `exercise_prompting` | All prompt techniques combined (~8.2) |
| 17 | `tool_functions` | Tool use — writing tool functions |
| 18 | `tool_schemas` | Tool use — JSON schemas for tools |
| 19 | `handling_message_blocks` | Tool use — multi-block responses |
| 20 | `sending_tool_results` | Tool use — full cycle with tool_result |
| 21 | `multi_turn_tools` | Tool use — multi-turn conversation loop |
| 22 | `implementing_multiple_turns` | Tool use — run_tools + error handling |
| 23 | `using_multiple_tools` | Tool use — 3 tools + set_reminder |
| 24 | `fine_grained_tool_calling` | Tool use — streaming + fine-grained |
| 25 | `text_editor_tool` | Tool use — built-in text editor tool |
| 26 | `web_search_tool` | Tool use — built-in web search tool |

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
