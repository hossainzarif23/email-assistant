from collections.abc import Callable

import pytest
from pydantic import BaseModel, ValidationError

from src.models import (
    EvaluationReport,
    EmailScenario,
    GeneratedEmail,
    JudgeScore,
    MetricName,
    MetricResult,
    MetricDefinition,
    MetricRubricLevel,
    ModelProvider,
    PromptStrategy,
    ReferenceEmail,
    ScenarioEvaluationResult,
)


def test_scenario_accepts_optional_identity_fields() -> None:
    scenario = EmailScenario(
        id="demo",
        intent="Request an updated proposal",
        key_facts=["Need the proposal by Friday", "Budget is $12,000"],
        tone="polite and concise",
        reference_email=ReferenceEmail(subject="Proposal Update", content="Dear Alex,\n\nPlease send the update.\n\nBest,\nSam"),
    )

    assert scenario.sender is None
    assert scenario.recipient is None
    assert scenario.affiliation is None


def test_scenario_requires_at_least_one_fact() -> None:
    with pytest.raises(ValidationError):
        EmailScenario(
            id="bad",
            intent="Request an updated proposal",
            key_facts=[],
            tone="polite",
            reference_email=ReferenceEmail(subject="Proposal", content="Hello"),
        )


def test_scenario_rejects_whitespace_only_key_fact() -> None:
    with pytest.raises(ValidationError):
        EmailScenario(
            id="bad",
            intent="Request an updated proposal",
            key_facts=["   "],
            tone="polite",
            reference_email=ReferenceEmail(subject="Proposal", content="Hello"),
        )


def test_generated_email_requires_non_empty_subject_and_content() -> None:
    email = GeneratedEmail(subject="Next Steps", content="Hi Alex,\n\nPlease confirm.\n\nBest,\nSam")

    assert email.subject == "Next Steps"
    assert "Please confirm" in email.content


@pytest.mark.parametrize(
    ("factory", "field_name"),
    [
        (
            lambda: EmailScenario(
                id="demo",
                intent="  ",
                key_facts=["Need the proposal by Friday"],
                tone="polite",
                reference_email=ReferenceEmail(subject="Proposal Update", content="Dear Alex,\n\nPlease send the update.\n\nBest,\nSam"),
            ),
            "intent",
        ),
        (
            lambda: EmailScenario(
                id="  ",
                intent="Request an updated proposal",
                key_facts=["Need the proposal by Friday"],
                tone="polite",
                reference_email=ReferenceEmail(subject="Proposal Update", content="Dear Alex,\n\nPlease send the update.\n\nBest,\nSam"),
            ),
            "id",
        ),
        (
            lambda: ReferenceEmail(subject="  ", content="Dear Alex,\n\nPlease send the update.\n\nBest,\nSam"),
            "subject",
        ),
        (
            lambda: ReferenceEmail(subject="Proposal Update", content="  "),
            "content",
        ),
        (
            lambda: GeneratedEmail(subject="  ", content="Hi Alex,\n\nPlease confirm.\n\nBest,\nSam"),
            "subject",
        ),
        (
            lambda: GeneratedEmail(subject="Next Steps", content="  "),
            "content",
        ),
        (
            lambda: JudgeScore(score=5, reason="  "),
            "reason",
        ),
        (
            lambda: EmailScenario(
                id="demo",
                intent="Request an updated proposal",
                key_facts=["Need the proposal by Friday"],
                tone="  ",
                reference_email=ReferenceEmail(subject="Proposal Update", content="Dear Alex,\n\nPlease send the update.\n\nBest,\nSam"),
            ),
            "tone",
        ),
    ],
)
def test_whitespace_only_text_fields_are_rejected(factory: Callable[[], BaseModel], field_name: str) -> None:
    with pytest.raises(ValidationError) as exc_info:
        factory()

    assert any(error["loc"] == (field_name,) and error["type"] == "string_too_short" for error in exc_info.value.errors())


def test_judge_score_is_integer_between_zero_and_five() -> None:
    assert JudgeScore(score=5, reason="All required facts are present.").score == 5

    with pytest.raises(ValidationError) as exc_info:
        JudgeScore(score=6, reason="Too high.")

    assert exc_info.value.errors()[0]["loc"] == ("score",)
    assert exc_info.value.errors()[0]["type"] == "less_than_equal"


def test_strategy_scenario_result_requires_exactly_three_unique_metrics() -> None:
    metrics = [
        MetricResult(metric=MetricName.FACT_COVERAGE, score=5, reason="Covered."),
        MetricResult(metric=MetricName.TONE_ALIGNMENT, score=4, reason="Aligned."),
        MetricResult(metric=MetricName.FACT_COVERAGE, score=3, reason="Duplicate."),
    ]

    with pytest.raises(ValidationError) as exc_info:
        ScenarioEvaluationResult(
            scenario_id="scenario-1",
            metrics=metrics,
        )

    error = exc_info.value.errors()[0]
    assert error["loc"] == ()
    assert error["type"] == "value_error"


@pytest.mark.parametrize("metrics", [[], [MetricResult(metric=MetricName.FACT_COVERAGE, score=5, reason="Covered.")]])
def test_strategy_scenario_result_rejects_wrong_metric_count(metrics: list[MetricResult]) -> None:
    with pytest.raises(ValidationError) as exc_info:
        ScenarioEvaluationResult(
            scenario_id="scenario-1",
            metrics=metrics,
        )

    error = exc_info.value.errors()[0]
    assert error["loc"] == ("metrics",)
    assert error["type"] == "too_short"


def test_evaluation_report_requires_metric_average_for_each_metric() -> None:
    with pytest.raises(ValidationError) as exc_info:
        EvaluationReport(
            source_file="data/scenarios.json",
            provider=ModelProvider.OPENAI,
            strategy=PromptStrategy.FEW_SHOT,
            metric_definitions=[
                MetricDefinition(
                    metric=MetricName.FACT_COVERAGE,
                    definition="Definition",
                    rubric=[
                        MetricRubricLevel(score=0, description="zero"),
                        MetricRubricLevel(score=1, description="one"),
                        MetricRubricLevel(score=2, description="two"),
                        MetricRubricLevel(score=3, description="three"),
                        MetricRubricLevel(score=4, description="four"),
                        MetricRubricLevel(score=5, description="five"),
                    ],
                ),
                MetricDefinition(
                    metric=MetricName.TONE_ALIGNMENT,
                    definition="Definition",
                    rubric=[
                        MetricRubricLevel(score=0, description="zero"),
                        MetricRubricLevel(score=1, description="one"),
                        MetricRubricLevel(score=2, description="two"),
                        MetricRubricLevel(score=3, description="three"),
                        MetricRubricLevel(score=4, description="four"),
                        MetricRubricLevel(score=5, description="five"),
                    ],
                ),
                MetricDefinition(
                    metric=MetricName.PROFESSIONAL_STRUCTURE,
                    definition="Definition",
                    rubric=[
                        MetricRubricLevel(score=0, description="zero"),
                        MetricRubricLevel(score=1, description="one"),
                        MetricRubricLevel(score=2, description="two"),
                        MetricRubricLevel(score=3, description="three"),
                        MetricRubricLevel(score=4, description="four"),
                        MetricRubricLevel(score=5, description="five"),
                    ],
                ),
            ],
            results=[],
            metric_averages={MetricName.FACT_COVERAGE: 4.0},
            overall_average=4.0,
        )

    error = exc_info.value.errors()[0]
    assert error["loc"] == ()
    assert error["type"] == "value_error"


def test_evaluation_report_accepts_single_provider_strategy_shape() -> None:
    report = EvaluationReport(
        source_file="data/scenarios.json",
        provider=ModelProvider.OPENAI,
        strategy=PromptStrategy.FEW_SHOT,
        metric_definitions=[
            MetricDefinition(
                metric=MetricName.FACT_COVERAGE,
                definition="Measures whether the generated email includes all required key facts accurately and naturally.",
                rubric=[
                    MetricRubricLevel(score=0, description="zero"),
                    MetricRubricLevel(score=1, description="one"),
                    MetricRubricLevel(score=2, description="two"),
                    MetricRubricLevel(score=3, description="three"),
                    MetricRubricLevel(score=4, description="four"),
                    MetricRubricLevel(score=5, description="five"),
                ],
            ),
            MetricDefinition(
                metric=MetricName.TONE_ALIGNMENT,
                definition="Measures whether the generated email matches the requested tone in context.",
                rubric=[
                    MetricRubricLevel(score=0, description="zero"),
                    MetricRubricLevel(score=1, description="one"),
                    MetricRubricLevel(score=2, description="two"),
                    MetricRubricLevel(score=3, description="three"),
                    MetricRubricLevel(score=4, description="four"),
                    MetricRubricLevel(score=5, description="five"),
                ],
            ),
            MetricDefinition(
                metric=MetricName.PROFESSIONAL_STRUCTURE,
                definition="Measures whether the output works as a professional email, including subject relevance, salutation, body organization, clear purpose, call to action where appropriate, and closing/signature.",
                rubric=[
                    MetricRubricLevel(score=0, description="zero"),
                    MetricRubricLevel(score=1, description="one"),
                    MetricRubricLevel(score=2, description="two"),
                    MetricRubricLevel(score=3, description="three"),
                    MetricRubricLevel(score=4, description="four"),
                    MetricRubricLevel(score=5, description="five"),
                ],
            ),
        ],
        results=[],
        metric_averages={
            MetricName.FACT_COVERAGE: 4.0,
            MetricName.TONE_ALIGNMENT: 4.0,
            MetricName.PROFESSIONAL_STRUCTURE: 4.0,
        },
        overall_average=4.0,
    )

    assert report.provider is ModelProvider.OPENAI
    assert report.strategy is PromptStrategy.FEW_SHOT


def test_enums_have_expected_values() -> None:
    assert PromptStrategy.STRUCTURED.value == "structured"
    assert PromptStrategy.FEW_SHOT.value == "few_shot"
    assert MetricName.FACT_COVERAGE.value == "fact_coverage"
    assert MetricName.TONE_ALIGNMENT.value == "tone_alignment"
    assert MetricName.PROFESSIONAL_STRUCTURE.value == "professional_structure"
