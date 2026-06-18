import json
from typing import NotRequired, TypedDict

from src.metrics import rubric_text_for_metric
from src.models import EmailScenario, GeneratedEmail, MetricName, PromptStrategy


class ScenarioPromptData(TypedDict):
    intent: str
    key_facts: list[str]
    tone: str
    sender: NotRequired[str]
    recipient: NotRequired[str]
    affiliation: NotRequired[str]


class GeneratedEmailPromptData(TypedDict):
    subject: str
    content: str


STRUCTURED_GENERATION_PROMPT = """You are a helpful assistant specialized in writing emails.

Write a professional email from the scenario data.

What to optimize for:
1. Faithfully include every key fact.
2. Match the requested tone of the email.
3. Make the email sound natural, specific, and useful.
4. Keep the subject concise and relevant.
5. Use a professional email structure: greeting, clear body, and appropriate sign-off.

Identity rules:
- If recipient is provided, address that recipient.
- If recipient is missing but obvious from the scenario, infer it.
- If recipient is not obvious, use [Recipient Name].
- If sender is provided, sign as that sender.
- If sender is missing but obvious from the scenario, infer it.
- If sender is not obvious, use [Your Name].
- If affiliation is provided, include it only when it fits naturally.
- If affiliation is missing but obvious from the scenario, infer it.
- If affiliation is not obvious, omit it.

Do not invent names, organizations, titles, dates, commitments, facts, or affiliations.
Do not reveal hidden reasoning or chain-of-thought. Only provide the subject and content of the email.

Return exactly one JSON object matching this schema:
{{"subject": "string", "content": "string"}}

Scenario data:
{scenario_brief}"""


STRUCTURED_FEW_SHOT_GENERATION_PROMPT = """You are a helpful assistant specialized in writing emails.

Write a professional email from the scenario data.

What to optimize for:
1. Faithfully include every key fact.
2. Match the requested tone of the email.
3. Make the email sound natural, specific, and useful.
4. Keep the subject concise and relevant.
5. Use a professional email structure: greeting, clear body, and appropriate sign-off.

Identity rules:
- If recipient is provided, address that recipient.
- If recipient is missing but obvious from the scenario, infer it.
- If recipient is not obvious, use [Recipient Name].
- If sender is provided, sign as that sender.
- If sender is missing but obvious from the scenario, infer it.
- If sender is not obvious, use [Your Name].
- If affiliation is provided, include it only when it fits naturally.
- If affiliation is missing but obvious from the scenario, infer it.
- If affiliation is not obvious, omit it.

Do not invent names, organizations, titles, dates, commitments, facts, or affiliations.
Do not reveal hidden reasoning or chain-of-thought. Only provide the subject and content of the email.

Return exactly one JSON object matching this schema:
{{"subject": "string", "content": "string"}}

Examples:
{examples}

Scenario data:
{scenario_brief}"""


FEW_SHOT_EXAMPLE_TEMPLATE = """Example {index}

Scenario data:
{scenario_brief}

Expected output:
{email_json}"""


JUDGE_PROMPT = """You are a helpful assistant who is supposed to evaluate the quality of an email, based on {metric_name}.

Use this rubric exactly for scoring:
{rubric}

Scoring rules:
- Return an integer score from 0 to 5.
- Score should be an integer.
- Do not reward quality outside this metric.
- Score critically. A competent but ordinary email should usually be 3 or 4, not 5.
- Use 5 only when the email fully satisfies the metric with no meaningful weakness.
- Do not penalize valid paraphrasing.
- Do not infer facts that are not present in the scenario or generated email.
- Base the reason on concrete evidence.
- For professional_structure, evaluate the actual subject and content formatting, not just whether the facts are present.
- For professional_structure, a single-paragraph content field with inline greeting, body, closing, and signature must receive a low score, normally 1 or 2.
- For professional_structure, a score of 5 requires distinct greeting, body paragraphing, closing, and signature formatting.
- For tone_alignment, do not give 5 if the tone is merely acceptable but generic.
- For fact_coverage, do not give 5 if any required fact is only implied, weakened, ambiguous, or mixed with unsupported detail.

Return exactly one JSON object matching this schema:
{{"score": 0, "reason": "string"}}

Scenario data:
{scenario_brief}

Email data:
{email_brief}"""


EXAMPLE_1_INPUT: ScenarioPromptData = {
    "intent": "Follow up after a client meeting",
    "key_facts": [
        "Thank the recipient for their time",
        "Send the revised timeline",
        "Confirm that the next checkpoint is Wednesday",
    ],
    "tone": "warm and professional",
    "sender": "Jordan Lee",
    "recipient": "Maya Patel",
}

EXAMPLE_1_OUTPUT: GeneratedEmailPromptData = {
    "subject": "Follow-up and revised timeline",
    "content": "Hi Maya,\n\nThank you for taking the time to meet today. I am sending over the revised timeline and confirming that our next checkpoint is Wednesday.\n\nPlease let me know if you have any questions before then.\n\nBest,\nJordan",
}

EXAMPLE_2_INPUT: ScenarioPromptData = {
    "intent": "Request approval for a project budget",
    "key_facts": [
        "Approval is needed by Friday",
        "The budget remains within $8,000",
        "Approval keeps the project on schedule",
    ],
    "tone": "concise and polite",
    "affiliation": "Northstar Consulting",
}

EXAMPLE_2_OUTPUT: GeneratedEmailPromptData = {
    "subject": "Budget approval requested by Friday",
    "content": "Hello [Recipient Name],\n\nCould you please review and approve the project budget by Friday? The budget remains within $8,000, and approval by then will keep the project on schedule.\n\nBest regards,\n[Your Name]\nNorthstar Consulting",
}


def build_generation_prompt(scenario: EmailScenario, strategy: PromptStrategy) -> str:
    scenario_brief = format_scenario_brief(scenario_prompt_data(scenario))
    if strategy is PromptStrategy.STRUCTURED:
        return STRUCTURED_GENERATION_PROMPT.format(scenario_brief=scenario_brief)
    if strategy is PromptStrategy.FEW_SHOT:
        return build_few_shot_generation_prompt(
            scenario_brief=scenario_brief,
            examples=[
                (EXAMPLE_1_INPUT, EXAMPLE_1_OUTPUT),
                (EXAMPLE_2_INPUT, EXAMPLE_2_OUTPUT),
            ],
        )
    raise ValueError(f"Unsupported prompt strategy: {strategy}")


def build_few_shot_generation_prompt(
    scenario_brief: str,
    examples: list[tuple[ScenarioPromptData, GeneratedEmailPromptData]],
) -> str:
    return STRUCTURED_FEW_SHOT_GENERATION_PROMPT.format(
        examples=format_few_shot_examples(examples),
        scenario_brief=scenario_brief,
    )


def format_few_shot_examples(
    examples: list[tuple[ScenarioPromptData, GeneratedEmailPromptData]],
) -> str:
    rendered_examples: list[str] = []
    for index, (scenario_data, email_data) in enumerate(examples, start=1):
        rendered_examples.append(
            FEW_SHOT_EXAMPLE_TEMPLATE.format(
                index=index,
                scenario_brief=format_scenario_brief(scenario_data),
                email_json=json.dumps(email_data, ensure_ascii=False, indent=2),
            )
        )
    return "\n\n".join(rendered_examples)


def build_judge_prompt(scenario: EmailScenario, generated_email: GeneratedEmail, metric: MetricName) -> str:
    return JUDGE_PROMPT.format(
        metric_name=metric.value,
        rubric=rubric_text_for_metric(metric),
        scenario_brief=format_scenario_brief(scenario_prompt_data(scenario)),
        email_brief=format_generated_email_brief(generated_email_prompt_data(generated_email)),
    )


def scenario_prompt_data(scenario: EmailScenario) -> ScenarioPromptData:
    data: ScenarioPromptData = {
        "intent": scenario.intent,
        "key_facts": scenario.key_facts,
        "tone": scenario.tone,
    }
    if scenario.sender is not None:
        data["sender"] = scenario.sender
    if scenario.recipient is not None:
        data["recipient"] = scenario.recipient
    if scenario.affiliation is not None:
        data["affiliation"] = scenario.affiliation
    return data


def format_scenario_brief(data: ScenarioPromptData) -> str:
    lines = [
        f"**Intent:** {data['intent']}",
        "",
        "**Key facts:**",
        *[f"- {fact}" for fact in data["key_facts"]],
        "",
        f"**Tone:** {data['tone']}",
    ]
    if "sender" in data:
        lines.append(f"**Sender:** {data['sender']}")
    if "recipient" in data:
        lines.append(f"**Recipient:** {data['recipient']}")
    if "affiliation" in data:
        lines.append(f"**Affiliation:** {data['affiliation']}")
    return "\n".join(lines)


def generated_email_prompt_data(generated_email: GeneratedEmail) -> GeneratedEmailPromptData:
    return {
        "subject": generated_email.subject,
        "content": generated_email.content,
    }


def format_generated_email_brief(data: GeneratedEmailPromptData) -> str:
    return f"""**Subject:** {data["subject"]}

**Content:**
{data["content"]}"""
