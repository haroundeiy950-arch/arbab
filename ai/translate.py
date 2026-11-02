from __future__ import annotations

import logging
import re
import threading
from collections import OrderedDict
from typing import Iterable

import requests

from config import LIBRETRANSLATE_URL, OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL

log = logging.getLogger(__name__)

_MYMEMORY_LANG = {
    "en": "en",
    "ar": "ar",
    "fr": "fr",
    "es": "es",
    "de": "de",
    "it": "it",
    "pt": "pt",
    "ru": "ru",
    "tr": "tr",
    "ur": "ur",
    "hi": "hi",
    "fa": "fa",
    "zh": "zh-CN",
    "ja": "ja",
    "ko": "ko",
    "id": "id",
    "ms": "ms",
    "sw": "sw",
    "bn": "bn",
}

_MAX_CACHE = 4000


class TranslationService:
    """Free translation with provider fallback, caching and safe failure."""

    def __init__(self) -> None:
        self._cache: OrderedDict[tuple[str, str, str], str] = OrderedDict()
        self._lock = threading.RLock()
        self._last_error = ""

    def _cache_get(self, key: tuple[str, str, str]) -> str | None:
        with self._lock:
            value = self._cache.get(key)
            if value is not None:
                self._cache.move_to_end(key)
            return value

    def _cache_put(self, key: tuple[str, str, str], value: str) -> None:
        if not value:
            return
        with self._lock:
            self._cache[key] = value
            self._cache.move_to_end(key)
            while len(self._cache) > _MAX_CACHE:
                self._cache.popitem(last=False)

    @staticmethod
    def _chunks(text: str, limit: int = 450) -> list[str]:
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) <= limit:
            return [text] if text else []
        sentences = re.split(r"(?<=[.!?؟。])\s+", text)
        chunks: list[str] = []
        current = ""
        for sentence in sentences:
            candidate = f"{current} {sentence}".strip()
            if len(candidate) <= limit:
                current = candidate
                continue
            if current:
                chunks.append(current)
            while len(sentence) > limit:
                cut = sentence.rfind(" ", 0, limit)
                cut = cut if cut > 40 else limit
                chunks.append(sentence[:cut].strip())
                sentence = sentence[cut:].strip()
            current = sentence
        if current:
            chunks.append(current)
        return chunks

    def _libretranslate(self, text: str, source: str, target: str) -> str:
        response = requests.post(
            f"{LIBRETRANSLATE_URL.rstrip('/')}/translate",
            json={"q": text, "source": source, "target": target, "format": "text"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        return str(data.get("translatedText", "")).strip()

    def _mymemory(self, text: str, source: str, target: str) -> str:
        src = _MYMEMORY_LANG.get(source, source)
        dst = _MYMEMORY_LANG.get(target, target)
        response = requests.get(
            "https://api.mymemory.translated.net/get",
            params={"q": text, "langpair": f"{src}|{dst}"},
            timeout=10,
            headers={"User-Agent": "SentinelAICamera/1.0"},
        )
        response.raise_for_status()
        data = response.json()
        translated = str((data.get("responseData") or {}).get("translatedText", "")).strip()
        if not translated or "MYMEMORY WARNING" in translated.upper():
            raise RuntimeError("MyMemory returned no translation")
        return translated

    def _openai(self, text: str, source: str, target: str) -> str:
        if not OPENAI_API_KEY:
            raise RuntimeError("OpenAI not configured")
        from openai import OpenAI

        client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
        names = {"en": "English", "ar": "Arabic", "fr": "French", "es": "Spanish", "de": "German"}
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            temperature=0.0,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional translator. Translate the user text faithfully. "
                        "Return only the translation, with no explanation or quotes."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Translate from {names.get(source, source)} to {names.get(target, target)}:\n\n{text}"
                    ),
                },
            ],
            timeout=25,
        )
        return (response.choices[0].message.content or "").strip()

    def translate(self, text: str, target: str = "ar", source: str = "en") -> str:
        text = (text or "").strip()
        target = (target or "").strip().lower()[:8]
        source = (source or "auto").strip().lower()[:8]
        if not text or not target or source == target:
            return text
        if source == "auto":
            source = "en"
        key = (text, source, target)
        cached = self._cache_get(key)
        if cached is not None:
            return cached

        providers = []
        if LIBRETRANSLATE_URL:
            providers.append(self._libretranslate)
        providers.append(self._mymemory)
        if OPENAI_API_KEY:
            providers.append(self._openai)

        parts_result: list[str] = []
        for chunk in self._chunks(text):
            translated = ""
            for provider in providers:
                try:
                    translated = provider(chunk, source, target)
                    if translated:
                        break
                except Exception as exc:  # noqa: BLE001
                    self._last_error = f"{provider.__name__}: {exc}"
                    log.debug("Translation provider failed: %s", self._last_error)
            parts_result.append(translated or chunk)
        result = " ".join(parts_result).strip()
        self._cache_put(key, result)
        return result

    def translate_many(self, text: str, targets: Iterable[str], source: str = "en") -> dict[str, str]:
        result: dict[str, str] = {}
        for target in targets:
            target = (target or "").strip().lower()
            if not target:
                continue
            result[target] = self.translate(text, target=target, source=source)
        return result

    @property
    def last_error(self) -> str:
        return self._last_error
