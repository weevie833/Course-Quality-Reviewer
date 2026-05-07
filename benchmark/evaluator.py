"""
Criterion evaluator — structural (regex) and semantic (Claude-as-judge).
"""

import json
import re

from anthropic import Anthropic

_client = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic()
    return _client


def evaluate_structural(response: str, criterion: dict) -> tuple[float, str]:
    """Return (score 0.0|1.0, reason)."""
    if "check_present" in criterion:
        pattern = criterion["check_present"]
        if re.search(pattern, response, re.IGNORECASE | re.MULTILINE):
            return 1.0, "Pattern found"
        return 0.0, f"Pattern not found: {pattern}"

    if "check_absent" in criterion:
        pattern = criterion["check_absent"]
        m = re.search(pattern, response, re.IGNORECASE | re.MULTILINE)
        if m is None:
            return 1.0, "Forbidden pattern correctly absent"
        return 0.0, f"Forbidden pattern found: '{m.group()}'"

    if "check_contains" in criterion:
        needle = criterion["check_contains"].lower()
        if needle in response.lower():
            return 1.0, "Text found"
        return 0.0, f"Text not found: {criterion['check_contains']}"

    return 0.0, "Unknown structural criterion type"


def evaluate_semantic(query: str, response: str, criterion: dict) -> tuple[float, str]:
    """Return (score 0.0|0.5|1.0, reason) using Claude Haiku as judge."""
    rubric = criterion["rubric"]

    prompt = f"""You are evaluating an AI assistant's response against a specific quality criterion.

USER QUERY:
{query}

AI RESPONSE:
{response[:3000]}

EVALUATION CRITERION:
{rubric}

Score the response ONLY on this criterion:
- 1.0: Fully meets the criterion
- 0.5: Partially meets (correct direction but incomplete or minor errors)
- 0.0: Does not meet the criterion

Respond with ONLY a JSON object, no other text:
{{"score": 0.0, "reason": "brief one-sentence explanation"}}"""

    result = _get_client().messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )

    text = result.content[0].text.strip()
    # Strip any markdown code fences the model may add
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
    data = json.loads(text)
    return float(data["score"]), data["reason"]
