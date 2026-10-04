import argparse
from pathlib import Path

import yt_dlp
from pydub import AudioSegment


PROJECT_DIR = Path(__file__).resolve().parents[2]
DOWNLOAD_DIR = PROJECT_DIR / "downloades"


def download_youtube_audio(url: str, download_dir: str | Path = DOWNLOAD_DIR) -> str:
    """Download a YouTube video's audio and return the generated WAV path."""
    if not url or not url.strip():
        raise ValueError("A YouTube URL is required.")

    download_dir = Path(download_dir)
    download_dir.mkdir(parents=True, exist_ok=True)
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(download_dir / "%(title)s.%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
        "quiet": True,
        "noplaylist": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        wav_path = Path(ydl.prepare_filename(info)).with_suffix(".wav")

    if not wav_path.is_file():
        raise FileNotFoundError(f"yt-dlp did not create the expected file: {wav_path}")
    return str(wav_path)


def convert_to_wav(input_path: str | Path) -> str:
    """Convert an audio/video file to mono, 16 kHz WAV format."""
    input_path = Path(input_path)
    if not input_path.is_file():
        raise FileNotFoundError(f"Input file does not exist: {input_path}")

    output_path = input_path.with_name(f"{input_path.stem}_converted.wav")
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(16000)
    audio.export(output_path, format="wav")
    return str(output_path)


def chunk_audio(wav_path: str | Path, chunk_minutes: int = 10) -> list[str]:
    """Split a WAV file into chunks and return the generated paths."""
    wav_path = Path(wav_path)
    if not wav_path.is_file():
        raise FileNotFoundError(f"WAV file does not exist: {wav_path}")
    if chunk_minutes <= 0:
        raise ValueError("chunk_minutes must be greater than zero.")

    audio = AudioSegment.from_wav(wav_path)
    chunk_ms = chunk_minutes * 60 * 1000
    chunks = []

    for index, start in enumerate(range(0, len(audio), chunk_ms)):
        chunk_path = wav_path.with_name(f"{wav_path.stem}_chunk_{index}.wav")
        audio[start : start + chunk_ms].export(chunk_path, format="wav")
        chunks.append(str(chunk_path))

    return chunks


def process_youtube_audio(url: str, chunk_minutes: int = 10) -> list[str]:
    """Download, normalize, and chunk a YouTube video's audio."""
    downloaded_path = download_youtube_audio(url)
    wav_path = convert_to_wav(downloaded_path)
    return chunk_audio(wav_path, chunk_minutes)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download and chunk YouTube audio.")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("--chunk-minutes", type=int, default=10)
    args = parser.parse_args()

    for chunk_path in process_youtube_audio(args.url, args.chunk_minutes):
        print(chunk_path)


if __name__ == "__main__":
    main()


def process_input(source: str) -> list:
    if source.startswith("http://") or source.startswith("https://"):
        print("Detected YouTube URL. Downloading audio...")
        wav_path = download_youtube_audio(source)
    else:
        print("Detected local file. Converting to WAV...")
        wav_path = convert_to_wav(source)

    print("Chunking audio...")
    chunks = chunk_audio(wav_path)
    print(f"Audio ready — {len(chunks)} chunk(s) created.")
    return chunks