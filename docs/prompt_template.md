# Prompt Template

This project compares two prompt strategies for the same email generation task.

## Shared Contract

Both strategies accept exactly three conceptual inputs:

- `intent`
- `key_facts`
- `tone`

Optional identity context may also be present:

- `sender`
- `recipient`
- `affiliation`

The model must return exactly one JSON object with this schema:

```json
{"subject": "...", "content": "..."}
```

The output is a professional email, not an explanation of how the answer was produced.

## Strategy A: Structured Role Prompt

Strategy A uses a direct role-based instruction set with a single readable scenario brief.

Core instruction themes:

- write professional emails from a brief intent, required facts, and tone
- use only the provided facts
- do not invent names, dates, commitments, or background details
- output JSON only, with `subject` and `content`
- format the scenario as a human-readable brief using labeled fields and bullet facts, rather than raw JSON
- return the email body as plain text with distinct greeting, body, and closing blocks

Scenario input format:

```markdown
**Intent:** Ask the meeting coordinator to provide exact waiting instructions for attendees coming to the May 17 meeting.

**Key facts:**
- The meeting is on May 17 at 11:00 A.M.
- The attendees are Kenneth Lay, Marty Sunde, and Bob Williams.
- The sender needs to know where the attendees should wait or go when they arrive.

**Tone:** concise, polite and professional
**Sender:** Rosalee Fleming
**Recipient:** Sarah Whalen
**Affiliation:** Kenneth Lay's assistant
```

Identity behavior:

- when `sender`, `recipient`, and `affiliation` are present, use them naturally
- if `recipient` is missing but obvious from the scenario, infer it; otherwise use `[Recipient Name]`
- if `sender` is missing but obvious from the scenario, infer it; otherwise use `[Your Name]`
- if `affiliation` is missing but obvious from the scenario, infer it; otherwise omit it
- never invent a person, role, company, date, commitment, or other identity detail

## Strategy B: Role Prompt Plus Few-Shot Examples

Strategy B uses the same role prompt and output contract as Strategy A, then adds two worked examples before the live scenario.

The examples show:

- how the scenario brief is structured
- how a polished subject line looks
- how facts are integrated naturally in the body
- how identity context may be used when available

The live scenario still follows the same rules:

- do not copy example text mechanically
- do not invent unsupported details
- return only the JSON object

## Reference Emails

Reference emails are part of the evaluation dataset, not generator input. The generator prompt receives only the scenario fields needed to draft the email: `intent`, `key_facts`, `tone`, and optional identity fields. This keeps the prompt strategy comparison focused on generation quality rather than copying or paraphrasing the reference email.

## No Hidden Chain-of-Thought

The prompt does not request hidden reasoning or internal deliberation.

The model is instructed to produce the final email only, in the declared JSON schema, without commentary or extra keys. The email body itself must be plain text, not HTML or Markdown.
