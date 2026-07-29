"""Offline-first deterministic evaluation for recorded AI outputs."""

from .evaluator import evaluate
from .models import CandidateOutput, EvaluationCase, EvaluationReport

__all__ = ["CandidateOutput", "EvaluationCase", "EvaluationReport", "evaluate"]
__version__ = "0.1.0"
