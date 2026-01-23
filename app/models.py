from __future__ import annotations

from pydantic import BaseModel, Field


class ProposedAction(BaseModel):
    action: str
    risk_type: str | None = None


class ChiefOfStaffOutput(BaseModel):
    intent: str
    constraints: list[str] = Field(default_factory=list)
    missing_info: list[str] = Field(default_factory=list)
    plan: list[str] = Field(default_factory=list)
    proposed_actions: list[ProposedAction] = Field(default_factory=list)
    decisions_needed: list[str] = Field(default_factory=list)


class SpecialistDraft(BaseModel):
    role: str
    summary: str
    draft_steps: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


class ExecutionResult(BaseModel):
    dry_run_log: list[str] = Field(default_factory=list)
    approvals: list[str] = Field(default_factory=list)


class WrapupSummary(BaseModel):
    intent: str
    approved: bool
    decisions: list[str] = Field(default_factory=list)
    execution_log: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
