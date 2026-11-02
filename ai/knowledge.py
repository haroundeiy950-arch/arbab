from __future__ import annotations

import logging
import re
import threading
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from config import KNOWLEDGE_DIR

log = logging.getLogger(__name__)

_ALLOWED = {".md", ".txt", ".pdf"}


@dataclass
class KnowledgeChunk:
    title: str
    text: str
    source: str


@dataclass
class KnowledgeBase:
    chunks: list[KnowledgeChunk] = field(default_factory=list)
    _vectorizer: TfidfVectorizer | None = None
    _matrix: object | None = None
    _lock: threading.RLock = field(default_factory=threading.RLock)

    def __post_init__(self) -> None:
        self.index()

    @staticmethod
    def _read_file(path: Path) -> str:
        if path.suffix.lower() == ".pdf":
            try:
                from pypdf import PdfReader

                reader = PdfReader(str(path))
                return "\n".join((page.extract_text() or "") for page in reader.pages)
            except Exception as exc:  # noqa: BLE001
                log.warning("Could not read PDF knowledge file %s: %s", path, exc)
                return ""
        return path.read_text(encoding="utf-8", errors="ignore")

    @staticmethod
    def _chunk_text(text: str, size: int = 850, overlap: int = 120) -> list[str]:
        text = re.sub(r"\r\n?", "\n", text).strip()
        text = re.sub(r"\n{3,}", "\n\n", text)
        if not text:
            return []
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        chunks: list[str] = []
        current = ""
        for paragraph in paragraphs:
            if len(paragraph) > size * 1.5:
                sentences = re.split(r"(?<=[.!?؟])\s+", paragraph)
                pieces = sentences
            else:
                pieces = [paragraph]
            for piece in pieces:
                if len(current) + len(piece) + 2 <= size:
                    current = f"{current}\n\n{piece}".strip()
                else:
                    if current:
                        chunks.append(current)
                    tail = current[-overlap:] if current else ""
                    current = f"{tail}\n{piece}".strip()
                    while len(current) > size:
                        chunks.append(current[:size])
                        current = current[size - overlap :]
        if current:
            chunks.append(current)
        return chunks

    def index(self) -> int:
        with self._lock:
            chunks: list[KnowledgeChunk] = []
            for path in sorted(KNOWLEDGE_DIR.iterdir()):
                if not path.is_file() or path.suffix.lower() not in _ALLOWED:
                    continue
                text = self._read_file(path)
                for index, chunk in enumerate(self._chunk_text(text)):
                    chunks.append(
                        KnowledgeChunk(
                            title=f"{path.stem} #{index + 1}",
                            text=chunk,
                            source=path.name,
                        )
                    )
            self.chunks = chunks
            if chunks:
                self._vectorizer = TfidfVectorizer(
                    ngram_range=(1, 2),
                    stop_words="english",
                    max_features=30000,
                    sublinear_tf=True,
                )
                try:
                    self._matrix = self._vectorizer.fit_transform([c.text for c in chunks])
                except ValueError:
                    self._matrix = None
            else:
                self._vectorizer = None
                self._matrix = None
            log.info("Knowledge base indexed: %d chunks", len(chunks))
            return len(chunks)

    def search(self, query: str, k: int = 4) -> list[dict]:
        query = (query or "").strip()
        with self._lock:
            if not query or not self.chunks or self._vectorizer is None or self._matrix is None:
                return []
            try:
                q = self._vectorizer.transform([query])
                scores = cosine_similarity(q, self._matrix).ravel()
            except Exception as exc:  # noqa: BLE001
                log.warning("Knowledge search failed: %s", exc)
                return []
            order = np.argsort(scores)[::-1][:k]
            results = []
            for idx in order:
                score = float(scores[idx])
                if score <= 0.01:
                    continue
                chunk = self.chunks[int(idx)]
                results.append(
                    {
                        "title": chunk.title,
                        "source": chunk.source,
                        "text": chunk.text,
                        "score": round(score, 4),
                    }
                )
            return results

    def answer(self, query: str, k: int = 3) -> dict:
        results = self.search(query, k=k)
        if not results:
            return {
                "answer": (
                    "I could not find that information in the company knowledge base. "
                    "An authorized administrator can add the document to the Knowledge page."
                ),
                "sources": [],
                "provider": "local-rag",
            }
        joined = "\n\n".join(f"[{r['title']}]\n{r['text']}" for r in results)
        intro = "Based on the company knowledge base:\n\n"
        return {
            "answer": intro + joined,
            "sources": [{"title": r["title"], "source": r["source"], "score": r["score"]} for r in results],
            "provider": "local-rag",
        }

    def stats(self) -> dict:
        files = [
            p.name
            for p in KNOWLEDGE_DIR.iterdir()
            if p.is_file() and p.suffix.lower() in _ALLOWED
        ]
        return {"files": sorted(files), "chunks": len(self.chunks), "source": str(KNOWLEDGE_DIR)}

    def save_document(self, filename: str, data: bytes | None = None, text: str | None = None) -> Path:
        KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = re.sub(r"[^A-Za-z0-9._ -]+", "_", Path(filename).name).strip() or "document.md"
        suffix = Path(safe_name).suffix.lower()
        if suffix not in _ALLOWED:
            safe_name += ".md"
        path = KNOWLEDGE_DIR / safe_name
        if data is not None:
            path.write_bytes(data)
        else:
            path.write_text(text or "", encoding="utf-8")
        self.index()
        return path


def seed_knowledge(company_name: str = "Arbab Company") -> None:
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    if any(KNOWLEDGE_DIR.iterdir()):
        return
    content = f"""# {company_name} - Company Knowledge Base

> Replace this demo content with your real company information. The AI assistant answers only from these documents.

## About the company
{company_name} is a technology and security services company. Our main office is open Sunday to Thursday,
08:00-17:00. Visitor reception is on the ground floor.

## Safety and security policy
- All visitors must sign in at reception and wear a visitor badge.
- Weapons, knives, and other prohibited items are not allowed in the building.
- Face recognition and audio monitoring are used only in clearly signed areas and only with legal authorization.
- Security staff must review any AI alert before taking action.

## Meetings
Meeting rooms are available from 09:00 to 16:00. Book a room through reception at least one day in advance.
Emergency exits are located at the east and west ends of each floor.

## Contact
Reception: +000 000 0000
Security desk: extension 110
Email: info@example.com

## Camera system
The AI camera counts people, recognizes registered people who gave consent, interprets basic gestures,
detects visible restricted items, reads license plates for registered vehicles, transcribes speech when audio
monitoring is enabled, and answers questions using this knowledge base. It does not perform body scans or
produce nude images. All alerts require human review.
"""
    (KNOWLEDGE_DIR / "company.md").write_text(content, encoding="utf-8")
    examples = """# Vehicle registry demo

Register vehicles on the Vehicles page. A plate lookup only returns the make, model, and owner that you
have registered in this system. Automatic lookup from an external vehicle registry can be enabled with the
VEHICLE_LOOKUP_URL environment variable.
"""
    (KNOWLEDGE_DIR / "vehicle-registry.md").write_text(examples, encoding="utf-8")
