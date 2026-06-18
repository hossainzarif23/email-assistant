from src.llm import build_generation_llm
from src.models import GeneratedEmail, ModelProvider


def generate_email(prompt: str, provider: ModelProvider = ModelProvider.GEMINI) -> GeneratedEmail:
    llm = build_generation_llm(provider)
    if provider is ModelProvider.OPENAI:
        generated_email = llm.with_structured_output(GeneratedEmail, method="function_calling").invoke(prompt)
    else:
        generated_email = llm.with_structured_output(GeneratedEmail).invoke(prompt)
    return GeneratedEmail(subject=generated_email.subject, content=generated_email.content)
