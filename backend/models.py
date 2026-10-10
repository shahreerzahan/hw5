"""Data types shared by the Campus Customs agent team."""

from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, Field

AgentName = Literal["boss", "inventory", "accounting", "facilities", "customer_service"]

AGENT_NAMES: tuple[AgentName, ...] = ("boss", "inventory", "accounting", "facilities", "customer_service")


class ActionTaken(BaseModel):
    """Something an agent changed through an MCP write tool."""

    tool: str = Field(description="MCP tool that made the change, e.g. prepare_payment")
    detail: str = Field(description="What was done, with ids (request_id, draft_id, ticket_id)")


class AgentReport(BaseModel):
    """What a specialist agent hands back to whoever asked it for help."""

    agent: AgentName
    summary: str = Field(description="Two or three sentences answering the request")
    facts: list[str] = Field(
        default_factory=list,
        description="Key facts with their numbers, each taken from an MCP tool result",
    )
    actions_taken: list[ActionTaken] = Field(default_factory=list)
    needs_human_approval: list[str] = Field(
        default_factory=list,
        description="Items queued for a human, e.g. 'payment request 1: $840 invoice 501'",
    )
    blockers: list[str] = Field(default_factory=list, description="Anything that stops the work from finishing")


class TicketDecision(BaseModel):
    """The Boss's final call on one ticket."""

    ticket_id: int
    decision: str = Field(description="The final call in one or two sentences")
    reasoning: str = Field(description="Why, citing the facts the team found")
    agents_consulted: list[AgentName] = Field(default_factory=list)
    actions_taken: list[ActionTaken] = Field(default_factory=list)
    needs_human_approval: list[str] = Field(default_factory=list)
    customer_draft_id: int | None = Field(default=None, description="message_drafts id if a draft was saved")
    ticket_status: Literal["resolved", "open"] = Field(description="Status of the ticket after this run")


@dataclass
class RunBudget:
    """Shared across every agent working on one ticket, to cap total work."""

    max_agent_runs: int
    agent_runs: int = 0


@dataclass
class TeamDeps:
    """Passed to every agent run (and down through delegation)."""

    run_id: str
    ticket_id: int
    agent: AgentName
    depth: int = 0
    chain: tuple[AgentName, ...] = ()
    budget: RunBudget = field(default_factory=lambda: RunBudget(max_agent_runs=8))
