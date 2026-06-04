# Anthropic Academy

Working through [Anthropic Academy](https://academy.anthropic.com/) courses on the Claude API and Claude Code.

## Structure

```
lessons/
├── 01_api_basics/           # Lessons 01–09: requests, conversations, streaming, structured data
├── 02_prompt_engineering/   # Lessons 10–16: evals, prompt techniques, exercises
├── 03_tool_use/             # Lessons 17–26: tool schemas, multi-turn, built-in tools
└── 04_advanced/             # Lessons 27–37: RAG, thinking, multimodal, caching, code execution

projects/
├── mcp_project/             # MCP server + client (FastMCP)
└── app_starter/             # App starter — tools, tests, hooks
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running lessons

```bash
cd lessons/01_api_basics
python3 01_making_a_request.py
```

Requires `ANTHROPIC_API_KEY` in `.env` at the project root.
