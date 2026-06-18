from __future__ import annotations

import pytest
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

import src.llm as llm_module
from src.llm import build_generation_llm, build_judge_llm
from src.models import ModelProvider


def test_build_generation_llm_uses_env_model_and_generation_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[bool] = []
    monkeypatch.setattr(llm_module, "load_dotenv", lambda: calls.append(True))
    monkeypatch.setenv("GEMINI_MODEL", "gemini-test-model")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

    model = build_generation_llm(ModelProvider.GEMINI)

    assert isinstance(model, ChatGoogleGenerativeAI)
    assert calls == [True]
    dumped = model.model_dump()
    assert dumped["model"] == "gemini-test-model"
    assert dumped["google_api_key"].get_secret_value() == "test-key"
    assert dumped["temperature"] == 0.7
    assert dumped["top_p"] == 0.95
    assert dumped["top_k"] == 40
    assert dumped["max_output_tokens"] == 32768
    assert dumped["thinking_level"] == "medium"


def test_build_judge_llm_uses_env_model_and_judge_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[bool] = []
    monkeypatch.setattr(llm_module, "load_dotenv", lambda: calls.append(True))
    monkeypatch.setenv("GEMINI_MODEL", "gemini-test-model")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

    model = build_judge_llm(ModelProvider.GEMINI)

    assert isinstance(model, ChatGoogleGenerativeAI)
    assert calls == [True]
    dumped = model.model_dump()
    assert dumped["model"] == "gemini-test-model"
    assert dumped["google_api_key"].get_secret_value() == "test-key"
    assert dumped["temperature"] == 0.1
    assert dumped["top_p"] == 0.2
    assert dumped["top_k"] == 1
    assert dumped["max_output_tokens"] == 32768
    assert dumped["thinking_level"] == "medium"


def test_build_generation_llm_supports_openai_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[bool] = []
    monkeypatch.setattr(llm_module, "load_dotenv", lambda: calls.append(True))
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4.1")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    model = build_generation_llm(ModelProvider.OPENAI)

    assert isinstance(model, ChatOpenAI)
    assert calls == [True]
    dumped = model.model_dump()
    assert dumped["model_name"] == "gpt-4.1"
    assert dumped["openai_api_key"].get_secret_value() == "test-key"
    assert dumped["temperature"] == 0.7
    assert dumped["top_p"] == 0.95
    assert dumped["max_tokens"] == 32768
    assert dumped["reasoning"] == {"effort": "medium"}


def test_build_judge_llm_supports_openai_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[bool] = []
    monkeypatch.setattr(llm_module, "load_dotenv", lambda: calls.append(True))
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4.1")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    model = build_judge_llm(ModelProvider.OPENAI)

    assert isinstance(model, ChatOpenAI)
    assert calls == [True]
    dumped = model.model_dump()
    assert dumped["model_name"] == "gpt-4.1"
    assert dumped["openai_api_key"].get_secret_value() == "test-key"
    assert dumped["temperature"] == 0.1
    assert dumped["top_p"] == 0.2
    assert dumped["max_tokens"] == 32768
    assert dumped["reasoning"] == {"effort": "medium"}


def test_build_openai_reasoning_models_omit_top_p(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(llm_module, "load_dotenv", lambda: None)
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.4-mini")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    model = build_generation_llm(ModelProvider.OPENAI)

    dumped = model.model_dump()
    assert dumped["model_name"] == "gpt-5.4-mini"
    assert dumped["top_p"] is None
