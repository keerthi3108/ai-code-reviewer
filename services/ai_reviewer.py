"""AI-powered code review using Groq or OpenAI."""
import json
import re
from typing import Any, Optional

from config import (
    AI_PROVIDER,
    GROQ_API_KEY,
    GROQ_MODEL,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    PERSONALITIES,
)


REVIEW_SCHEMA = """
Return ONLY valid JSON (no markdown fences) with this structure:
{
  "summary": "2-3 sentence executive summary",
  "scores": {
    "readability": 0-100,
    "scalability": 0-100,
    "production_readiness": 0-100,
    "maintainability": 0-100,
    "security": 0-100,
    "performance": 0-100
  },
  "issues": [
    {
      "type": "bug|performance|security|practice|smell",
      "severity": "critical|high|medium|low|info",
      "title": "short title",
      "message": "detailed explanation",
      "line": 0,
      "file": "filename or null",
      "suggestion": "how to fix"
    }
  ],
  "inline_comments": [
    {
      "line": 0,
      "severity": "critical|high|medium|low|info",
      "comment": "PR-style inline comment",
      "suggestion": "optional code snippet"
    }
  ],
  "fixes": ["actionable fix 1", "actionable fix 2"],
  "optimized_code": "full improved code or empty if minor changes",
  "refactored_code": "refactored version emphasizing structure",
  "strengths": ["good pattern 1"],
  "recommendations": ["recommendation 1"]
}
"""


def _build_prompt(code: str, language: str, personality_key: str, filename: str) -> str:
    personality = PERSONALITIES.get(personality_key, PERSONALITIES["friendly_mentor"])
    return f"""You are an expert code reviewer acting as: {personality['name']}.
Review tone: {personality['tone']}

Analyze the following {language} code thoroughly. Detect:
- Bugs and logic errors
- Performance bottlenecks
- Security vulnerabilities (OWASP-style)
- Bad practices and anti-patterns
- Code smells

Provide production-quality review with scores, inline PR comments, fixes, optimized code, and refactored code.
Filename/context: {filename}

{REVIEW_SCHEMA}

CODE TO REVIEW:
```
{code}
```
"""


def _extract_json(text: str) -> dict:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fence:
        text = fence.group(1)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
        raise


def _call_groq(prompt: str) -> str:
    from groq import Groq

    client = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": "You are a senior staff engineer performing code reviews. Output valid JSON only."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=8000,
    )
    return response.choices[0].message.content or ""


def _call_openai(prompt: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "You are a senior staff engineer performing code reviews. Output valid JSON only."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=8000,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content or ""


def _fallback_review(code: str, language: str, error: str) -> dict:
    """Rule-based fallback when API is unavailable."""
    issues = []
    lines = code.splitlines()

    patterns = [
        (r"eval\s*\(", "critical", "security", "Avoid eval() - code injection risk"),
        (r"exec\s*\(", "critical", "security", "Avoid exec() - arbitrary code execution"),
        (r"password\s*=\s*['\"]", "high", "security", "Hardcoded password detected"),
        (r"except\s*:", "medium", "practice", "Bare except clause - catch specific exceptions"),
        (r"import \*", "medium", "smell", "Wildcard import pollutes namespace"),
        (r"print\s*\(", "low", "practice", "Debug print statement in production code"),
        (r"time\.sleep", "medium", "performance", "Blocking sleep may impact performance"),
        (r"TODO|FIXME|HACK", "info", "smell", "Unresolved TODO/FIXME comment"),
    ]

    for i, line in enumerate(lines, 1):
        for pattern, severity, itype, msg in patterns:
            if re.search(pattern, line, re.IGNORECASE):
                issues.append({
                    "type": itype,
                    "severity": severity,
                    "title": msg[:60],
                    "message": msg,
                    "line": i,
                    "file": None,
                    "suggestion": "Refactor or remove this pattern",
                })

    line_count = len(lines)
    base = max(40, 100 - len(issues) * 5)

    return {
        "summary": f"Offline heuristic review ({error}). Configure API keys for full AI analysis.",
        "scores": {
            "readability": min(95, base + 10),
            "scalability": base,
            "production_readiness": max(30, base - 10),
            "maintainability": base,
            "security": max(25, base - len([x for x in issues if x["type"] == "security"]) * 10),
            "performance": base,
        },
        "issues": issues[:20],
        "inline_comments": [
            {"line": iss["line"], "severity": iss["severity"], "comment": iss["message"], "suggestion": iss.get("suggestion", "")}
            for iss in issues[:10]
        ],
        "fixes": [iss["suggestion"] for iss in issues[:5]],
        "optimized_code": "",
        "refactored_code": "",
        "strengths": ["Code structure parseable for static analysis"],
        "recommendations": ["Add GROQ_API_KEY or OPENAI_API_KEY to .env for AI-powered review"],
        "_fallback": True,
    }


def get_api_status() -> dict:
    groq_ok = bool(GROQ_API_KEY)
    openai_ok = bool(OPENAI_API_KEY)
    return {
        "groq": groq_ok,
        "openai": openai_ok,
        "provider": AI_PROVIDER,
        "ready": (AI_PROVIDER == "groq" and groq_ok) or (AI_PROVIDER == "openai" and openai_ok) or groq_ok or openai_ok,
    }


def review_code(
    code: str,
    language: str = "python",
    personality_key: str = "friendly_mentor",
    filename: str = "pasted_code",
) -> dict[str, Any]:
    """Run AI code review and return structured results."""
    prompt = _build_prompt(code, language, personality_key, filename)

    try:
        if AI_PROVIDER == "openai" and OPENAI_API_KEY:
            raw = _call_openai(prompt)
        elif GROQ_API_KEY:
            raw = _call_groq(prompt)
        elif OPENAI_API_KEY:
            raw = _call_openai(prompt)
        else:
            return _fallback_review(code, language, "No API key configured")

        result = _extract_json(raw)
        result["_fallback"] = False
        return _normalize_review(result, code)

    except Exception as e:
        return _fallback_review(code, language, str(e))


def _normalize_review(data: dict, original_code: str) -> dict:
    """Ensure all expected fields exist with defaults."""
    scores = data.get("scores") or {}
    default_scores = {
        "readability": 70, "scalability": 70, "production_readiness": 70,
        "maintainability": 70, "security": 70, "performance": 70,
    }
    for k, v in default_scores.items():
        scores.setdefault(k, v)
        scores[k] = max(0, min(100, int(scores.get(k, v))))

    return {
        "summary": data.get("summary", "Review completed."),
        "scores": scores,
        "issues": data.get("issues") or [],
        "inline_comments": data.get("inline_comments") or [],
        "fixes": data.get("fixes") or [],
        "optimized_code": data.get("optimized_code") or "",
        "refactored_code": data.get("refactored_code") or "",
        "strengths": data.get("strengths") or [],
        "recommendations": data.get("recommendations") or [],
        "_fallback": data.get("_fallback", False),
        "original_code": original_code,
    }
