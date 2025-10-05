"""
Audio transcription using OpenAI Whisper API.
"""

from pathlib import Path
from typing import Optional
import openai


def transcribe_audio(
    audio_path: str,
    language: Optional[str] = None,
    prompt: Optional[str] = None
    
) -> str:
    path = Path(audio_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    # Whisper API accepts various formats
    supported_formats = {'.m4a', '.mp3', '.wav', '.mp4', '.mpeg', '.mpga', '.webm'}
    if path.suffix.lower() not in supported_formats:
        raise ValueError(f"Unsupported format: {path.suffix}. Supported: {supported_formats}")
    
    print(f"Transcribing audio file: {path.name}")
    print(f"File size: {path.stat().st_size / 1024 / 1024:.2f} MB")
    
    with open(path, 'rb') as audio_file:
        transcript = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language=language,
            prompt=prompt,
            response_format="text"
        )
    
    print(f"Transcription complete: {len(transcript)} characters")
    
    return transcript