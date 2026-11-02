from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from ai.knowledge import KnowledgeBase
from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
from core import database as db

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the AI security assistant of an authorized camera monitoring system.
Answer questions using ONLY the provided company knowledge base excerpts. If the answer is not in the
knowledge base, say that clearly and suggest adding the document. Do not invent names, policies, or facts.
Be concise, professional, and safety-aware. For risk questions, state that AI output is advisory and a
human must verify it. Never provide instructions for harming people or bypassing security.
"""


class SecurityAgent:
    def __init__(self, knowledge: KnowledgeBase, translator=None) -> None:
        self.knowledge = knowledge
        self.translator = translator
        self.enabled = bool(OPENAI_API_KEY)

    @property
    def provider(self) -> str:
        if self.enabled:
            return f"openai:{OPENAI_MODEL}"
        return "local-rag"

    def _llm(self, system: str, user: str, max_tokens: int = 700) -> str:
        if not OPENAI_API_KEY:
            raise RuntimeError("LLM not configured")
        from openai import OpenAI

        client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            temperature=0.15,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            timeout=40,
        )
        return (response.choices[0].message.content or "").strip()

    def ask(self, question: str, language: str = "en", use_llm: bool = True) -> dict[str, Any]:
        question = (question or "").strip()
        if not question:
            return {"answer": "Please enter a question.", "sources": [], "provider": self.provider}
        results = self.knowledge.search(question, k=4)
        context = "\n\n".join(
            f"--- {r['title']} ({r['source']}) ---\n{r['text']}" for r in results
        ) or "No matching knowledge base content was found."
        answer = ""
        provider = "local-rag"
        if OPENAI_API_KEY and use_llm:
            try:
                answer = self._llm(
                    SYSTEM_PROMPT,
                    (
                        f"Company knowledge base excerpts:\n{context}\n\n"
                        f"Visitor question: {question}\n\n"
                        f"Answer in {'Arabic' if language == 'ar' else 'English'}. "
                        "Mention the source document titles you used."
                    ),
                )
                provider = self.provider
            except Exception as exc:  # noqa: BLE001
                log.warning("LLM answer failed, using local knowledge: %s", exc)
        if not answer:
            local = self.knowledge.answer(question, k=4)
            answer = local["answer"]
            results = [r for r in results]
            if language == "ar" and self.translator:
                try:
                    answer = self.translator.translate(answer, target="ar", source="en")
                except Exception:  # noqa: BLE001
                    pass
        sources = [
            {"title": r["title"], "source": r["source"], "score": r["score"]} for r in results
        ]
        self._save_conversation(question, answer, sources, provider)
        return {"answer": answer, "sources": sources, "provider": provider, "question": question}

    def assess(self, language: str = "en") -> dict[str, Any]:
        since = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat(timespec="seconds")
        events = db.fetch_all(
            "SELECT kind, severity, title, description, person_name, created_at, meta "
            "FROM events WHERE created_at >= ? ORDER BY id DESC LIMIT 120",
            (since,),
        )
        stats = db.fetch_one(
            "SELECT "
            "(SELECT COUNT(*) FROM people) AS people, "
            "(SELECT COUNT(*) FROM vehicles) AS vehicles, "
            "(SELECT COUNT(*) FROM events WHERE created_at >= ?) AS events_today, "
            "(SELECT COUNT(*) FROM events WHERE severity='critical' AND created_at >= ?) AS critical_today, "
            "(SELECT COUNT(*) FROM events WHERE severity='warning' AND created_at >= ?) AS warnings_today",
            (since, since, since),
        ) or {}
        known_names = sorted({e["person_name"] for e in events if e.get("person_name")})
        critical = [e for e in events if e["severity"] == "critical"]
        warnings = [e for e in events if e["severity"] == "warning"]
        score = min(100, len(critical) * 35 + len(warnings) * 8 + (20 if stats.get("events_today", 0) > 30 else 0))
        if score >= 65:
            level = "high"
            summary = "High risk signal. At least one critical alert was recorded in the last 24 hours."
            actions = [
                "Review every critical alert and its evidence snapshot immediately.",
                "Verify restricted-item detections by video; model output can be wrong.",
                "Send a human officer to the location of the most recent critical alert.",
            ]
        elif score >= 25:
            level = "medium"
            summary = "Attention needed. There were warnings or an unusual number of events."
            actions = [
                "Review unresolved warnings and unknown-person events.",
                "Confirm whether detected items are legitimate work tools.",
                "Keep audio monitoring and face recognition within local legal approval.",
            ]
        else:
            level = "low"
            summary = "No major AI alerts in the last 24 hours. Continue routine monitoring."
            actions = [
                "Keep the knowledge base and vehicle registry up to date.",
                "Test the camera and microphone weekly.",
                "Review access consent records periodically.",
            ]

        details = (
            f"Last 24h: {stats.get('events_today', 0)} events, {len(critical)} critical, "
            f"{len(warnings)} warnings. Registered people: {stats.get('people', 0)}. "
            f"Registered vehicles: {stats.get('vehicles', 0)}. Known names seen: "
            f"{', '.join(known_names) if known_names else 'none'}."
        )
        answer = f"Risk level: {level.upper()}. {summary}\n\n{details}\n\nRecommended actions:\n" + "\n".join(
            f"- {item}" for item in actions
        )
        provider = "rules"
        if OPENAI_API_KEY and events:
            compact = [
                {
                    "kind": e["kind"],
                    "severity": e["severity"],
                    "title": e["title"],
                    "person": e.get("person_name") or "",
                    "time": e["created_at"],
                }
                for e in events[:40]
            ]
            try:
                llm_text = self._llm(
                    SYSTEM_PROMPT,
                    (
                        "You are producing an advisory security assessment. Data (JSON):\n"
                        + json.dumps({"stats": stats, "events": compact}, ensure_ascii=False)
                        + "\nReturn: risk level (low/medium/high), a short summary, and three recommended actions. "
                        "Emphasize human verification. Do not claim an item is definitely a weapon."
                    ),
                    max_tokens=500,
                )
                if llm_text:
                    answer = llm_text
                    provider = self.provider
            except Exception as exc:  # noqa: BLE001
                log.warning("LLM assessment failed: %s", exc)
        if language == "ar" and self.translator:
            try:
                answer = self.translator.translate(answer, target="ar", source="en")
            except Exception:  # noqa: BLE001
                pass
        return {
            "risk_level": level,
            "risk_score": score,
            "summary": summary,
            "answer": answer,
            "recommendations": actions,
            "stats": stats,
            "provider": provider,
        }

    @staticmethod
    def _save_conversation(question: str, answer: str, sources: list[dict], provider: str) -> None:
        try:
            db.execute(
                "INSERT INTO conversations(question, answer, sources, provider, created_at) VALUES(?,?,?,?,?)",
                (
                    question[:3000],
                    answer[:12000],
                    json.dumps(sources, ensure_ascii=False)[:4000],
                    provider,
                    db.utcnow(),
                ),
            )
        except Exception:  # noqa: BLE001
            log.debug("Could not save conversation", exc_info=True)
