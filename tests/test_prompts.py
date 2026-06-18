from src.models import EmailScenario, GeneratedEmail, MetricName, PromptStrategy, ReferenceEmail
from src.prompts import build_generation_prompt, build_judge_prompt


def _scenario() -> EmailScenario:
    return EmailScenario(
        id="meeting_waiting_instructions",
        intent="Ask the meeting coordinator to provide exact waiting instructions for attendees coming to the May 17 meeting.",
        key_facts=[
            "The meeting is on May 17 at 11:00 A.M.",
            "The attendees are Kenneth Lay, Marty Sunde, and Bob Williams.",
            "The sender needs to know where the attendees should wait or go when they arrive.",
        ],
        tone="concise, polite and professional",
        reference_email=ReferenceEmail(subject="Waiting instructions", content="Hi Sarah"),
        sender="Rosalee Fleming",
        recipient="Sarah Whalen",
        affiliation="Kenneth Lay's assistant",
    )


def test_generation_prompt_uses_readable_scenario_brief() -> None:
    prompt = build_generation_prompt(_scenario(), PromptStrategy.STRUCTURED)

    assert "**Intent:** Ask the meeting coordinator" in prompt
    assert "**Key facts:**" in prompt
    assert "- The meeting is on May 17 at 11:00 A.M." in prompt
    assert "**Tone:** concise, polite and professional" in prompt
    assert "**Sender:** Rosalee Fleming" in prompt
    assert '"intent":' not in prompt
    assert '"key_facts":' not in prompt
    assert '{"subject": "string", "content": "string"}' in prompt


def test_few_shot_prompt_uses_readable_scenario_briefs_for_examples_and_target() -> None:
    prompt = build_generation_prompt(_scenario(), PromptStrategy.FEW_SHOT)

    assert "Example 1" in prompt
    assert "**Intent:** Follow up after a client meeting" in prompt
    assert "**Intent:** Ask the meeting coordinator" in prompt
    assert '"intent":' not in prompt
    assert '"key_facts":' not in prompt


def test_judge_prompt_uses_readable_scenario_and_email_briefs() -> None:
    prompt = build_judge_prompt(
        _scenario(),
        GeneratedEmail(
            subject="Waiting instructions",
            content="Dear Sarah,\n\nCould you confirm where attendees should wait?\n\nBest,\nRosalee",
        ),
        MetricName.PROFESSIONAL_STRUCTURE,
    )

    assert "**Intent:** Ask the meeting coordinator" in prompt
    assert "**Subject:** Waiting instructions" in prompt
    assert "**Content:**" in prompt
    assert "Dear Sarah,\n\nCould you confirm" in prompt
    assert '"content":' not in prompt
