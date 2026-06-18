from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from src.evaluation import run_evaluation, write_report_json
from src.generator import generate_email
from src.models import EmailScenario, ModelProvider, PromptStrategy, ReferenceEmail
from src.prompts import build_generation_prompt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="email-generation-assistant")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser("generate", help="Generate a single email from intent, facts, and tone.")
    generate_parser.add_argument("--intent", required=True)
    generate_parser.add_argument("--fact", action="append", required=True, dest="fact")
    generate_parser.add_argument("--tone", required=True)
    generate_parser.add_argument("--sender")
    generate_parser.add_argument("--recipient")
    generate_parser.add_argument("--affiliation")
    generate_parser.add_argument(
        "--strategy",
        choices=[item.value for item in PromptStrategy],
        default=PromptStrategy.STRUCTURED.value,
    )
    generate_parser.add_argument(
        "--provider",
        choices=[item.value for item in ModelProvider],
        default=ModelProvider.GEMINI.value,
    )

    evaluate_parser = subparsers.add_parser("evaluate", help="Run the evaluation pipeline and write a report.")
    evaluate_parser.add_argument("--scenarios", type=Path, default=Path("data/scenarios.json"))
    evaluate_parser.add_argument("--limit", type=int)
    evaluate_parser.add_argument("--scenario-id")
    evaluate_parser.add_argument("--output", type=Path, default=Path("artifacts/evaluation_results.json"))
    evaluate_parser.add_argument(
        "--provider",
        choices=[item.value for item in ModelProvider],
        default=ModelProvider.GEMINI.value,
    )

    return parser


def build_cli_scenario(args: argparse.Namespace) -> EmailScenario:
    return EmailScenario(
        id="cli",
        intent=args.intent,
        key_facts=list(args.fact),
        tone=args.tone,
        reference_email=ReferenceEmail(subject="Placeholder", content="Placeholder"),
        sender=args.sender,
        recipient=args.recipient,
        affiliation=args.affiliation,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "generate":
        scenario = build_cli_scenario(args)
        generated_email = generate_email(
            build_generation_prompt(scenario, PromptStrategy(args.strategy)),
            ModelProvider(args.provider),
        )
        print(generated_email.model_dump_json())
        return 0

    if args.command == "evaluate":
        report = run_evaluation(
            args.scenarios,
            limit=args.limit,
            scenario_id=args.scenario_id,
            provider=ModelProvider(args.provider),
        )
        write_report_json(report, args.output)
        print(args.output)
        return 0

    raise ValueError(f"Unsupported command: {args.command}")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
