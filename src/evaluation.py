import json
from pathlib import Path

from pydantic import TypeAdapter

from src.generator import generate_email
from src.llm import build_judge_llm
from src.models import (
    EmailScenario,
    EvaluationReport,
    GeneratedEmail,
    JudgeScore,
    MetricName,
    MetricResult,
    ModelProvider,
    PromptStrategy,
    StrategyAggregate,
    StrategyScenarioResult,
)
from src.metrics import METRIC_DEFINITIONS
from src.prompts import build_generation_prompt, build_judge_prompt


def load_scenarios(path: Path) -> list[EmailScenario]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return TypeAdapter(list[EmailScenario]).validate_python(data)


def run_judges(
    scenario: EmailScenario,
    generated_email: GeneratedEmail,
    provider: ModelProvider = ModelProvider.GEMINI,
) -> list[MetricResult]:
    if provider is ModelProvider.OPENAI:
        structured_judge = build_judge_llm(provider).with_structured_output(JudgeScore, method="function_calling")
    else:
        structured_judge = build_judge_llm(provider).with_structured_output(JudgeScore)
    results: list[MetricResult] = []

    for metric in MetricName:
        prompt = build_judge_prompt(scenario, generated_email, metric)
        judge_score = structured_judge.invoke(prompt)
        judge_score = JudgeScore(score=judge_score.score, reason=judge_score.reason)
        results.append(MetricResult(metric=metric, score=judge_score.score, reason=judge_score.reason))

    return results


def aggregate_results(results: dict[PromptStrategy, list[StrategyScenarioResult]]) -> tuple[list[StrategyAggregate], PromptStrategy | None]:
    if not any(results.values()):
        return [], None

    missing_strategies = [strategy.value for strategy in PromptStrategy if not results.get(strategy)]
    if missing_strategies:
        raise ValueError(f"results must include both prompt strategies; missing: {', '.join(missing_strategies)}")

    aggregates: list[StrategyAggregate] = []
    for strategy in PromptStrategy:
        metric_averages: dict[MetricName, float] = {}
        for metric in MetricName:
            scores = [
                metric_result.score
                for result in results[strategy]
                for metric_result in result.metrics
                if metric_result.metric is metric
            ]
            metric_averages[metric] = sum(scores) / len(scores) if scores else 0.0

        overall_average = sum(metric_averages.values()) / len(metric_averages)
        aggregates.append(
            StrategyAggregate(
                strategy=strategy,
                metric_averages=metric_averages,
                overall_average=overall_average,
            )
        )

    winner = max(aggregates, key=lambda aggregate: aggregate.overall_average).strategy
    return aggregates, winner


def run_evaluation(
    scenarios_path: Path,
    limit: int | None = None,
    scenario_id: str | None = None,
    provider: ModelProvider = ModelProvider.GEMINI,
) -> EvaluationReport:
    scenarios = load_scenarios(scenarios_path)
    if scenario_id is not None:
        scenarios = [scenario for scenario in scenarios if scenario.id == scenario_id]
    if limit is not None:
        scenarios = scenarios[:limit]

    results: dict[PromptStrategy, list[StrategyScenarioResult]] = {strategy: [] for strategy in PromptStrategy}
    for strategy in PromptStrategy:
        for scenario in scenarios:
            generation_prompt = build_generation_prompt(scenario, strategy)
            result = generate_email(generation_prompt, provider)
            results[strategy].append(
                StrategyScenarioResult(
                    scenario_id=scenario.id,
                    generation_prompt=generation_prompt,
                    generated_email=result,
                    metrics=run_judges(scenario, result, provider),
                )
            )

    aggregates, winner = aggregate_results(results)
    return EvaluationReport(
        source_file=scenarios_path,
        metric_definitions=METRIC_DEFINITIONS,
        results=results,
        aggregates=aggregates,
        winner=winner,
    )


def write_report_json(report: EvaluationReport, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
