from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.types import Command, interrupt
from pydantic import BaseModel

from app.models import ChiefOfStaffOutput, ExecutionResult, SpecialistDraft, WrapupSummary

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "business_state.json"
DECISION_LOG = Path(__file__).resolve().parent.parent / "knowledge" / "decision_log.md"

RISK_GATES = {
    "external_message",
    "price_change",
    "spend",
    "site_change",
    "supplier_commitment",
}


class AgentState(BaseModel):
    user_input: str
    intake: Dict[str, Any] = {}
    plan_json: str | None = None
    specialist_json: List[str] = []
    approval_payload: Dict[str, Any] | None = None
    approval_response: str | None = None
    approved: bool = False
    execution_log: List[str] = []
    wrapup_json: str | None = None


def _json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _load_business_state() -> Dict[str, Any]:
    if DATA_PATH.exists():
        return json.loads(DATA_PATH.read_text())
    return {}


def _maybe_use_llm() -> ChatOpenAI | None:
    try:
        return ChatOpenAI(model="gpt-4o-mini", temperature=0)
    except Exception:
        return None


def intake_node(state: AgentState) -> Dict[str, Any]:
    business_state = _load_business_state()
    intake = {
        "timestamp": datetime.utcnow().isoformat(),
        "request": state.user_input,
        "business_state": business_state,
    }
    return {"intake": intake}


def plan_node(state: AgentState) -> Dict[str, Any]:
    request = state.intake.get("request", state.user_input)
    llm = _maybe_use_llm()

    if llm:
        prompt = (
            "You are ChiefOfStaff. Produce STRICT JSON with keys: intent, constraints, "
            "missing_info, plan, proposed_actions, decisions_needed. "
            "proposed_actions items require action and risk_type. "
            f"User request: {request}"
        )
        response = llm.invoke(prompt)
        raw = response.content
        try:
            parsed = json.loads(raw)
            output = ChiefOfStaffOutput.model_validate(parsed)
        except Exception:
            output = ChiefOfStaffOutput(
                intent="Operational plan",
                constraints=["Dry-run only"],
                missing_info=[],
                plan=["Review request", "Draft actions"],
                proposed_actions=[{"action": "Draft outreach email", "risk_type": "external_message"}],
                decisions_needed=["Confirm go-live timing"],
            )
    else:
        output = ChiefOfStaffOutput(
            intent=f"Support request: {request}",
            constraints=["Dry-run only"],
            missing_info=["Target audience"],
            plan=[
                "Clarify goals and constraints",
                "Draft channel-specific actions",
                "Collect approvals for risky actions",
            ],
            proposed_actions=[
                {"action": "Draft customer outreach message", "risk_type": "external_message"},
                {"action": "Evaluate pricing update", "risk_type": "price_change"},
            ],
            decisions_needed=["Approval for outreach and pricing review"],
        )

    plan_json = _json_dumps(output.model_dump())
    return {"plan_json": plan_json}


def specialists_node(state: AgentState) -> Dict[str, Any]:
    drafts = []
    roles = [
        "ExecutiveAssistant",
        "Webmaster",
        "CreativeDirector",
        "SupplyManager",
    ]
    for role in roles:
        draft = SpecialistDraft(
            role=role,
            summary=f"{role} prepared a dry-run draft for: {state.user_input}",
            draft_steps=[
                "Review constraints",
                "Draft recommended actions",
                "Flag risks for approval",
            ],
            risks=["external_message", "site_change"],
        )
        drafts.append(_json_dumps(draft.model_dump()))
    return {"specialist_json": drafts}


def _collect_risks(plan_json: str | None, specialist_json: List[str]) -> List[str]:
    risks: List[str] = []
    if plan_json:
        try:
            parsed = json.loads(plan_json)
            for item in parsed.get("proposed_actions", []):
                risk_type = item.get("risk_type")
                if risk_type:
                    risks.append(risk_type)
        except Exception:
            pass
    for draft in specialist_json:
        try:
            parsed = json.loads(draft)
            risks.extend(parsed.get("risks", []))
        except Exception:
            continue
    return sorted(set(risks))


def approval_interrupt_node(state: AgentState) -> Dict[str, Any]:
    risks = _collect_risks(state.plan_json, state.specialist_json)
    gated = [risk for risk in risks if risk in RISK_GATES]
    if not gated:
        return {"approved": True}
    payload = {
        "gated_risks": gated,
        "summary": "Approval required for actions touching sensitive areas.",
        "plan": json.loads(state.plan_json) if state.plan_json else {},
        "specialists": [json.loads(draft) for draft in state.specialist_json],
    }
    response = interrupt(payload)
    approved = str(response).strip().lower() in {"y", "yes", "approve", "approved"}
    return {
        "approval_payload": payload,
        "approval_response": str(response),
        "approved": approved,
    }


def execute_node(state: AgentState) -> Dict[str, Any]:
    execution_log = [
        "Dry-run execution only. No external systems contacted.",
        f"Approved: {state.approved}",
    ]
    if state.plan_json:
        execution_log.append(f"Plan JSON: {state.plan_json}")
    for draft in state.specialist_json:
        execution_log.append(f"Specialist draft: {draft}")
    result = ExecutionResult(
        dry_run_log=execution_log,
        approvals=[state.approval_response] if state.approval_response else [],
    )
    return {"execution_log": result.dry_run_log}


def wrapup_node(state: AgentState) -> Dict[str, Any]:
    summary = WrapupSummary(
        intent=json.loads(state.plan_json or "{}").get("intent", ""),
        approved=state.approved,
        decisions=json.loads(state.plan_json or "{}").get("decisions_needed", []),
        execution_log=state.execution_log,
        next_steps=["Collect missing info", "Schedule follow-up"],
    )
    wrapup_json = _json_dumps(summary.model_dump())
    DECISION_LOG.parent.mkdir(parents=True, exist_ok=True)
    with DECISION_LOG.open("a", encoding="utf-8") as handle:
        handle.write("\n```json\n")
        handle.write(wrapup_json)
        handle.write("\n```\n")
    return {"wrapup_json": wrapup_json}


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)
    graph.add_node("intake", intake_node)
    graph.add_node("plan", plan_node)
    graph.add_node("specialists", specialists_node)
    graph.add_node("approval_interrupt", approval_interrupt_node)
    graph.add_node("execute", execute_node)
    graph.add_node("wrapup", wrapup_node)

    graph.set_entry_point("intake")
    graph.add_edge("intake", "plan")
    graph.add_edge("plan", "specialists")
    graph.add_edge("specialists", "approval_interrupt")
    graph.add_edge("approval_interrupt", "execute")
    graph.add_edge("execute", "wrapup")
    graph.add_edge("wrapup", END)
    return graph


def build_app() -> Any:
    graph = build_graph()
    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)


def resume_command(payload: str) -> Command:
    return Command(resume=payload)
