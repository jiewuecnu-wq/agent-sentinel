"""Alias module name expected by phase1_validate (re-exports phase1_case)."""

from phase1_case import (  # noqa: F401
    get_case,
    get_phase1_cases,
    list_case_ids,
    summarize_cases,
)

__all__ = [
    "get_case",
    "get_phase1_cases",
    "list_case_ids",
    "summarize_cases",
]
