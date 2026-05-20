from __future__ import annotations

import os
from typing import Any

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")


def _build_prompt(overview: dict[str, Any], activity: list[dict[str, Any]], at_risk_count: int) -> str:
    top_activities = ", ".join(
        f"{a['activity']} ({a['count']})" for a in activity[:4]
    ) or "N/A"

    return f"""You are an educational data analyst. Based on the following learning analytics summary, write a concise 3-4 sentence insight paragraph for an instructor dashboard. Be specific and actionable.

Data summary:
- Total students: {overview.get("total_students", "N/A")}
- Total interactions: {overview.get("total_interactions", "N/A")}
- Average score: {overview.get("average_score", "N/A")}
- Active last 7 days: {overview.get("active_last_7_days", "N/A")}
- At-risk students: {at_risk_count}
- Top activities: {top_activities}

Write the insight paragraph directly, no headers or bullet points."""


async def generate_insights(
    overview: dict[str, Any],
    activity: list[dict[str, Any]],
    at_risk_count: int,
    provider: str = "gemini",
) -> dict[str, str]:
    prompt = _build_prompt(overview, activity, at_risk_count)

    if provider == "openai":
        return await _call_openai(prompt)
    if provider == "gemini":
        return await _call_gemini(prompt)
    return await _call_groq(prompt)


async def _call_openai(prompt: str) -> dict[str, str]:
    if not OPENAI_API_KEY:
        return {"error": "OpenAI API key not configured.", "provider": "openai"}
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250,
            temperature=0.7,
        )
        return {
            "insight": response.choices[0].message.content.strip(),
            "provider": "openai",
            "model": "gpt-4o-mini",
        }
    except Exception as exc:
        return {"error": str(exc), "provider": "openai"}


async def _call_groq(prompt: str) -> dict[str, str]:
    if not GROQ_API_KEY:
        return {"error": "Groq API key not configured.", "provider": "groq"}
    try:
        from groq import AsyncGroq
        client = AsyncGroq(api_key=GROQ_API_KEY)
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250,
            temperature=0.7,
        )
        return {
            "insight": response.choices[0].message.content.strip(),
            "provider": "groq",
            "model": "llama-3.3-70b-versatile",
        }
    except Exception as exc:
        return {"error": str(exc), "provider": "groq"}


async def _call_gemini(prompt: str) -> dict[str, str]:
    if not GOOGLE_API_KEY:
        return {"error": "Google API key not configured.", "provider": "gemini"}
    try:
        from google import genai
        client = genai.Client(api_key=GOOGLE_API_KEY)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        return {
            "insight": response.text.strip(),
            "provider": "gemini",
            "model": "gemini-2.0-flash",
        }
    except Exception as exc:
        return {"error": str(exc), "provider": "gemini"}
