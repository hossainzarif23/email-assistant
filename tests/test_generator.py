from __future__ import annotations

import pytest

import src.generator as generator_module
from src.generator import generate_email
from src.models import GeneratedEmail, ModelProvider


def test_generate_email_invokes_structured_llm_with_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    observed: dict[str, object] = {}

    class FakeRunnable:
        def invoke(self, prompt: str) -> GeneratedEmail:
            observed["prompt"] = prompt
            return GeneratedEmail(
                subject="Follow-up",
                content="Hello Maya,\n\nThanks for your time.\n\nBest,\nJordan",
            )

    class FakeLLM:
        def with_structured_output(self, schema: type[GeneratedEmail], **kwargs: object) -> FakeRunnable:
            observed["schema"] = schema
            observed["kwargs"] = kwargs
            return FakeRunnable()

    def fake_build_generation_llm(provider: ModelProvider) -> FakeLLM:
        observed["provider"] = provider
        return FakeLLM()

    monkeypatch.setattr(generator_module, "build_generation_llm", fake_build_generation_llm)

    result = generate_email("fake prompt", ModelProvider.OPENAI)

    assert result == GeneratedEmail(
        subject="Follow-up",
        content="Hello Maya,\n\nThanks for your time.\n\nBest,\nJordan",
    )
    assert observed == {
        "schema": GeneratedEmail,
        "kwargs": {"method": "function_calling"},
        "prompt": "fake prompt",
        "provider": ModelProvider.OPENAI,
    }
