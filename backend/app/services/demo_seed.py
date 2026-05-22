"""Seed demo policy FAQs for sandbox testing."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.config import Settings
from app.models import FAQ

logger = logging.getLogger("smarted.demo_seed")

DEMO_FAQS: list[dict[str, str]] = [
    {
        "category": "policy",
        "question": "What is your refund policy?",
        "answer": (
            "Refunds for paid courses may be requested within 14 days of purchase if less than "
            "20% of the course content has been completed. Submit a request via Settings → Billing. "
            "Approved refunds are processed within 5–10 business days. "
            "View the full policy: /demo/policy/refund"
        ),
    },
    {
        "category": "policy",
        "question": "How are assignments graded?",
        "answer": (
            "Assignments are graded on rubric criteria published with each task. "
            "Late submissions may receive a penalty unless you have an approved extension. "
            "Final grades appear under Progress and in each course gradebook. "
            "View details: /demo/policy/grading"
        ),
    },
    {
        "category": "policy",
        "question": "What is the attendance policy?",
        "answer": (
            "Live sessions and scheduled modules count toward attendance when you complete "
            "the linked activity or watch at least 80% of a live recording. "
            "Missing more than three consecutive weeks without activity may trigger a check-in email. "
            "View details: /demo/policy/attendance"
        ),
    },
]


def seed_demo_faqs(db: Session, settings: Settings) -> int:
    if not settings.seed_demo_faqs:
        return 0
    existing = db.query(FAQ).count()
    if existing > 0:
        return 0
    for row in DEMO_FAQS:
        db.add(
            FAQ(
                question=row["question"],
                answer=row["answer"],
                category=row.get("category"),
            )
        )
    db.commit()
    logger.info("[SEED] Inserted %d demo policy FAQs", len(DEMO_FAQS))
    return len(DEMO_FAQS)
