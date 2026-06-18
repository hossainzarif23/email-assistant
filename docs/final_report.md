# Final Report Template

Use this document as the source markdown for the final PDF or Google Doc report.
Complete it only after `data/scenarios.json` contains 10 unique scenarios and the full evaluation has been run.

All report content must be grounded in the evaluation JSON files under `artifacts/`. Do not invent scores, averages, examples, or conclusions that are not supported by the evaluation output.

## Prompt Summary

Fill after full evaluation.

- Strategy A: `structured`
- Strategy B: `few_shot`
- Brief summary of how each prompt works:
  - `structured`: [describe the prompt approach used]
  - `few_shot`: [describe the prompt approach used]

## Metric Definitions

Summarize the three custom metrics used in evaluation and how they are scored.

1. Fact Coverage
   - Definition: [fill from `docs/evaluation_metrics.md`]
   - Logic: [fill from `docs/evaluation_metrics.md`]

2. Tone Alignment
   - Definition: [fill from `docs/evaluation_metrics.md`]
   - Logic: [fill from `docs/evaluation_metrics.md`]

3. Professional Email Structure (`professional_structure`)
   - Definition: [fill from `docs/evaluation_metrics.md`]
   - Logic: [fill from `docs/evaluation_metrics.md`]

## Raw Data Reference

- Source files: the provider/strategy evaluation JSON files under `artifacts/`
- Optional companion file: `artifacts/evaluation_results.csv` if present
- Include the evaluation run date, model/configuration details, and any notes needed to interpret the run

## Comparative Analysis

Use the raw scenario results to compare the two strategies across all 10 scenarios.

- Overall averages: [fill from evaluation output]
- Metric-by-metric comparison: [fill from evaluation output]
- Scenario-level wins and losses: [fill from evaluation output]
- Notable strengths: [fill from evaluation output]
- Notable weaknesses: [fill from evaluation output]

## Biggest Failure Mode

Identify the single most important failure mode observed in the full evaluation.

- Failure mode: [fill after review]
- Evidence: [cite the affected scenarios from the evaluation JSON files]
- Impact: [describe why it matters]

## Production Recommendation

State which provider/strategy combination should be recommended for production and why.

- Recommendation: [choose based on evaluation data]
- Rationale: [grounded in metric averages and scenario-level behavior]
- Follow-up work: [list the most useful next improvements]

## Appendix

Optional: paste or summarize the key rows from the evaluation JSON files here for the final report package.
