"""Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field, model_validator


class Annotation(BaseModel):
    kind: Literal["circle", "arrow", "highlight", "label"] = "highlight"
    x: float = Field(..., ge=0, le=1, description="Normalized left")
    y: float = Field(..., ge=0, le=1, description="Normalized top")
    w: float = Field(default=0.2, ge=0, le=1)
    h: float = Field(default=0.1, ge=0, le=1)
    label: str | None = None


class NavigationAction(BaseModel):
    label: str
    path: str


class VisualStep(BaseModel):
    step: int = 1
    title: str
    description: str
    image_url: str | None = None
    open_url: str | None = None
    auto_navigate: bool = False
    annotations: list[Annotation] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _coerce_image_field(cls, data: object) -> object:
        if isinstance(data, dict):
            if not data.get("image_url") and data.get("image"):
                data = {**data, "image_url": data["image"]}
        return data


class SupportTicketCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    email: EmailStr
    issue: str = Field(..., min_length=5, max_length=4000)
    session_key: str | None = Field(default=None, max_length=64)


class SupportTicketOut(BaseModel):
    id: str
    status: str
    message: str = "Your request has been submitted. Our team will follow up by email."


class LmsContextSnapshot(BaseModel):
    """Live LMS state injected by the frontend before each chat turn."""

    current_route: str | None = Field(default=None, max_length=512)
    current_page: str | None = Field(default=None, max_length=128)
    student_id: str | None = Field(default=None, max_length=64)
    student: dict[str, Any] | None = None
    courses: list[dict[str, Any]] = Field(default_factory=list)
    upcoming_exams: list[dict[str, Any]] = Field(default_factory=list)
    recent_activity: list[dict[str, Any]] = Field(default_factory=list)
    available_features: list[str] = Field(default_factory=list)
    available_routes: dict[str, str] = Field(default_factory=dict)
    certificates_count: int | None = None

    model_config = {"extra": "ignore"}


class ChatTurnRequest(BaseModel):
    session_key: str = Field(..., min_length=8, max_length=64)
    message: str = Field(..., min_length=1, max_length=8000)
    current_route: str | None = Field(
        default=None,
        max_length=512,
        description="Browser path the student is viewing in the demo LMS",
    )
    lms_context: LmsContextSnapshot | dict[str, Any] | None = Field(
        default=None,
        description="Authoritative mock LMS state for contextual AI (routes, enrollments, exams)",
    )


class ChatTurnResponse(BaseModel):
    reply: str
    intent: str
    confidence: float
    visual_steps: list[VisualStep] = Field(default_factory=list)
    suggested_replies: list[str] = Field(default_factory=list)
    escalate: bool = False
    follow_up_question: str | None = None
    citations: list[dict[str, str]] = Field(default_factory=list)

    response_source: Literal["support_flow", "llm", "fallback", "navigation"] = "llm"
    response_type: Literal["support_flow", "llm", "fallback", "navigation"] = "llm"
    response_mode: str | None = Field(
        default=None,
        description="Orchestrator mode: navigate_only, walkthrough, hybrid, conversational",
    )
    flow_title: str | None = None
    matched_flow_intent: str | None = None
    intent_match_confidence: float | None = None
    navigation_actions: list[NavigationAction] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _sync_response_type(cls, data: object) -> object:
        if isinstance(data, dict):
            src = data.get("response_source") or data.get("response_type") or "llm"
            data.setdefault("response_source", src)
            data.setdefault("response_type", src)
        return data


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AdminLogin(BaseModel):
    email: EmailStr
    password: str


class FAQCreate(BaseModel):
    question: str
    answer: str
    category: str | None = None


class FAQOut(BaseModel):
    id: str
    question: str
    answer: str
    category: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationSummary(BaseModel):
    id: str
    session_key: str
    title: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    meta: dict[str, Any] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class VisualGuideCreate(BaseModel):
    title: str
    description: str | None = None
    tags: str | None = None


class VisualGuideOut(BaseModel):
    id: str
    title: str
    description: str | None
    image_url: str
    tags: str | None
    created_at: datetime


class TicketOut(BaseModel):
    id: str
    conversation_id: str | None
    reason: str
    status: str
    confidence_at_escalation: float | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalyticsSummary(BaseModel):
    conversations_24h: int
    messages_24h: int
    tickets_open: int
    faq_count: int
    kb_documents: int
