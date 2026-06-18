## Metric 1: Fact Coverage

**Definition**: Measures whether the generated email includes all required key facts accurately and naturally.

**Evaluation Method**: LLM as a judge

**Rubric**:

| Score | Criteria |
| --- | --- |
| 0 | The email ignores the required facts or contradicts them. |
| 1 | Only a tiny fragment of one required fact appears. |
| 2 | Some facts are present, but multiple important facts are missing or distorted. |
| 3 | Most facts are present, but one important fact is missing, weakened, or ambiguous. |
| 4 | Almost all required facts are present, with only a minor omission or awkward compression. |
| 5 | Every required fact is included accurately and naturally, with no unsupported factual claims. |

## Metric 2: Tone Alignment

**Definition**: Measures whether the generated email matches the requested tone in context.

**Evaluation Method**: LLM as a judge

**Rubric**:

| Score | Criteria |
| --- | --- |
| 0 | The tone is absent, opposite of the requested tone, or unusable for the context. |
| 1 | The tone is very far from the requested tone. |
| 2 | The tone only loosely resembles the requested tone and is noticeably mismatched. |
| 3 | The tone is partly aligned but generic, uneven, or inconsistent. |
| 4 | The tone is mostly aligned with only small mismatches. |
| 5 | The tone closely and consistently matches the requested tone throughout. |

## Metric 3: Professional Email Structure

**Definition**: Measures whether the output works as a professional email.

**Evaluation Method**: LLM as a judge

**Rubric**:

| Score | Criteria |
| --- | --- |
| 0 | The output is not usable as an email. |
| 1 | It barely resembles a professional email or collapses greeting, body, closing, and signature into a flat single paragraph. |
| 2 | Some email elements are present, but structure is incomplete, hard to scan, or mostly unformatted. |
| 3 | Basic email content is present, but paragraphing, greeting, body, or sign-off formatting is noticeably weak. |
| 4 | The email is clear and professional with only minor structure or formatting rough edges. |
| 5 | The subject and body are polished, clear, concise, and formatted with distinct greeting, body paragraphing, and sign-off. |
