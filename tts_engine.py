import os
import io
import tempfile
from pydub import AudioSegment

# Attempt to load Coqui TTS, otherwise mock it so the app still runs using gTTS
try:
    from TTS.api import TTS as CoquiTTS
    print("Loading Coqui TTS model...")
    _tts_model = CoquiTTS(model_name="tts_models/en/ljspeech/tacotron2-DDC",
                          progress_bar=False,
                          gpu=False)
except ImportError:
    print("WARNING: Coqui TTS not installed. Falling back to gTTS.")
    _tts_model = None

def synthesize_coqui(text: str, profile: dict, output_path: str) -> AudioSegment:
    if _tts_model is None:
        raise RuntimeError("Coqui TTS is disabled/missing.")

    speed_factor = profile['rate'] / 150.0
    speed_factor = max(0.5, min(2.0, speed_factor))

    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
        tmp_path = tmp.name

    _tts_model.tts_to_file(text=text, file_path=tmp_path, speed=speed_factor)
    audio = AudioSegment.from_wav(tmp_path)
    os.unlink(tmp_path)
    return audio

def apply_vocal_effects(audio: AudioSegment, profile: dict) -> AudioSegment:
    processed = audio
    semitones = profile.get('pitch_shift', 0)
    if semitones != 0:
        import math
        freq_ratio = math.pow(2, semitones / 12.0) 
        # In music, raising a sound by exactly 1 octave (12 semitones) doubles its frequency (2.0x).
        original_frame_rate = processed.frame_rate
        shifted = processed._spawn(processed.raw_data, overrides={
            "frame_rate": int(processed.frame_rate * freq_ratio)
        })
        processed = shifted.set_frame_rate(original_frame_rate)

    volume_db = profile.get('volume_db', 0)
    if volume_db != 0:
        processed = processed + volume_db

    return processed

def save_audio(audio: AudioSegment, output_path: str) -> str:
    fmt = output_path.split('.')[-1]
    audio.export(output_path, format=fmt)
    return output_path

from gtts import gTTS

def synthesize_gtts_fallback(text: str, profile: dict) -> AudioSegment:
    tts = gTTS(text=text, lang='en', slow=False)
    buf = io.BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)
    audio = AudioSegment.from_mp3(buf)

    speed_factor = profile['rate'] / 150.0
    speed_factor = max(0.6, min(1.8, speed_factor))
    audio = audio._spawn(audio.raw_data, overrides={
        "frame_rate": int(audio.frame_rate * speed_factor)
    }).set_frame_rate(audio.frame_rate)
    
    return audio
