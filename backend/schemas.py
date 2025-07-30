from __future__ import annotations

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Question(BaseModel):
    """A follow‑up question presented to the user.

    Attributes:
        id: Machine‑readable identifier for the question used when submitting answers.
        text: Human readable question text.
        type: Input type (e.g. "text", "number", "select").
        options: Optional list of selection options when type is select.
    """
    id: str
    text: str
    type: str = Field(default="text")
    options: Optional[List[str]] = None


class ScanResult(BaseModel):
    """Response returned from the /scan endpoint.

    Contains detected issues and a tailored follow‑up questionnaire.
    """
    issues: List[str]
    questions: List[Question]


class RecommendRequest(BaseModel):
    """Request body for the /recommend endpoint.

    Includes the scan result (issues) and user answers to follow‑up questions.
    """
    issues: List[str]
    answers: Dict[str, Any]
