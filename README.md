# Typed JSON Drill

A small Python example that asks a language model to extract a task record and returns JSON only after schema validation.

## What it includes

- **Schema:** `TaskData` is a Pydantic model with required fields, length limits, a priority enum, and forbidden extra fields.
- **Structured generation:** the OpenAI Responses API receives the Pydantic model as its output format.
- **Validation:** Pydantic validates the parsed result again before the function returns it.
- **Retry/repair:** if parsing or validation fails, the next attempt includes the validation error as feedback. After three failed attempts, the program stops with an error instead of returning untrusted data.
- **Typed result:** `generate_task()` returns a `TaskData` instance, not an unchecked dictionary.

## Requirements

- Python 3.10+
- An OpenAI API key

## Run it

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

Set your API key in the environment:

```bash
# Windows PowerShell:
$env:OPENAI_API_KEY="your-api-key"

# macOS/Linux:
export OPENAI_API_KEY="your-api-key"
```

Run:

```bash
python main.py "Prepare slides for Friday project review and send them to the team"
```

Example shape of the output:

```json
{
  "title": "Prepare project review slides",
  "summary": "Prepare slides for Friday's project review and send them to the team.",
  "priority": "medium",
  "tags": ["slides", "project review"]
}
```

The exact generated values may differ.

Optionally choose a different supported model:

```bash
# Windows PowerShell:
$env:OPENAI_MODEL="gpt-4o-mini"

# macOS/Linux:
export OPENAI_MODEL="gpt-4o-mini"
```

## Design decisions and limitations

- I chose task extraction because it makes the schema easy to understand and test.
- I used a Pydantic model as the single source of truth for both the structured-output schema and runtime validation.
- Retries are bounded to avoid infinite loops. The program **does not** promise success if the API is unavailable, the model refuses, or every attempt fails; it fails closed and returns no invalid result.
- The API key is read from an environment variable and should never be committed to Git.

## Files

- `main.py` — schema, model call, validation, retry/repair, CLI.
- `requirements.txt` — dependencies.
- `.gitignore` — excludes secrets and local Python files.
