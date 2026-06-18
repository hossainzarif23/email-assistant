# Email Generation Assistant

This repository contains a small Python 3.11 assessment prototype that generates professional emails from three inputs:
`intent`, `key_facts`, and `tone`.

## Setup

Use the bundled virtual environment:

```powershell
.\venv\Scripts\python -m pip install -r requirements.txt
```

Create a local `.env` file with the documented variables only:

```env
GOOGLE_API_KEY=your_google_api_key
GEMINI_MODEL=gemini-3.1-flash-lite

OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-5.4-mini
```

Only set the API key for the provider you plan to use. `GEMINI_MODEL` and `OPENAI_MODEL` are optional and default to the models shown above. The judge model is fixed to `gpt-5.4-mini`, so `OPENAI_MODEL` only affects OpenAI generation.

## Testing

Run mocked unit tests only:

```powershell
.\venv\Scripts\python -m pytest tests -q -m "not integration"
```

Run live Gemini integration tests:

```powershell
.\venv\Scripts\python -m pytest tests -q -m integration
```

The integration tests load `.env` from the repository root and skip automatically if `GOOGLE_API_KEY` is not available.

## Generate

Run the generator from the command line:

```powershell
.\venv\Scripts\python -m src.cli generate --intent "Follow up after the meeting" --fact "Thank the recipient for their time" --fact "Share the revised timeline" --tone "warm and professional"
```

Add `--sender`, `--recipient`, and `--affiliation` when that identity context is known. Use `--provider gemini` or `--provider openai` to choose the model provider. The CLI prints a JSON object with `subject` and `content`.

## Evaluate

Smoke test a single scenario:

```powershell
.\venv\Scripts\python -m src.cli evaluate --limit 1
```

Run the full evaluation for one provider and one strategy:

```powershell
.\venv\Scripts\python -m src.cli evaluate --scenarios data/scenarios.json --provider gemini --strategy structured --output artifacts/gemini-structured-evaluation.json
```

Use `--provider gemini` or `--provider openai` to select the model provider. Use `--strategy structured` or `--strategy few_shot` to select the prompt strategy. Each evaluation report JSON represents one provider and one strategy, and includes the source file, metric definitions and rubrics, per-scenario metric scores, per-metric averages, and overall average.

The judge is fixed to `gpt-5.4-mini` for every evaluation run, regardless of the generation provider or prompt strategy, so score comparisons stay on the same judge model.

## Assessment Data

`data/scenarios.json` contains 10 unique scenarios, each with intent, key facts, tone, and a human reference email.

## Final Report

Complete the final report only after all provider and strategy combinations needed for comparison have been run.

Use the evaluation JSON files under `artifacts/` as the raw data source for the report. Then update [docs/final_report.md](docs/final_report.md) with:

- a short prompt summary
- the metric definitions and logic
- a reference to the raw evaluation data
- comparative analysis between the evaluated providers and strategies
- the biggest failure mode
- the production recommendation

Keep the report grounded in the evaluated output. Do not invent metric scores, averages, or examples that are not present in the evaluation artifacts.

## Prompt Strategy

The generator supports two prompt strategies:

- `structured`: a direct role prompt with explicit instructions and a readable scenario brief.
- `few_shot`: the same role prompt plus two worked examples before the live scenario.

Both strategies use the same output schema: `{"subject": "...", "content": "..."}`.

The prompt avoids invented identity details. If `recipient` or `sender` is missing but obvious from the scenario, the model may infer it; otherwise it uses `[Recipient Name]` or `[Your Name]`. If `affiliation` is missing and not obvious, the model omits it.

See [docs/prompt_template.md](docs/prompt_template.md) for the full prompt design.

## Evaluation Metrics

The evaluation uses three custom LLM-as-judge metrics:

- Fact Coverage
- Tone Alignment
- Professional Email Structure (`professional_structure`)

Each judge scores on a 0-5 scale and returns only a numeric score plus a short reason. See [docs/evaluation_metrics.md](docs/evaluation_metrics.md) for the rubric logic and separation strategy.

## Comparison Rationale

Each evaluation run covers one provider and one prompt strategy. Run the same 10 scenarios and three metrics for each combination being compared, then write the final comparison from those raw evaluation artifacts.
