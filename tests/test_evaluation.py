from __future__ import annotations

import json
from pathlib import Path

import pytest

import src.evaluation as evaluation_module
from src.models import (
    EmailScenario,
    EvaluationReport,
    GeneratedEmail,
    JudgeScore,
    MetricDefinition,
    MetricName,
    MetricResult,
    MetricRubricLevel,
    ModelProvider,
    PromptStrategy,
    ReferenceEmail,
    ScenarioEvaluationResult,
)


def _scenario() -> EmailScenario:
    return EmailScenario(
        id="demo",
        intent="Request a proposal",
        key_facts=["Need it by Friday", "Budget is $12,000"],
        tone="polite and concise",
        reference_email=ReferenceEmail(subject="Proposal", content="Dear Alex,\n\nPlease send the proposal.\n\nBest,\nSam"),
    )


def _generated_email(subject: str = "Proposal update") -> GeneratedEmail:
    return GeneratedEmail(
        subject=subject,
        content="Dear Alex,\n\nPlease send the proposal by Friday.\n\nBest,\nSam",
    )


def _metric_result(metric: MetricName, score: int) -> MetricResult:
    return MetricResult(metric=metric, score=score, reason=f"{metric.value}:{score}")


def _metric_definition(metric: MetricName) -> MetricDefinition:
    return MetricDefinition(
        metric=metric,
        definition=f"{metric.value} definition",
        rubric=[
            MetricRubricLevel(score=0, description="zero"),
            MetricRubricLevel(score=1, description="one"),
            MetricRubricLevel(score=2, description="two"),
            MetricRubricLevel(score=3, description="three"),
            MetricRubricLevel(score=4, description="four"),
            MetricRubricLevel(score=5, description="five"),
        ],
    )


def test_load_scenarios_reads_and_validates_json(tmp_path: Path) -> None:
    scenario_file = tmp_path / "scenarios.json"
    scenario_file.write_text(
        json.dumps(
            [
                {
                    "id": "demo",
                    "intent": "Request a proposal",
                    "key_facts": ["Need it by Friday", "Budget is $12,000"],
                    "tone": "polite and concise",
                    "reference_email": {
                        "subject": "Proposal",
                        "content": "Dear Alex,\n\nPlease send the proposal.\n\nBest,\nSam",
                    },
                }
            ]
        ),
        encoding="utf-8",
    )

    scenarios = evaluation_module.load_scenarios(scenario_file)

    assert len(scenarios) == 1
    assert scenarios[0] == _scenario()


def test_run_judges_scores_once_per_metric(monkeypatch: pytest.MonkeyPatch) -> None:
    scenario = _scenario()
    email = _generated_email()
    prompts: list[str] = []
    observed: dict[str, object] = {}

    class _FakeJudgeModel:
        def with_structured_output(self, schema: type[JudgeScore], **kwargs: object) -> object:
            observed["kwargs"] = kwargs

            class _Runnable:
                def invoke(self, prompt: str) -> JudgeScore:
                    prompts.append(prompt)
                    return JudgeScore(score=5, reason="Meets the rubric.")

            return _Runnable()

    def fake_build_judge_llm(provider: ModelProvider) -> _FakeJudgeModel:
        observed["provider"] = provider
        return _FakeJudgeModel()

    monkeypatch.setattr(evaluation_module, "build_judge_llm", fake_build_judge_llm)

    results = evaluation_module.run_judges(scenario, email, ModelProvider.OPENAI)

    assert observed["provider"] is ModelProvider.OPENAI
    assert observed["kwargs"] == {"method": "function_calling"}
    assert [result.metric for result in results] == list(MetricName)
    assert all(result.score == 5 for result in results)
    assert all(result.reason == "Meets the rubric." for result in results)
    assert len(prompts) == 3
    assert len(set(prompts)) == 3


def test_run_judges_uses_default_structured_path_without_injected_judge(monkeypatch: pytest.MonkeyPatch) -> None:
    scenario = _scenario()
    email = _generated_email()
    observed: dict[str, object] = {}

    class _FakeJudgeModel:
        def with_structured_output(self, schema: type[JudgeScore], **kwargs: object) -> object:
            observed["schema"] = schema
            observed["kwargs"] = kwargs

            class _Runnable:
                def invoke(self, prompt: str) -> JudgeScore:
                    observed.setdefault("prompts", []).append(prompt)
                    return JudgeScore(score=4, reason="structured")

            return _Runnable()

    def fake_build_judge_llm(provider: ModelProvider) -> _FakeJudgeModel:
        observed["built"] = True
        observed["provider"] = provider
        return _FakeJudgeModel()

    monkeypatch.setattr(evaluation_module, "build_judge_llm", fake_build_judge_llm)

    results = evaluation_module.run_judges(scenario, email)

    assert observed["built"] is True
    assert observed["provider"] is ModelProvider.GEMINI
    assert observed["schema"] is JudgeScore
    assert observed["kwargs"] == {"method": "function_calling"}
    assert len(observed["prompts"]) == 3
    assert len(results) == 3


def test_aggregate_results_computes_per_metric_and_overall_averages() -> None:
    results = [
        ScenarioEvaluationResult(
            scenario_id="s1",
            metrics=[
                _metric_result(MetricName.FACT_COVERAGE, 3),
                _metric_result(MetricName.TONE_ALIGNMENT, 4),
                _metric_result(MetricName.PROFESSIONAL_STRUCTURE, 5),
            ],
        ),
        ScenarioEvaluationResult(
            scenario_id="s2",
            metrics=[
                _metric_result(MetricName.FACT_COVERAGE, 5),
                _metric_result(MetricName.TONE_ALIGNMENT, 4),
                _metric_result(MetricName.PROFESSIONAL_STRUCTURE, 5),
            ],
        ),
    ]

    metric_averages, overall_average = evaluation_module.aggregate_results(results)

    assert metric_averages == {
        MetricName.FACT_COVERAGE: pytest.approx(4.0),
        MetricName.TONE_ALIGNMENT: pytest.approx(4.0),
        MetricName.PROFESSIONAL_STRUCTURE: pytest.approx(5.0),
    }
    assert overall_average == pytest.approx(13 / 3)


def test_aggregate_results_returns_zero_averages_for_no_results() -> None:
    metric_averages, overall_average = evaluation_module.aggregate_results([])

    assert metric_averages == {
        MetricName.FACT_COVERAGE: 0.0,
        MetricName.TONE_ALIGNMENT: 0.0,
        MetricName.PROFESSIONAL_STRUCTURE: 0.0,
    }
    assert overall_average == 0.0


def test_run_evaluation_uses_selected_scenarios_strategy_and_provider(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    scenarios_file = tmp_path / "scenarios.json"
    scenarios_file.write_text(
        json.dumps(
            [
                {
                    "id": "alpha",
                    "intent": "Request a proposal",
                    "key_facts": ["Need it by Friday"],
                    "tone": "polite",
                    "reference_email": {"subject": "Alpha", "content": "Hi"},
                },
                {
                    "id": "beta",
                    "intent": "Schedule a meeting",
                    "key_facts": ["Need next week"],
                    "tone": "professional",
                    "reference_email": {"subject": "Beta", "content": "Hello"},
                },
            ]
        ),
        encoding="utf-8",
    )

    generated_calls: list[tuple[str, ModelProvider]] = []
    judged_calls: list[tuple[str, ModelProvider]] = []

    def fake_build_generation_prompt(scenario: EmailScenario, strategy: PromptStrategy) -> str:
        return f"prompt:{scenario.id}:{strategy.value}"

    def fake_generate_email(prompt: str, provider: ModelProvider) -> GeneratedEmail:
        generated_calls.append((prompt, provider))
        return _generated_email(prompt.removeprefix("prompt:"))

    def fake_run_judges(
        scenario: EmailScenario,
        generated_email: GeneratedEmail,
        provider: ModelProvider = ModelProvider.GEMINI,
    ) -> list[MetricResult]:
        judged_calls.append((f"{scenario.id}:{generated_email.subject}", provider))
        return [
            _metric_result(MetricName.FACT_COVERAGE, 5),
            _metric_result(MetricName.TONE_ALIGNMENT, 4),
            _metric_result(MetricName.PROFESSIONAL_STRUCTURE, 3),
        ]

    monkeypatch.setattr(evaluation_module, "build_generation_prompt", fake_build_generation_prompt)
    monkeypatch.setattr(evaluation_module, "generate_email", fake_generate_email)
    monkeypatch.setattr(evaluation_module, "run_judges", fake_run_judges)

    report = evaluation_module.run_evaluation(
        scenarios_file,
        limit=1,
        provider=ModelProvider.OPENAI,
        strategy=PromptStrategy.FEW_SHOT,
    )

    assert report.source_file == scenarios_file.as_posix()
    assert report.provider is ModelProvider.OPENAI
    assert report.strategy is PromptStrategy.FEW_SHOT
    assert [definition.metric for definition in report.metric_definitions] == list(MetricName)
    assert [result.scenario_id for result in report.results] == ["alpha"]
    assert [metric.score for metric in report.results[0].metrics] == [5, 4, 3]
    assert generated_calls == [
        ("prompt:alpha:few_shot", ModelProvider.OPENAI),
    ]
    assert judged_calls == [
        ("alpha:alpha:few_shot", ModelProvider.OPENAI),
    ]
    assert report.metric_averages == {
        MetricName.FACT_COVERAGE: pytest.approx(5.0),
        MetricName.TONE_ALIGNMENT: pytest.approx(4.0),
        MetricName.PROFESSIONAL_STRUCTURE: pytest.approx(3.0),
    }
    assert report.overall_average == pytest.approx(4.0)


def test_write_report_json_creates_parent_directory_and_writes_report(tmp_path: Path) -> None:
    report = EvaluationReport(
        source_file="data/scenarios.json",
        provider=ModelProvider.OPENAI,
        strategy=PromptStrategy.FEW_SHOT,
        metric_definitions=[_metric_definition(metric) for metric in MetricName],
        results=[],
        metric_averages={
            MetricName.FACT_COVERAGE: 4.0,
            MetricName.TONE_ALIGNMENT: 4.0,
            MetricName.PROFESSIONAL_STRUCTURE: 4.0,
        },
        overall_average=4.0,
    )
    output_path = tmp_path / "nested" / "evaluation.json"

    evaluation_module.write_report_json(report, output_path)

    written = json.loads(output_path.read_text(encoding="utf-8"))
    assert output_path.exists()
    assert written["source_file"] == "data/scenarios.json"
    assert written["provider"] == "openai"
    assert written["strategy"] == "few_shot"
    assert [definition["metric"] for definition in written["metric_definitions"]] == [metric.value for metric in MetricName]
    assert set(written["metric_definitions"][0]) == {"metric", "definition", "rubric"}
    assert written["results"] == []
    assert written["metric_averages"] == {
        "fact_coverage": 4.0,
        "tone_alignment": 4.0,
        "professional_structure": 4.0,
    }
    assert written["overall_average"] == 4.0
