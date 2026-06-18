# Evaluation Metrics

The evaluation pipeline runs one provider and one prompt strategy per output file. The CLI options are:

- `--provider gemini` or `--provider openai`
- `--strategy structured` or `--strategy few_shot`

Each run loads scenarios from `data/scenarios.json`, generates one email per selected scenario, runs three LLM-as-judge metrics, and writes one JSON report with this top-level shape:

```json
{
  "source_file": "data/scenarios.json",
  "provider": "gemini",
  "strategy": "structured",
  "metric_definitions": [],
  "results": [],
  "metric_averages": {},
  "overall_average": 0.0
}
```

`metric_definitions` contains exactly three objects with `metric`, `definition`, and `rubric`. The rubric is the scoring logic. `results` contains one object per scenario with `scenario_id` and a `metrics` array. Each metric result has `metric`, `score`, and `reason`.

## Judge Contract

The evaluator builds one judge prompt per metric. Each judge receives:

- the scenario data: `intent`, `key_facts`, `tone`, plus optional `sender`, `recipient`, and `affiliation`
- the generated email data: `subject` and `content`
- the metric-specific rubric

Each judge must return exactly one JSON object:

```json
{"score": 0, "reason": "string"}
```

The shared scoring rules in `src/prompts.py` are:

- Return an integer score from 0 to 5.
- Score should be an integer.
- Do not reward quality outside this metric.
- Score critically. A competent but ordinary email should usually be 3 or 4, not 5.
- Use 5 only when the email fully satisfies the metric with no meaningful weakness.
- Do not penalize valid paraphrasing.
- Do not infer facts that are not present in the scenario or generated email.
- Base the reason on concrete evidence.
- For `professional_structure`, evaluate the actual subject and content formatting, not just whether the facts are present.
- For `professional_structure`, a single-paragraph content field with inline greeting, body, closing, and signature must receive a low score, normally 1 or 2.
- For `professional_structure`, a score of 5 requires distinct greeting, body paragraphing, closing, and signature formatting.
- For `tone_alignment`, do not give 5 if the tone is merely acceptable but generic.
- For `fact_coverage`, do not give 5 if any required fact is only implied, weakened, ambiguous, or mixed with unsupported detail.

## Aggregation

For each metric, the evaluator averages that metric's scores across the scenarios in the run. `overall_average` is the mean of the three metric averages.

If no scenarios are selected, each metric average is `0.0` and `overall_average` is `0.0`.

## Metric 1: Fact Coverage

Metric key: `fact_coverage`

Definition: Measures whether the generated email includes all required key facts accurately and naturally.

Rubric:

- 0: The email ignores the required facts or contradicts them.
- 1: Only a tiny fragment of one required fact appears.
- 2: Some facts are present, but multiple important facts are missing or distorted.
- 3: Most facts are present, but one important fact is missing, weakened, or ambiguous.
- 4: Almost all required facts are present, with only a minor omission or awkward compression.
- 5: Every required fact is included accurately and naturally, with no unsupported factual claims.

## Metric 2: Tone Alignment

Metric key: `tone_alignment`

Definition: Measures whether the generated email matches the requested tone in context.

Rubric:

- 0: The tone is absent, opposite of the requested tone, or unusable for the context.
- 1: The tone is very far from the requested tone.
- 2: The tone only loosely resembles the requested tone and is noticeably mismatched.
- 3: The tone is partly aligned but generic, uneven, or inconsistent.
- 4: The tone is mostly aligned with only small mismatches.
- 5: The tone closely and consistently matches the requested tone throughout.

## Metric 3: Professional Email Structure

Metric key: `professional_structure`

Definition: Measures whether the output works as a professional email.

Rubric:

- 0: The output is not usable as an email.
- 1: It barely resembles a professional email or collapses greeting, body, closing, and signature into a flat single paragraph.
- 2: Some email elements are present, but structure is incomplete, hard to scan, or mostly unformatted.
- 3: Basic email content is present, but paragraphing, greeting, body, or sign-off formatting is noticeably weak.
- 4: The email is clear and professional with only minor structure or formatting rough edges.
- 5: The subject and body are polished, clear, concise, and formatted with distinct greeting, body paragraphing, and sign-off.
