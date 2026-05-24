# Anthropic Academy — Building with the Claude API

Working through the [Anthropic Academy](https://academy.anthropic.com/) course "Building with the Claude API". Each lesson is a standalone .py file with a working example.

## Stack

- Python 3.9
- `anthropic` SDK
- `python-dotenv` for loading API key
- Virtual environment: `.venv/`

## File structure

| File | Lesson |
|------|--------|
| `making_a_request.py` | First API request |
| `multi_turn.py` | Multi-turn conversations (message history) |
| `chatbot.py` | Interactive chat loop |
| `system_prompts.py` | System prompts (math tutor) |
| `system_prompts_exercise.py` | Comparing responses with/without system prompt |
| `temperature.py` | Temperature effect on creativity |
| `streaming.py` | Response streaming |

## Conventions

- Model: `claude-sonnet-4-6`
- API key in `.env` (do not commit)
- Each file is self-contained — run with `python3 <file>.py`
