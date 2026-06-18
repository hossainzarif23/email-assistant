from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

import src.cli as cli_module
from src.models import EmailScenario, GeneratedEmail, ModelProvider, PromptStrategy, ReferenceEmail


def test_build_parser_supports_generate_subcommand() -> None:
    parser = cli_module.build_parser()

    namespace = parser.parse_args(
        [
            "generate",
            "--intent",
            "Follow up after the meeting",
            "--fact",
            "Thank the recipient for their time",
            "--fact",
            "Share the revised timeline",
            "--tone",
            "warm and professional",
            "--sender",
            "Jordan Lee",
            "--recipient",
            "Maya Patel",
            "--affiliation",
            "Northstar Consulting",
        ]
    )

    assert namespace.command == "generate"
    assert namespace.intent == "Follow up after the meeting"
    assert namespace.fact == ["Thank the recipient for their time", "Share the revised timeline"]
    assert namespace.tone == "warm and professional"
    assert namespace.sender == "Jordan Lee"
    assert namespace.recipient == "Maya Patel"
    assert namespace.affiliation == "Northstar Consulting"
    assert namespace.strategy == PromptStrategy.STRUCTURED.value
    assert namespace.provider == ModelProvider.GEMINI.value


def test_build_parser_supports_evaluate_subcommand_with_defaults() -> None:
    parser = cli_module.build_parser()

    namespace = parser.parse_args(["evaluate"])

    assert namespace.command == "evaluate"
    assert namespace.scenarios == Path("data/scenarios.json")
    assert namespace.limit is None
    assert namespace.scenario_id is None
    assert namespace.output == Path("artifacts/evaluation_results.json")
    assert namespace.provider == ModelProvider.GEMINI.value


def test_generate_help_uses_literal_strategy_values(capsys: pytest.CaptureFixture[str]) -> None:
    parser = cli_module.build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["generate", "--help"])

    help_text = capsys.readouterr().out
    assert "structured" in help_text
    assert "few_shot" in help_text
    assert "PromptStrategy.STRUCTURED" not in help_text
    assert "PromptStrategy.FEW_SHOT" not in help_text


def test_build_parser_rejects_invalid_generate_strategy() -> None:
    parser = cli_module.build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "generate",
                "--intent",
                "Follow up",
                "--fact",
                "Include the timeline",
                "--tone",
                "polite",
                "--strategy",
                "invalid",
            ]
        )


def test_main_generate_invokes_generator_and_prints_email_json(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    observed: dict[str, object] = {}

    def fake_build_generation_prompt(scenario: EmailScenario, strategy: PromptStrategy) -> str:
        observed["scenario"] = scenario
        observed["strategy"] = strategy
        return "fake prompt"

    def fake_generate_email(prompt: str) -> GeneratedEmail:
        observed["prompt"] = prompt
        return GeneratedEmail(subject="Follow-up", content="Hello Maya,\n\nThanks for your time.\n\nBest,\nJordan")

    def fake_generate_email_with_provider(prompt: str, provider: ModelProvider) -> GeneratedEmail:
        observed["prompt"] = prompt
        observed["provider"] = provider
        return fake_generate_email(prompt)

    monkeypatch.setattr(cli_module, "build_generation_prompt", fake_build_generation_prompt)
    monkeypatch.setattr(cli_module, "generate_email", fake_generate_email_with_provider)

    exit_code = cli_module.main(
        [
            "generate",
            "--intent",
            "Follow up after the meeting",
            "--fact",
            "Thank the recipient for their time",
            "--fact",
            "Share the revised timeline",
            "--tone",
            "warm and professional",
            "--sender",
            "Jordan Lee",
            "--recipient",
            "Maya Patel",
            "--affiliation",
            "Northstar Consulting",
            "--strategy",
            "few_shot",
            "--provider",
            "openai",
        ]
    )

    assert exit_code == 0
    assert observed["strategy"] is PromptStrategy.FEW_SHOT
    assert observed["provider"] is ModelProvider.OPENAI
    assert observed["prompt"] == "fake prompt"
    scenario = observed["scenario"]
    assert isinstance(scenario, EmailScenario)
    assert scenario.id == "cli"
    assert scenario.reference_email == ReferenceEmail(subject="Placeholder", content="Placeholder")
    assert scenario.key_facts == [
        "Thank the recipient for their time",
        "Share the revised timeline",
    ]

    printed = json.loads(capsys.readouterr().out)
    assert printed == {
        "subject": "Follow-up",
        "content": "Hello Maya,\n\nThanks for your time.\n\nBest,\nJordan",
    }


def test_main_evaluate_invokes_report_writer_and_prints_output_path(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    observed: dict[str, object] = {}
    output_path = tmp_path / "reports" / "evaluation.json"
    scenarios_path = tmp_path / "scenarios.json"
    scenarios_path.write_text("[]", encoding="utf-8")

    report = object()

    def fake_run_evaluation(
        path: Path,
        limit: int | None = None,
        scenario_id: str | None = None,
        provider: ModelProvider = ModelProvider.GEMINI,
    ) -> object:
        observed["path"] = path
        observed["limit"] = limit
        observed["scenario_id"] = scenario_id
        observed["provider"] = provider
        return report

    def fake_write_report_json(report_arg: object, output_arg: Path) -> None:
        observed["report"] = report_arg
        observed["output"] = output_arg

    monkeypatch.setattr(cli_module, "run_evaluation", fake_run_evaluation)
    monkeypatch.setattr(cli_module, "write_report_json", fake_write_report_json)

    exit_code = cli_module.main(
        [
            "evaluate",
            "--scenarios",
            str(scenarios_path),
            "--limit",
            "1",
            "--scenario-id",
            "demo",
            "--output",
            str(output_path),
            "--provider",
            "openai",
        ]
    )

    assert exit_code == 0
    assert observed == {
        "path": scenarios_path,
        "limit": 1,
        "scenario_id": "demo",
        "provider": ModelProvider.OPENAI,
        "report": report,
        "output": output_path,
    }
    assert capsys.readouterr().out.strip() == str(output_path)
