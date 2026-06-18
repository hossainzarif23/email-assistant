from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, field_validator, model_validator

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
OptionalNonEmptyStr = Annotated[str | None, StringConstraints(strip_whitespace=True, min_length=1)]


class PromptStrategy(str, Enum):
    STRUCTURED = "structured"
    FEW_SHOT = "few_shot"


class ModelProvider(str, Enum):
    GEMINI = "gemini"
    OPENAI = "openai"


class MetricName(str, Enum):
    FACT_COVERAGE = "fact_coverage"
    TONE_ALIGNMENT = "tone_alignment"
    PROFESSIONAL_STRUCTURE = "professional_structure"


class ReferenceEmail(BaseModel):
    subject: NonEmptyStr
    content: NonEmptyStr


class EmailScenario(BaseModel):
    id: NonEmptyStr
    intent: NonEmptyStr
    key_facts: list[str] = Field(min_length=1)
    tone: NonEmptyStr
    reference_email: ReferenceEmail
    sender: OptionalNonEmptyStr = None
    recipient: OptionalNonEmptyStr = None
    affiliation: OptionalNonEmptyStr = None

    @field_validator("key_facts")
    @classmethod
    def facts_must_be_non_empty_strings(cls, value: list[str]) -> list[str]:
        if any(not fact.strip() for fact in value):
            raise ValueError("key_facts must contain only non-empty strings")
        return value


class GeneratedEmail(BaseModel):
    subject: NonEmptyStr
    content: NonEmptyStr


class JudgeScore(BaseModel):
    score: int = Field(ge=0, le=5)
    reason: NonEmptyStr


class MetricResult(BaseModel):
    metric: MetricName
    score: int = Field(ge=0, le=5)
    reason: NonEmptyStr


class MetricRubricLevel(BaseModel):
    score: Annotated[int, Field(ge=0, le=5)]
    description: NonEmptyStr


class MetricDefinition(BaseModel):
    metric: MetricName
    title: NonEmptyStr
    description: NonEmptyStr
    rubric: list[MetricRubricLevel] = Field(min_length=6, max_length=6)

    @model_validator(mode="after")
    def rubric_must_cover_all_scores(self) -> MetricDefinition:
        expected_scores = list(range(6))
        actual_scores = [level.score for level in self.rubric]
        if actual_scores != expected_scores:
            raise ValueError("rubric must include exactly one level for each score from 0 to 5 in order")
        return self


class StrategyScenarioResult(BaseModel):
    scenario_id: NonEmptyStr
    generation_prompt: NonEmptyStr
    generated_email: GeneratedEmail
    metrics: list[MetricResult] = Field(min_length=3, max_length=3)

    @model_validator(mode="after")
    def metrics_must_have_unique_names(self) -> StrategyScenarioResult:
        seen: set[MetricName] = set()
        for metric_result in self.metrics:
            if metric_result.metric in seen:
                raise ValueError("metrics must not contain duplicate metric names")
            seen.add(metric_result.metric)
        return self


class StrategyAggregate(BaseModel):
    strategy: PromptStrategy
    metric_averages: dict[MetricName, Annotated[float, Field(ge=0, le=5)]]
    overall_average: Annotated[float, Field(ge=0, le=5)]

    @model_validator(mode="after")
    def metric_averages_must_cover_all_metrics(self) -> StrategyAggregate:
        if set(self.metric_averages.keys()) != set(MetricName):
            raise ValueError("metric_averages must include exactly one entry for each MetricName")
        return self


class EvaluationReport(BaseModel):
    source_file: Path
    metric_definitions: list[MetricDefinition] = Field(min_length=3, max_length=3)
    results: dict[PromptStrategy, list[StrategyScenarioResult]]
    aggregates: list[StrategyAggregate]
    winner: PromptStrategy | None = None

    @model_validator(mode="after")
    def metric_definitions_must_cover_all_metrics(self) -> EvaluationReport:
        if {definition.metric for definition in self.metric_definitions} != set(MetricName):
            raise ValueError("metric_definitions must include exactly one entry for each MetricName")
        return self
