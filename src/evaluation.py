import json
from pathlib import Path

from pydantic import TypeAdapter

from src.generator import generate_email
from src.llm import build_openai_judge_llm
from src.models import (
    EmailScenario,
    EvaluationReport,
    GeneratedEmail,
    JudgeScore,
    MetricName,
    MetricResult,
    ModelProvider,
    PromptStrategy,
    ScenarioEvaluationResult,
)
from src.metrics import METRIC_DEFINITIONS
from src.prompts import build_generation_prompt, build_judge_prompt


def load_scenarios(path: Path) -> list[EmailScenario]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return TypeAdapter(list[EmailScenario]).validate_python(data)


def run_judges(
    scenario: EmailScenario,
    generated_email: GeneratedEmail
) -> list[MetricResult]:
    structured_judge = build_openai_judge_llm().with_structured_output(JudgeScore, method="function_calling")
    
    results: list[MetricResult] = []

    for metric in MetricName:
        prompt = build_judge_prompt(scenario, generated_email, metric)
        judge_score = structured_judge.invoke(prompt)
        judge_score = JudgeScore(score=judge_score.score, reason=judge_score.reason)
        results.append(MetricResult(metric=metric, score=judge_score.score, reason=judge_score.reason))

    return results


def aggregate_results(results: list[ScenarioEvaluationResult]) -> tuple[dict[MetricName, float], float]:
    metric_averages: dict[MetricName, float] = {}
    for metric in MetricName:
        scores = [
            metric_result.score
            for result in results
            for metric_result in result.metrics
            if metric_result.metric is metric
        ]
        metric_averages[metric] = sum(scores) / len(scores) if scores else 0.0

    overall_average = sum(metric_averages.values()) / len(metric_averages)
    return metric_averages, overall_average


def run_evaluation(
    scenarios_path: Path,
    limit: int | None = None,
    scenario_id: str | None = None,
    provider: ModelProvider = ModelProvider.GEMINI,
    strategy: PromptStrategy = PromptStrategy.STRUCTURED,
) -> EvaluationReport:
    scenarios = load_scenarios(scenarios_path)
    if scenario_id is not None:
        scenarios = [scenario for scenario in scenarios if scenario.id == scenario_id]
    if limit is not None:
        scenarios = scenarios[:limit]

    results: list[ScenarioEvaluationResult] = []
    for scenario in scenarios:
        generation_prompt = build_generation_prompt(scenario, strategy)
        result = generate_email(generation_prompt, provider)
        results.append(
            ScenarioEvaluationResult(
                scenario_id=scenario.id,
                metrics=run_judges(scenario, result),
            )
        )

    metric_averages, overall_average = aggregate_results(results)
    return EvaluationReport(
        source_file=scenarios_path.as_posix(),
        provider=provider,
        strategy=strategy,
        metric_definitions=METRIC_DEFINITIONS,
        results=results,
        metric_averages=metric_averages,
        overall_average=overall_average,
    )


def write_report_json(report: EvaluationReport, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
