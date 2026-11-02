from __future__ import annotations

import io
import logging
import queue
import re
import threading
import time
import uuid
import wave
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np

from ai.agent import SecurityAgent
from ai.translate import TranslationService
from config import AUDIO_DIR, WHISPER_MODEL
from core import database as db
from core.events import EventManager
from core.storage import relative_path
from services.camera_service import CameraService

log = logging.getLogger(__name__)

QUESTION_RE = re.compile(
    r"(^\s*(what|who|where|when|why|how|which|can|could|would|will|is|are|am|do|does|did|"
    r"tell me|explain|show me|ماذا|ما |من |أين|متى|لماذا|كيف|هل|أخبرني))|[\?؟]",
    re.IGNORECASE,
)


class AudioService:
    def __init__(
        self,
        events: EventManager,
        translator: TranslationService,
        agent: SecurityAgent,
        camera: CameraService,
    ) -> None:
        self.events = events
        self.translator = translator
        self.agent = agent
        self.camera = camera
        self._running = False
        self._thread: threading.Thread | None = None
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="speech")
        self._whisper = None
        self._whisper_lock = threading.RLock()
        self._whisper_error = ""
        self._mic_error = ""
        self._samplerate = 16_000
        self._stream = None
        self._pending = 0
        self._lock = threading.RLock()
        self._speaking = False
        self._last_text = ""
        self._last_language = ""
        self._utterances = 0
        self._input_devices = 0
        self._last_event_time = 0.0

    # ------------------------------------------------------------------ thread

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, name="audio-monitor", daemon=True)
        self._thread.start()
        log.info("Audio monitoring service started")

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=4)
        self._close_stream()
        self._executor.shutdown(wait=False, cancel_futures=True)
        log.info("Audio monitoring service stopped")

    def _open_stream(self) -> bool:
        try:
            import sounddevice as sd
        except Exception as exc:  # noqa: BLE001
            self._mic_error = f"sounddevice is not available: {exc}"
            return False
        try:
            devices = sd.query_devices()
            self._input_devices = sum(1 for d in devices if int(d.get("max_input_channels", 0)) > 0)
        except Exception:  # noqa: BLE001
            self._input_devices = 0
        last_error = ""
        for samplerate in (16_000, 48_000, 44_100, 32_000):
            try:
                stream = sd.InputStream(
                    samplerate=samplerate,
                    channels=1,
                    dtype="int16",
                    blocksize=max(256, int(samplerate * 0.03)),
                    latency="low",
                )
                stream.start()
                self._stream = stream
                self._samplerate = samplerate
                self._mic_error = ""
                log.info("Microphone opened at %d Hz", samplerate)
                return True
            except Exception as exc:  # noqa: BLE001
                last_error = str(exc)
                try:
                    if "stream" in locals() and stream is not None:
                        stream.close()
                except Exception:  # noqa: BLE001
                    pass
        self._mic_error = f"No microphone could be opened: {last_error}"
        log.warning(self._mic_error)
        time.sleep(2.0)
        return False

    def _close_stream(self) -> None:
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:  # noqa: BLE001
                pass
            self._stream = None

    def _loop(self) -> None:
        try:
            import sounddevice as sd  # noqa: F401
        except Exception as exc:  # noqa: BLE001
            self._mic_error = f"sounddevice import failed: {exc}"
            log.warning(self._mic_error)
            return
        blocksize_seconds = 0.03
        preroll_max = 12
        preroll = []
        recording: list[np.ndarray] = []
        voiced_blocks = 0
        active = False
        silent_since = 0.0
        started = 0.0
        while self._running:
            try:
                if not db.get_bool_setting("audio_monitor", True):
                    with self._lock:
                        self._speaking = False
                    recording = []
                    active = False
                    time.sleep(0.4)
                    continue
                if self._stream is None:
                    if not self._open_stream():
                        continue
                    blocksize_seconds = max(0.02, min(0.05, float(self._stream.blocksize) / self._samplerate))
                    preroll_max = max(5, int(0.35 / blocksize_seconds))
                data, _overflowed = self._stream.read(int(self._stream.blocksize))
                samples = np.asarray(data, dtype=np.int16).reshape(-1)
                if samples.size == 0:
                    continue
                rms = float(np.sqrt(np.mean(samples.astype(np.float32) ** 2)))
                threshold = max(80, db.get_int_setting("audio_threshold", 450))
                now = time.time()
                if not active:
                    preroll.append(samples.copy())
                    if len(preroll) > preroll_max:
                        preroll.pop(0)
                    if rms >= threshold:
                        active = True
                        started = now
                        silent_since = now
                        recording = list(preroll)
                        voiced_blocks = 1
                        with self._lock:
                            self._speaking = True
                else:
                    recording.append(samples.copy())
                    if rms >= threshold * 0.75:
                        voiced_blocks += 1
                        silent_since = now
                    duration = now - started
                    silence = now - silent_since
                    if (silence >= 0.85 and duration >= 0.7) or duration >= 20.0:
                        active = False
                        with self._lock:
                            self._speaking = False
                        if duration >= 0.7 and voiced_blocks >= 4 and len(recording) >= 4:
                            audio = np.concatenate(recording)
                            self._submit_utterance(audio, self._samplerate)
                        recording = []
                        voiced_blocks = 0
                        preroll = []
            except Exception as exc:  # noqa: BLE001
                self._mic_error = f"Microphone read failed: {exc}"
                log.warning(self._mic_error)
                self._close_stream()
                with self._lock:
                    self._speaking = False
                time.sleep(2.0)

    # --------------------------------------------------------------- processing

    @staticmethod
    def _wav_bytes(samples: np.ndarray, samplerate: int) -> bytes:
        samples = np.asarray(samples, dtype=np.int16)
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as handle:
            handle.setnchannels(1)
            handle.setsampwidth(2)
            handle.setframerate(samplerate)
            handle.writeframes(samples.tobytes())
        return buffer.getvalue()

    @staticmethod
    def _resample(samples: np.ndarray, source_rate: int, target_rate: int = 16_000) -> np.ndarray:
        if source_rate == target_rate:
            return samples
        try:
            from scipy.signal import resample_poly

            gcd = np.gcd(source_rate, target_rate)
            return resample_poly(samples.astype(np.float32), target_rate // gcd, source_rate // gcd).astype(np.int16)
        except Exception:  # noqa: BLE001
            return samples

    def _submit_utterance(self, samples: np.ndarray, samplerate: int) -> None:
        samples = self._resample(samples, samplerate, 16_000)
        wav = self._wav_bytes(samples, 16_000)
        AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"speech_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}.wav"
        path = AUDIO_DIR / filename
        path.write_bytes(wav)
        rel = relative_path(path)
        with self._lock:
            self._pending += 1
        try:
            self._executor.submit(self._process_utterance, str(path), rel, wav)
        except RuntimeError:
            with self._lock:
                self._pending = max(0, self._pending - 1)

    def _get_whisper(self):
        if self._whisper is not None:
            return self._whisper
        with self._whisper_lock:
            if self._whisper is not None:
                return self._whisper
            try:
                import os

                os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
                from faster_whisper import WhisperModel

                self._whisper = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
                db.set_setting("whisper_model", WHISPER_MODEL)
                log.info("Whisper model loaded: %s", WHISPER_MODEL)
            except Exception as exc:  # noqa: BLE001
                self._whisper_error = str(exc)
                log.warning("Whisper could not be loaded: %s", exc)
                return None
        return self._whisper

    def _transcribe(self, path: str) -> dict[str, Any]:
        result = {
            "text": "",
            "language": "",
            "english": "",
            "arabic": "",
            "backend": "unavailable",
            "error": "",
        }
        if not db.get_bool_setting("transcribe_audio", True):
            result["error"] = "Transcription is disabled in settings."
            return result
        model = self._get_whisper()
        if model is None:
            result["error"] = self._whisper_error or "Whisper model unavailable."
            return result
        try:
            segments, info = model.transcribe(
                path,
                vad_filter=True,
                beam_size=1,
                condition_on_previous_text=False,
                word_timestamps=False,
            )
            text = " ".join(segment.text.strip() for segment in segments).strip()
            language = (info.language or "").lower()
            result.update({"text": text, "language": language, "backend": f"faster-whisper:{WHISPER_MODEL}"})
            english = text if language.startswith("en") else ""
            if text and not language.startswith("en"):
                try:
                    segs, _ = model.transcribe(
                        path, task="translate", vad_filter=True, beam_size=1, condition_on_previous_text=False
                    )
                    english = " ".join(segment.text.strip() for segment in segs).strip()
                except Exception as exc:  # noqa: BLE001
                    log.debug("Whisper translation failed: %s", exc)
            result["english"] = english
            english_for_translation = english or text
            arabic = ""
            if language.startswith("ar"):
                arabic = text
            elif english_for_translation and db.get_bool_setting("translate_events", True):
                arabic = self.translator.translate(english_for_translation, target="ar", source="en")
            result["arabic"] = arabic
            return result
        except Exception as exc:  # noqa: BLE001
            result["error"] = str(exc)
            log.warning("Transcription failed: %s", exc)
            return result

    def _process_utterance(self, path: str, audio_rel: str, wav_bytes: bytes) -> None:
        try:
            transcription = self._transcribe(path)
            text = transcription["text"]
            language = transcription["language"]
            english = transcription["english"]
            arabic = transcription["arabic"]
            with self._lock:
                self._last_text = text
                self._last_language = language
                self._utterances += 1
            question = bool(text and QUESTION_RE.search(text))
            answer_data = None
            person = self.camera.current_known_person()
            snapshot_path, _ = self.camera.snapshot_for_event("speech")
            if question and db.get_bool_setting("auto_answer_questions", True):
                answer_data = self.agent.ask(english or text, language="en", use_llm=True)
            if not text:
                title = "Speech captured"
                description = (
                    "Audio was captured but speech could not be transcribed. "
                    + (transcription.get("error") or "Try a quieter environment or a larger Whisper model.")
                )
                description_ar = "تم التقاط الصوت ولكن تعذر نسخ الكلام."
                translations = ""
            elif question and answer_data:
                title = "Question asked and answered by AI"
                answer = answer_data.get("answer", "")
                description = f"Question: {text}\n\nAI answer: {answer}"
                description_ar = f"السؤال: {arabic or text}\n\nإجابة الذكاء الاصطناعي: {answer_data.get('answer', '')}"
                translations = english if english and english != text else ""
            else:
                title = f"Speech captured{f' ({language})' if language else ''}"
                description = text
                description_ar = arabic or "تم التقاط كلام."
                translations = english if english and english != text else (arabic if arabic and arabic != text else "")
            meta: dict[str, Any] = {
                "language": language,
                "backend": transcription.get("backend", ""),
                "audio": audio_rel,
                "translations": {
                    "original": text,
                    "english": english,
                    "arabic": arabic,
                },
                "question": question,
            }
            if transcription.get("error"):
                meta["transcription_error"] = transcription["error"]
            if answer_data:
                meta["answer"] = answer_data.get("answer", "")
                meta["answer_sources"] = answer_data.get("sources", [])
                meta["answer_provider"] = answer_data.get("provider", "")
                meta["speak_text"] = answer_data.get("answer", "")[:900]
                meta["speak_language"] = "en"
            elif question:
                meta["question_unanswered"] = True
            event = self.events.log(
                "question" if question and answer_data else "speech",
                "info",
                title,
                description,
                description_ar=description_ar,
                person=person,
                snapshot_path=snapshot_path,
                audio_path=audio_rel,
                transcript=text,
                translation=translations,
                meta=meta,
                translate=False,
            )
            if event:
                self._last_event_time = time.time()
        except Exception:  # noqa: BLE001
            log.exception("Speech processing failed")
        finally:
            with self._lock:
                self._pending = max(0, self._pending - 1)
            try:
                Path(path).unlink(missing_ok=True)
            except OSError:
                pass

    # --------------------------------------------------------------- upload/API

    def process_uploaded_audio(self, data: bytes, filename: str) -> dict:
        suffix = Path(filename or "upload.wav").suffix.lower()
        if suffix not in {".wav", ".mp3", ".m4a", ".ogg", ".webm", ".flac"}:
            suffix = ".wav"
        AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        path = AUDIO_DIR / f"upload_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}{suffix}"
        path.write_bytes(data)
        transcription = self._transcribe(str(path))
        wav_for_web = data
        if suffix != ".wav":
            try:
                from faster_whisper.audio import decode_audio
                import soundfile as sf

                decoded = decode_audio(str(path), sampling_rate=16_000)
                wav_for_web = self._wav_bytes((decoded * 32767).astype(np.int16), 16_000)
                suffix = ".wav"
                path.unlink(missing_ok=True)
                path = path.with_suffix(".wav")
                path.write_bytes(wav_for_web)
            except Exception:  # noqa: BLE001
                pass
        rel = relative_path(path)
        english = transcription.get("english") or transcription.get("text", "")
        arabic = transcription.get("arabic", "")
        snapshot_path, _ = self.camera.snapshot_for_event("speech_upload")
        event = self.events.log(
            "speech",
            "info",
            "Uploaded audio transcribed",
            transcription.get("text") or "The uploaded audio could not be transcribed.",
            description_ar=arabic or "تم نسخ الملف الصوتي المرفوع.",
            snapshot_path=snapshot_path,
            audio_path=rel,
            transcript=transcription.get("text", ""),
            translation=english if english and english != transcription.get("text") else arabic,
            meta={
                "language": transcription.get("language", ""),
                "backend": transcription.get("backend", ""),
                "transcription_error": transcription.get("error", ""),
                "translations": {"english": english, "arabic": arabic},
                "uploaded": True,
            },
            translate=False,
        )
        return {
            "event": event,
            "transcript": transcription.get("text", ""),
            "language": transcription.get("language", ""),
            "translation_en": english,
            "translation_ar": arabic,
            "error": transcription.get("error", ""),
        }

    def get_status(self) -> dict:
        with self._lock:
            return {
                "mic_available": self._stream is not None,
                "mic_error": self._mic_error,
                "input_devices": self._input_devices,
                "monitoring": db.get_bool_setting("audio_monitor", True),
                "speaking": self._speaking,
                "pending": self._pending,
                "utterances": self._utterances,
                "last_text": self._last_text,
                "last_language": self._last_language,
                "whisper_model": WHISPER_MODEL,
                "whisper_error": self._whisper_error,
                "samplerate": self._samplerate,
            }
