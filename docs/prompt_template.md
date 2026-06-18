# Prompt Template

The generator supports two prompt strategies from `src.models.PromptStrategy`:

- `structured`
- `few_shot`

Both strategies use the same conceptual email inputs:

- `intent`
- `key_facts`
- `tone`

The `EmailScenario` model also supports optional identity context:

- `sender`
- `recipient`
- `affiliation`

Reference emails are part of the evaluation dataset only. They are not passed to the generation prompt.

## Output Contract

Both strategies instruct the model to return exactly one JSON object:

```json
{"subject": "string", "content": "string"}
```

The generated output is validated as `GeneratedEmail`, which requires non-empty `subject` and `content`.

## Scenario Brief Format

The prompt does not pass raw scenario JSON. It formats each scenario as a readable brief:

```markdown
**Intent:** Ask the meeting coordinator to provide exact waiting instructions for attendees coming to the May 17 meeting.

**Key facts:**
- The meeting is on May 17 at 11:00 A.M.
- The attendees are Kenneth Lay, Marty Sunde, and Bob Williams.
- The sender needs to know where the attendees should wait or go when they arrive.

**Tone:** Concise, Polite and Professional
**Sender:** Rosalee Fleming
**Recipient:** Sarah Whalen
**Affiliation:** Kenneth Lay's assistant
```

`Sender`, `Recipient`, and `Affiliation` are included only when present on the scenario.

## Strategy: `structured`

The `structured` strategy uses this role prompt and scenario brief:

```text
You are a helpful assistant specialized in writing emails.

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
{"subject": "string", "content": "string"}

Scenario data:
{scenario_brief}
```

## Strategy: `few_shot`

The `few_shot` strategy uses the same role prompt, identity rules, constraints, and output schema as `structured`. It inserts two examples before the live scenario:

```text
Examples:
{examples}

Scenario data:
{scenario_brief}
```

Each example is formatted as:

```text
Example {index}

Scenario data:
{scenario_brief}

Expected output:
{email_json}
```

## Few-Shot Example 1

Scenario data:

```markdown
**Intent:** Follow up after a client meeting

**Key facts:**
- Thank the recipient for their time
- Send the revised timeline
- Confirm that the next checkpoint is Wednesday

**Tone:** warm and professional
**Sender:** Jordan Lee
**Recipient:** Maya Patel
```

Expected output:

```json
{
  "subject": "Follow-up and revised timeline",
  "content": "Hi Maya,\n\nThank you for taking the time to meet today. I am sending over the revised timeline and confirming that our next checkpoint is Wednesday.\n\nPlease let me know if you have any questions before then.\n\nBest,\nJordan"
}
```

## Few-Shot Example 2

Scenario data:

```markdown
**Intent:** Request approval for a project budget

**Key facts:**
- Approval is needed by Friday
- The budget remains within $8,000
- Approval keeps the project on schedule

**Tone:** concise and polite
**Affiliation:** Northstar Consulting
```

Expected output:

```json
{
  "subject": "Budget approval requested by Friday",
  "content": "Hello [Recipient Name],\n\nCould you please review and approve the project budget by Friday? The budget remains within $8,000, and approval by then will keep the project on schedule.\n\nBest regards,\n[Your Name]\nNorthstar Consulting"
}
```

## No Hidden Chain-of-Thought

The generation prompt explicitly says:

```text
Do not reveal hidden reasoning or chain-of-thought. Only provide the subject and content of the email.
```

The prompt asks for the final email only. It does not request hidden reasoning, internal deliberation, or a rationale.
