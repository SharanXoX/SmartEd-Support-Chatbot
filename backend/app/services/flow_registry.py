"""Backward-compatible exports — dynamic discovery lives in support_indexer."""

from app.services.support_indexer import (
    FlowMatch,
    FlowStepDefinition,
    SupportFlowDefinition,
    get_support_indexer,
    invalidate_flow_cache,
    list_flows,
    match_support_flow,
)

__all__ = [
    "FlowMatch",
    "FlowStepDefinition",
    "SupportFlowDefinition",
    "get_support_indexer",
    "invalidate_flow_cache",
    "list_flows",
    "match_support_flow",
]
