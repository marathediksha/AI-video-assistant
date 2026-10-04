import os
from functools import lru_cache
from pathlib import Path
from typing import Iterable


@lru_cache(maxsize=1)
def _load_model(model_name: str):
	"""Load Whisper only when transcription is requested, and reuse it."""
	import whisper

	return whisper.load_model(model_name)


def _whisper_language(language: str | None) -> str | None:
	if not language:
		return None

	normalized = language.strip().lower()
	if normalized in {"english", "en"}:
		return "en"
	if normalized in {"hindi", "hi"}:
		return "hi"
	if normalized in {"hinglish", "auto", "automatic"}:
		return None
	raise ValueError("language must be 'english', 'hindi', or 'hinglish'.")


def transcribe_all(chunks: Iterable[str | Path], language: str = "english") -> str:
	"""Transcribe audio chunks in order and return one combined transcript."""
	chunk_paths = [Path(chunk) for chunk in chunks]
	if not chunk_paths:
		raise ValueError("At least one audio chunk is required for transcription.")
	missing = [str(path) for path in chunk_paths if not path.is_file()]
	if missing:
		raise FileNotFoundError(f"Audio chunk does not exist: {missing[0]}")

	model_name = os.getenv("WHISPER_MODEL", "base")
	model = _load_model(model_name)
	whisper_language = _whisper_language(language)
	transcript_parts = []

	for chunk_path in chunk_paths:
		options = {"language": whisper_language} if whisper_language else {}
		result = model.transcribe(str(chunk_path), fp16=False, **options)
		text = result.get("text", "").strip()
		if text:
			transcript_parts.append(text)

	return "\n\n".join(transcript_parts)
