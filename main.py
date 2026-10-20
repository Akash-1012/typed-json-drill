"""Return schema-validated, typed JSON from an OpenAI model."""

from enum import Enum
import os
import sys
import time
from typing import Type

from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskData(BaseModel):
    """The exact data contract returned by the model."""

    model_config = ConfigDict(extra="forbid", strict=True)

    title: str = Field(min_length=1, max_length=100)
    summary: str = Field(min_length=1, max_length=500)
    priority: Priority
    tags: list[str] = Field(min_length=1, max_length=8)


SYSTEM_PROMPT = """Extract a concise task record from the user's text.
Return only data matching the supplied schema.
Do not invent details. If priority is unclear, use medium.
Keep title and summary non-empty; tags must be short strings."""


def generate_task(text: str, max_attempts: int = 3) -> TaskData:
    """Return a validated TaskData object or raise an error (fail closed)."""
    if not text.strip():
        raise ValueError("Input text cannot be empty.")
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1.")

    client = OpenAI()
    repair_feedback = ""

    for attempt in range(1, max_attempts + 1):
        prompt = f"Text to extract:\n{text}"
        if repair_feedback:
            prompt += (
                "\n\nYour previous attempt failed validation. "
                "Correct the output using this feedback:\n"
                f"{repair_feedback}"
            )

        try:
            response = client.responses.parse(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                input=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                text_format=TaskData,
            )

            result = response.output_parsed
            if result is None:
                raise ValueError("The model returned no parsed result (possibly a refusal).")

            # Explicit second validation boundary before data leaves this function.
            return TaskData.model_validate(result.model_dump(), strict=True)

        except (ValidationError, ValueError) as exc:
            repair_feedback = str(exc)
            if attempt == max_attempts:
                raise RuntimeError(
                    f"Could not produce valid TaskData after {max_attempts} attempts."
                ) from exc
            time.sleep(0.25 * attempt)

    raise RuntimeError("Unexpected retry-loop exit.")


def main() -> None:
    text = " ".join(sys.argv[1:]).strip()
    if not text:
        print('Usage: python main.py "Prepare slides for Friday project review"', file=sys.stderr)
        raise SystemExit(2)

    try:
        task = generate_task(text)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)

    # model_dump_json emits valid JSON; the Pydantic instance is typed and validated.
    print(task.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
