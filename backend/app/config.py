"""Application configuration from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.env_bootstrap import bootstrap_env


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "SmartEd Support API"
    debug: bool = False
    enable_debug_routes: bool = Field(default=True, description="Expose /debug/env and /debug/provider")

    database_url: str = Field(
        default="sqlite:///./smarted_support.db",
        description="SQLAlchemy URL (SQLite for local dev; Postgres in Docker/production)",
    )

    jwt_secret: str = Field(default="change-me-in-production-use-openssl-rand", min_length=16)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    # --- LLM routing (Groq default; OpenAI optional) ---
    ai_provider: Literal["groq", "openai"] = "groq"
    groq_api_key: str = Field(default="", description="Groq API key (chat completions)")
    groq_model: str = Field(default="llama-3.3-70b-versatile", description="Groq model id")

    openai_api_key: str = Field(default="", description="Optional: OpenAI key for chat when AI_PROVIDER=openai")
    openai_chat_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"

    # --- Adaptive visual support engine (support-assets/) ---
    intent_flow_threshold: float = Field(
        default=0.38,
        ge=0.0,
        le=1.0,
        description="Minimum hybrid match score to trigger a visual walkthrough",
    )
    support_assets_dir: str = Field(
        default="",
        description="Root folder for dynamic support categories; blank = backend/support-assets",
    )
    support_index_cache_path: str = Field(
        default="./vector_db/support_flow_index.json",
        description="Cached catalog snapshot written after each index scan",
    )
    match_weight_keyword: float = Field(default=0.30, ge=0.0, le=1.0)
    match_weight_fuzzy: float = Field(default=0.25, ge=0.0, le=1.0)
    match_weight_tfidf: float = Field(default=0.25, ge=0.0, le=1.0)
    match_weight_embedding: float = Field(default=0.20, ge=0.0, le=1.0)

    public_base_url: str = Field(
        default="",
        description="Browser-facing origin for absolute image URLs (e.g. http://localhost:8080)",
    )

    flows_dir: str = Field(default="", description="Legacy JSON flows fallback; blank = backend/flows")
    demo_assets_dir: str = Field(
        default="",
        description="Legacy demo screenshots; auto-migrated into support-assets on scan",
    )

    chroma_persist_dir: str = "./vector_db/chroma_data"
    chroma_collection: str = "support_kb"

    uploads_dir: str = "./storage/uploads"
    visual_assets_dir: str = "./storage/visuals"

    cors_origins: str = "http://localhost:5173,http://localhost:3000,http://localhost:8080"

    rate_limit_default: str = "60/minute"

    escalation_webhook_url: str | None = None
    notify_email_from: str | None = None

    bootstrap_admin_email: str | None = Field(default=None)
    bootstrap_admin_password: str | None = Field(default=None)

    mock_student_enabled: bool = Field(
        default=True,
        description="Inject mock_student.json into AI prompts (disable in production LMS)",
    )
    mock_student_path: str = Field(
        default="",
        description="Path to mock student JSON; blank = backend/mock_student.json",
    )
    seed_demo_faqs: bool = Field(
        default=True,
        description="Seed policy FAQs on startup when the FAQ table is empty",
    )


@lru_cache
def get_settings() -> Settings:
    bootstrap_env()
    settings = Settings()
    return settings


def split_origins(origins: str) -> list[str]:
    return [o.strip() for o in origins.split(",") if o.strip()]
