import os

from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from src.models import ModelProvider


def build_generation_llm(provider: ModelProvider = ModelProvider.GEMINI) -> BaseChatModel:
    if provider is ModelProvider.GEMINI:
        return build_gemini_generation_llm()
    if provider is ModelProvider.OPENAI:
        return build_openai_generation_llm()
    raise ValueError(f"Unsupported model provider: {provider}")


def build_gemini_generation_llm() -> ChatGoogleGenerativeAI:
    load_dotenv()
    return ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.7,
        top_p=0.95,
        top_k=40,
        max_output_tokens=32768,
        thinking_level="medium",
    )


def build_openai_generation_llm() -> ChatOpenAI:
    load_dotenv()
    model_name = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")
    return ChatOpenAI(
        model=model_name,
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0.7,
        max_tokens=32768,
        reasoning={"effort": "medium"},
    )


def build_openai_judge_llm() -> ChatOpenAI:
    load_dotenv()
    model_name = "gpt-5.4-mini"
    return ChatOpenAI(
        model=model_name,
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0.1,
        max_tokens=32768,
        reasoning={"effort": "medium"},
    )
