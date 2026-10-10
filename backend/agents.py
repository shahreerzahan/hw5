"""The Campus Customs agent team: Boss, Inventory, Accounting, Facilities, Customer Service.

- Every agent runs on gpt-6-luna through Portkey.
- Shop data only comes from the MCP server (mcp_server/server.py). All agents
  share one MCP connection, and each only sees the MCP tools its role needs.
- Any agent can ask any other agent for help with the `ask_agent` tool (full
  connectivity), within the depth and budget limits in config.py.
- Every agent-loop step is appended to output/audit_trail.json.
"""

import json
import sys
import uuid
from contextlib import AsyncExitStack

from fastmcp.client.transports import StdioTransport
from openai import AsyncOpenAI
from portkey_ai import PORTKEY_GATEWAY_URL
from pydantic_ai import Agent, RunContext, UsageLimits
from pydantic_ai.exceptions import UsageLimitExceeded
from pydantic_ai.mcp import MCPToolset
from pydantic_ai.messages import RetryPromptPart, ToolCallPart, ToolReturnPart
from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings
from pydantic_ai.providers.openai import OpenAIProvider

from backend import audit, config
from backend.models import AGENT_NAMES, AgentName, AgentReport, RunBudget, TeamDeps, TicketDecision

# Which MCP tools each agent may call (least privilege). Only Accounting can
# queue money, only Customer Service can save customer drafts, and only the
# Boss can resolve a ticket.
AGENT_TOOLS: dict[AgentName, set[str]] = {
    "boss": {"get_desk_date", "list_tickets", "get_ticket", "list_pending_approvals", "resolve_ticket"},
    "inventory": {"get_desk_date", "get_ticket", "check_stock", "list_vendors", "get_vendor_invoices"},
    "accounting": {
        "get_desk_date", "get_ticket", "get_cash_balance", "list_pending_approvals", "get_invoice",
        "get_vendor_invoices", "get_lease", "check_stock", "prepare_payment", "prepare_purchase_order",
    },
    "facilities": {"get_desk_date", "get_ticket", "get_lease", "get_cash_balance", "list_pending_approvals"},
    "customer_service": {"get_desk_date", "get_ticket", "check_stock", "save_customer_draft"},
}

OUTPUT_TYPES = {name: AgentReport for name in AGENT_NAMES} | {"boss": TicketDecision}


def build_model() -> OpenAIResponsesModel:
    key = config.portkey_api_key()
    client = AsyncOpenAI(api_key=key, base_url=PORTKEY_GATEWAY_URL, default_headers={"x-portkey-api-key": key})
    return OpenAIResponsesModel(config.MODEL_NAME, provider=OpenAIProvider(openai_client=client))


def load_prompt(name: AgentName) -> str:
    return (config.PROMPTS_DIR / f"{name}.md").read_text()


class Team:
    """Holds the five agents and the shared MCP connection."""

    def __init__(self) -> None:
        self.mcp = MCPToolset(
            StdioTransport(command=sys.executable, args=[str(config.MCP_SERVER)], cwd=str(config.ROOT)),
            # Tool errors go back to the model as a retry prompt.
            tool_error_behavior="retry",
            max_retries=2,
        )
        model = build_model()
        settings = OpenAIResponsesModelSettings(
            openai_reasoning_effort=config.REASONING_EFFORT,
            parallel_tool_calls=False,  # one step at a time: simpler audit, no racing writes
        )
        self.agents: dict[AgentName, Agent] = {}
        for name in AGENT_NAMES:
            allowed = AGENT_TOOLS[name]
            agent = Agent(
                model,
                name=name,
                deps_type=TeamDeps,
                output_type=OUTPUT_TYPES[name],
                instructions=load_prompt(name),
                model_settings=settings,
                toolsets=[self.mcp.filtered(lambda ctx, tool, allowed=allowed: tool.name in allowed)],
                retries=2,
            )
            agent.tool(self._ask_agent_tool())
            self.agents[name] = agent

    async def __aenter__(self) -> "Team":
        self._stack = AsyncExitStack()
        await self._stack.enter_async_context(self.mcp)  # one MCP server process for the whole team
        return self

    async def __aexit__(self, *exc) -> None:
        await self._stack.aclose()

    # ------------------------------------------------------------ delegation

    def _ask_agent_tool(self):
        team = self

        async def ask_agent(ctx: RunContext[TeamDeps], agent: AgentName, request: str) -> str:
            """Ask another agent on the team for help and get its report back.

            agent: one of boss, inventory, accounting, facilities, customer_service.
            request: a specific question or task, with the ticket id and any facts
            (sku, size, qty, ids, amounts) the other agent needs.
            """
            deps = ctx.deps
            refusal = None
            if agent == deps.agent:
                refusal = "You can't delegate to yourself."
            elif agent in deps.chain:
                refusal = f"{agent} is already working on this request higher up the chain ({' -> '.join(deps.chain)}); answer with what you have."
            elif deps.depth + 1 > config.MAX_DELEGATION_DEPTH:
                refusal = f"Delegation depth limit ({config.MAX_DELEGATION_DEPTH}) reached; finish with what you have."
            elif deps.budget.agent_runs >= deps.budget.max_agent_runs:
                refusal = f"Agent-run budget for this ticket ({deps.budget.max_agent_runs}) is used up; finish with what you have."
            if refusal:
                audit.append({
                    "run_id": deps.run_id, "ticket_id": deps.ticket_id, "agent": deps.agent, "depth": deps.depth,
                    "step": "delegation_refused", "tool": "ask_agent", "args": audit.short({"agent": agent}),
                    "result": refusal, "stop_reason": "guardrail",
                })
                return f"REFUSED: {refusal}"

            sub_deps = TeamDeps(
                run_id=deps.run_id,
                ticket_id=deps.ticket_id,
                agent=agent,
                depth=deps.depth + 1,
                chain=(*deps.chain, deps.agent),
                budget=deps.budget,
            )
            prompt = f"Request from {deps.agent} about ticket {deps.ticket_id}:\n{request}"
            output = await team.run_agent(agent, prompt, sub_deps)
            if output is None:
                return f"{agent} could not finish (limit reached or error); see the audit trail."
            return output.model_dump_json()

        return ask_agent

    # ----------------------------------------------------------- agent loop

    async def run_agent(self, name: AgentName, prompt: str, deps: TeamDeps):
        """Run one agent to completion, writing each loop step to the audit trail."""
        deps.budget.agent_runs += 1
        base = {"run_id": deps.run_id, "ticket_id": deps.ticket_id, "agent": name, "depth": deps.depth}
        audit.append({**base, "step": "start", "tool": None, "args": audit.short(prompt), "result": None,
                      "stop_reason": None, "called_by": deps.chain[-1] if deps.chain else "user"})
        limits = UsageLimits(
            request_limit=config.MAX_STEPS_PER_AGENT,
            tool_calls_limit=config.MAX_TOOL_CALLS_PER_AGENT,
            total_tokens_limit=config.MAX_TOKENS_PER_AGENT,
        )
        pending: dict[str, ToolCallPart] = {}  # tool calls waiting for their result
        step = 0
        try:
            async with self.agents[name].iter(prompt, deps=deps, usage_limits=limits) as run:
                async for node in run:
                    if Agent.is_call_tools_node(node):
                        step += 1
                        response = node.model_response
                        calls = [p for p in response.parts if isinstance(p, ToolCallPart)]
                        for call in calls:
                            pending[call.tool_call_id] = call
                        if not calls:
                            audit.append({**base, "step": step, "tool": None, "args": None,
                                          "result": audit.short(response.text or ""),
                                          "stop_reason": response.finish_reason or "stop"})
                    elif Agent.is_model_request_node(node):
                        for part in node.request.parts:
                            if isinstance(part, (ToolReturnPart, RetryPromptPart)) and part.tool_call_id in pending:
                                call = pending.pop(part.tool_call_id)
                                is_retry = isinstance(part, RetryPromptPart)
                                audit.append({
                                    **base, "step": step, "tool": call.tool_name,
                                    "args": audit.short(call.args_as_dict()),
                                    "result": audit.short(part.model_response() if is_retry else part.content),
                                    "stop_reason": "tool_error_retry" if is_retry else "tool_call",
                                })
                    elif Agent.is_end_node(node):
                        output = node.data.output
                        for call in pending.values():  # the final_result output call
                            audit.append({**base, "step": step, "tool": call.tool_name,
                                          "args": audit.short(call.args_as_dict()), "result": "final output",
                                          "stop_reason": "final_output"})
                        audit.append({**base, "step": "end", "tool": None, "args": None,
                                      "result": audit.short(output.model_dump()), "stop_reason": "completed",
                                      "usage": {"requests": run.usage.requests,
                                                "input_tokens": run.usage.input_tokens,
                                                "output_tokens": run.usage.output_tokens}})
                        return output
        except UsageLimitExceeded as e:
            audit.append({**base, "step": "end", "tool": None, "args": None, "result": audit.short(str(e)),
                          "stop_reason": "usage_limit"})
        except Exception as e:  # keep the rest of the team running; the error is in the trail
            audit.append({**base, "step": "end", "tool": None, "args": None,
                          "result": audit.short(f"{type(e).__name__}: {e}"), "stop_reason": "error"})
        return None

    async def work_ticket(self, ticket_id: int) -> TicketDecision | None:
        """Hand one ticket to the Boss, who delegates and makes the final call."""
        deps = TeamDeps(
            run_id=uuid.uuid4().hex[:12],
            ticket_id=ticket_id,
            agent="boss",
            budget=RunBudget(max_agent_runs=config.MAX_AGENT_RUNS_PER_TICKET),
        )
        return await self.run_agent("boss", f"Work ticket {ticket_id}.", deps)


async def work_ticket(ticket_id: int) -> TicketDecision | None:
    async with Team() as team:
        return await team.work_ticket(ticket_id)


if __name__ == "__main__":
    import asyncio

    ticket = int(sys.argv[1]) if len(sys.argv) > 1 else 101
    result = asyncio.run(work_ticket(ticket))
    print(json.dumps(result.model_dump() if result else None, indent=2))
