from __future__ import annotations

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

from src.evaluation import load_scenarios, run_evaluation, write_report_json
from src.generator import generate_email
from src.models import GeneratedEmail, PromptStrategy
from src.prompts import build_generation_prompt

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCENARIOS_PATH = PROJECT_ROOT / "data" / "scenarios.json"
SMOKE_REPORT_PATH = PROJECT_ROOT / "artifacts" / "evaluation_smoke.json"

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module", autouse=True)
def _require_live_google_api_key() -> None:
    load_dotenv(dotenv_path=PROJECT_ROOT / ".env")
    if not os.getenv("GOOGLE_API_KEY", "").strip():
        pytest.skip(
            "GOOGLE_API_KEY is not available after loading repo-root .env; "
            "skipping live Gemini integration tests"
        )


def test_real_generation_produces_non_empty_email() -> None:
    scenario = load_scenarios(SCENARIOS_PATH)[0]

    generated_email = generate_email(build_generation_prompt(scenario, PromptStrategy.STRUCTURED))

    assert isinstance(generated_email, GeneratedEmail)
    assert generated_email.subject.strip()
    assert generated_email.content.strip()


def test_real_evaluation_smoke_writes_report_and_scores_one_scenario() -> None:
    report = run_evaluation(SCENARIOS_PATH, limit=1)
    write_report_json(report, SMOKE_REPORT_PATH)

    assert SMOKE_REPORT_PATH.exists()
    assert report.source_file == SCENARIOS_PATH.as_posix()
    assert report.strategy is PromptStrategy.STRUCTURED
    assert len(report.results) == 1
    assert len(report.results[0].metrics) == 3
    assert len(report.metric_averages) == 3
