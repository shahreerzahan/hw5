"""Settings: paths, the one allowed model, and limits that keep token use down."""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

PROMPTS_DIR = ROOT / "backend" / "prompts"
MCP_SERVER = ROOT / "mcp_server" / "server.py"
AUDIT_TRAIL = ROOT / "output" / "audit_trail.json"

# Every agent uses gpt-6-luna through Portkey, and nothing else.
MODEL_NAME = "gpt-6-luna"
if os.getenv("MODEL_NAME", MODEL_NAME) != MODEL_NAME:
    raise RuntimeError(f"MODEL_NAME must be {MODEL_NAME!r}; this project only uses gpt-6-luna.")


def portkey_api_key() -> str:
    key = os.getenv("PORTKEY_API_KEY")
    if not key:
        raise RuntimeError("PORTKEY_API_KEY is not set in .env")
    return key


# Token and loop limits.
REASONING_EFFORT = "low"      # reasoning tokens per model call
MAX_STEPS_PER_AGENT = 10      # model requests per agent run
MAX_TOOL_CALLS_PER_AGENT = 15  # tool calls per agent run
MAX_TOKENS_PER_AGENT = 80_000  # total tokens per agent run
MAX_DELEGATION_DEPTH = 2      # boss -> specialist -> specialist, no deeper
MAX_AGENT_RUNS_PER_TICKET = 8  # all agent runs (boss + delegations) for one ticket
