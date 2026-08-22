from dataclasses import dataclass, field


@dataclass
class EditorialNote:
    category: str
    severity: str
    section: str
    message: str
    suggestion: str
    quote: str = ""


@dataclass
class StructuralValidation:
    """LLM verdict on a single deterministic structural check result."""
    rule_id: str
    verdict: str  # "confirm" | "false_positive"
    reason: str


@dataclass
class EditorialReviewResult:
    notes: list[EditorialNote]
    structural_validations: list[StructuralValidation] = field(default_factory=list)
    model_used: str = ""
    token_usage: dict = field(default_factory=dict)
