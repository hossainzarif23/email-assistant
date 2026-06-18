# Evaluation Metrics

The evaluation pipeline uses three separate LLM-as-judge prompts. Each prompt is narrowly scoped to one dimension so the judges do not blur multiple concerns into a single score.

All three judges follow the same output contract:

- return JSON only
- return `score` and `reason`
- score on a 0-5 scale
- keep the reason short and specific

## Why Separate Judges

A single broad judge often mixes factual coverage, tone, and structure into one opinion. That creates metric bleed and makes it hard to tell whether a prompt helped with facts, style, or formatting.

Separate judges reduce that problem because:

- each prompt states exactly one rubric
- each score is interpreted against one dimension only
- the resulting averages are easier to compare across strategies

## Metric 1: Fact Coverage

Purpose: verify that every required fact appears naturally and accurately.

What the judge should consider:

- whether the required facts are present
- whether any required fact is contradicted
- whether the email adds unsupported factual claims that change meaning

Scoring guide:

- 0: facts are ignored or contradicted
- 1: only a tiny fragment of a fact appears
- 2: some facts are present, but multiple important facts are missing or distorted
- 3: most facts are present, but one or two important fact is missing, weakened, or ambiguous
- 4: almost all facts are present with only minor omission or awkwardness
- 5: all required facts are present accurately and naturally, with no unsupported factual claims

## Metric 2: Tone Alignment

Purpose: judge whether the email matches the requested tone.

What the judge should consider:

- warmth, directness, politeness, urgency, or other requested tonal cues
- whether the tone stays consistent across the email
- whether the tone suits the scenario context

Scoring guide:

- 0: tone is opposite of the request
- 1: tone is very far from the request
- 2: tone only loosely resembles the request and is noticeably mismatched
- 3: tone is partly aligned but generic or inconsistent
- 4: tone is mostly aligned with small mismatches
- 5: tone closely and consistently matches the request throughout

## Metric 3: Professional Email Structure (`professional_structure`)

Purpose: judge whether the output is structured like a useful professional email.

What the judge should consider:

- subject relevance
- greeting and closing quality
- organization and readability
- conciseness and clarity
- grammar and overall polish

Scoring guide:

- 0: not usable as an email
- 1: barely resembles a professional email and lacks multiple major elements
- 2: some email elements are present, but structure is incomplete or hard to follow
- 3: basic email structure is present, but organization or formatting is noticeably weak
- 4: well structured with only minor rough edges
- 5: subject and body are polished, clear, complete, and appropriate for a professional email

## Judge Prompt Pattern

Each metric uses its own prompt with:

- the scenario data
- the generated email data
- a metric-specific rubric
- a JSON-only response requirement

The prompt explicitly tells the judge not to evaluate the other two metrics.
