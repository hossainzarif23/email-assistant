from src.models import MetricDefinition, MetricName, MetricRubricLevel


METRIC_DEFINITIONS: list[MetricDefinition] = [
    MetricDefinition(
        metric=MetricName.FACT_COVERAGE,
        title="Fact Coverage",
        description="Measures whether the generated email includes all required key facts accurately and naturally.",
        rubric=[
            MetricRubricLevel(score=0, description="The email ignores the required facts or contradicts them."),
            MetricRubricLevel(score=1, description="Only a tiny fragment of one required fact appears."),
            MetricRubricLevel(score=2, description="Some facts are present, but multiple important facts are missing or distorted."),
            MetricRubricLevel(score=3, description="Most facts are present, but one important fact is missing, weakened, or ambiguous."),
            MetricRubricLevel(score=4, description="Almost all required facts are present, with only a minor omission or awkward compression."),
            MetricRubricLevel(score=5, description="Every required fact is included accurately and naturally, with no unsupported factual claims."),
        ],
    ),
    MetricDefinition(
        metric=MetricName.TONE_ALIGNMENT,
        title="Tone Alignment",
        description="Measures whether the generated email matches the requested tone in context.",
        rubric=[
            MetricRubricLevel(score=0, description="The tone is absent, opposite of the requested tone, or unusable for the context."),
            MetricRubricLevel(score=1, description="The tone is very far from the requested tone."),
            MetricRubricLevel(score=2, description="The tone only loosely resembles the requested tone and is noticeably mismatched."),
            MetricRubricLevel(score=3, description="The tone is partly aligned but generic, uneven, or inconsistent."),
            MetricRubricLevel(score=4, description="The tone is mostly aligned with only small mismatches."),
            MetricRubricLevel(score=5, description="The tone closely and consistently matches the requested tone throughout."),
        ],
    ),
    MetricDefinition(
        metric=MetricName.PROFESSIONAL_STRUCTURE,
        title="Professional Email Structure",
        description="Measures whether the output works as a professional email.",
        rubric=[
            MetricRubricLevel(score=0, description="The output is not usable as an email."),
            MetricRubricLevel(score=1, description="It barely resembles a professional email or collapses greeting, body, closing, and signature into a flat single paragraph."),
            MetricRubricLevel(score=2, description="Some email elements are present, but structure is incomplete, hard to scan, or mostly unformatted."),
            MetricRubricLevel(score=3, description="Basic email content is present, but paragraphing, greeting, body, or sign-off formatting is noticeably weak."),
            MetricRubricLevel(score=4, description="The email is clear and professional with only minor structure or formatting rough edges."),
            MetricRubricLevel(score=5, description="The subject and body are polished, clear, concise, and formatted with distinct greeting, body paragraphing, and sign-off."),
        ],
    ),
]


def metric_definition_for(metric: MetricName) -> MetricDefinition:
    for definition in METRIC_DEFINITIONS:
        if definition.metric is metric:
            return definition
    raise ValueError(f"Unsupported metric: {metric}")


def rubric_text_for_metric(metric: MetricName) -> str:
    definition = metric_definition_for(metric)
    return "\n".join(f"{level.score} = {level.description}" for level in definition.rubric)
