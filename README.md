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

Only set the API key for the provider you plan to use. `GEMINI_MODEL` and `OPENAI_MODEL` are optional and default to the models shown above.

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

Run the full evaluation and write structured output to `artifacts/evaluation_results.json`:

```powershell
.\venv\Scripts\python -m src.cli evaluate --scenarios data/scenarios.json --output artifacts/evaluation_results.json
```

Use `--provider gemini` or `--provider openai` to run generation and judging with the selected provider. The evaluation report JSON includes per-scenario results, metric definitions, strategy aggregates, and the winner.

## Assessment Data

`data/scenarios.json` is user-maintained. The checked-in file is currently a smoke-test sample only.
Before the final assessment run or submission, expand or replace it with 10 unique scenarios, each with intent, key facts, tone, and a human reference email.
The smoke-test sample is not sufficient for final evaluation.

## Final Report

Complete the final report only after `data/scenarios.json` contains all 10 unique scenarios and the full evaluation has been run.

Use `artifacts/evaluation_results.json` as the raw data source for the report. Then update [docs/final_report.md](docs/final_report.md) with:

- a short prompt summary
- the metric definitions and logic
- a reference to the raw evaluation data
- comparative analysis between the two strategies
- the biggest failure mode
- the production recommendation

Keep the report grounded in the evaluated output. Do not invent metric scores, averages, or examples that are not present in `artifacts/evaluation_results.json`.

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

## Provider Comparison Rationale

Both prompt strategies are evaluated with the same provider and model configuration for a given run so the comparison isolates prompt design instead of model capability. Gemini is the default provider. OpenAI can be selected with `--provider openai`.
