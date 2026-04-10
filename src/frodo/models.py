from dataclasses import dataclass, field


@dataclass
class NewsBrief:
    """Structured fact extraction from search results, used by the Writer."""

    headline: str
    key_facts: list[str]
    outlets: list[str]
    korean_angle: str
    angle_strength: str  # "strong" | "medium" | "weak"
    source_url: str | None = None


@dataclass
class EditorReview:
    passed: bool
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


@dataclass
class FactCheckResult:
    passed: bool
    verified: list[str] = field(default_factory=list)
    unverified: list[str] = field(default_factory=list)
    contradicted: list[str] = field(default_factory=list)


@dataclass
class PostResult:
    topic: str
    brief: NewsBrief | None
    text: str
    revisions: int
    final_issues: list[str]
