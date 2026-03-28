"""
tts_engine.py — Multi-engine TTS with SSML generation and native prosody control.

Supports three synthesis backends in priority order:
    1. edge-tts    — Microsoft Neural voices with native rate/pitch/volume control
    2. Coqui TTS   — Offline Tacotron2-DDC with pydub post-processing
    3. gTTS         — Google TTS fallback with pydub post-processing

Includes SSML markup generation for demonstrating Speech Synthesis Markup Language
integration (<prosody>, <break>, <emphasis> tags).

References:
    - Ref 33 (Azure SSML): <prosody> tag specification
    - Ref 35 (AWS Polly): Rate, pitch, volume control via SSML
    - Ref 36 (Google Cloud): SSML prosody implementation
"""
import os
import io
import re
import sys
import math
import asyncio
import tempfile
from pydub import AudioSegment

# ---------------------------------------------------------------------------
#  Windows event loop compatibility
# ---------------------------------------------------------------------------
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# ---------------------------------------------------------------------------
#  edge-tts (Primary — SSML-capable Neural Voices)
# ---------------------------------------------------------------------------
try:
    import edge_tts
    _edge_available = True
    print("edge-tts available (Microsoft Neural voices).")
except ImportError:
    print("WARNING: edge-tts not installed. Run: pip install edge-tts")
    _edge_available = False

EDGE_VOICE = "en-US-AriaNeural"

# ---------------------------------------------------------------------------
#  Coqui TTS (Offline Fallback)
# ---------------------------------------------------------------------------
try:
    from TTS.api import TTS as CoquiTTS
    print("Loading Coqui TTS model...")
    _tts_model = CoquiTTS(
        model_name="tts_models/en/ljspeech/tacotron2-DDC",
        progress_bar=False,
        gpu=False
    )
except ImportError:
    print("WARNING: Coqui TTS not installed. Falling back to gTTS.")
    _tts_model = None

# ---------------------------------------------------------------------------
#  gTTS (Last Resort Fallback)
# ---------------------------------------------------------------------------
from gtts import gTTS


# ===================================================================
#  SSML Generation (Bonus Objective: SSML Integration)
# ===================================================================
def generate_ssml(text: str, profile: dict) -> str:
    """
    Generate SSML markup from text and voice profile.

    Demonstrates SSML integration with:
        - <prosody rate="..." pitch="..." volume="..."> for vocal modulation
        - <break time="...ms"/> for strategic inter-sentence pauses
        - Proper SSML document structure (W3C Speech Synthesis 1.1, Ref 34)

    This markup shows the exact SSML that would be consumed by SSML-capable
    engines like Google Cloud TTS (Ref 36), Azure Speech (Ref 33), or
    Amazon Polly (Ref 35).
    """
    # Pattern splits at . ! ? followed by space, but ignores common titles using negative lookbehind
    pattern = r'(?<=(?<!\bMr)(?<!\bMrs)(?<!\bMs)(?<!\bDr)(?<!\bProf)(?<!\bSr)(?<!\bJr)[.!?])\s+'
    sentences = re.split(pattern, text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]
    if not sentences:
        sentences = [text]

    rate = profile.get('ssml_rate', '+0%')
    pitch = profile.get('ssml_pitch', '+0%')
    volume = profile.get('ssml_volume', '+0dB')
    pause_ms = profile.get('pause_ms', 300)

    ssml_body = []
    for i, sentence in enumerate(sentences):
        ssml_body.append(
            f'        <prosody rate="{rate}" pitch="{pitch}" volume="{volume}">'
            f'{sentence}</prosody>'
        )
        if i < len(sentences) - 1:
            ssml_body.append(f'        <break time="{pause_ms}ms"/>')

    body = '\n'.join(ssml_body)
    ssml = (
        '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
        'xml:lang="en-US">\n'
        f'    <voice name="{EDGE_VOICE}">\n'
        f'{body}\n'
        '    </voice>\n'
        '</speak>'
    )
    return ssml


# ===================================================================
#  edge-tts Synthesis (Primary)
# ===================================================================
async def _edge_synth(text: str, output_path: str,
                      rate: str, pitch: str, volume: str):
    """Async edge-tts synthesis for a single text segment."""
    communicate = edge_tts.Communicate(
        text=text,
        voice=EDGE_VOICE,
        rate=rate,
        pitch=pitch,
        volume=volume,
    )
    await communicate.save(output_path)


async def _edge_synth_batch(sentences: list, tmp_paths: list,
                            rate: str, pitch: str, volume: str):
    """Synthesize multiple sentences in series (one edge-tts call each)."""
    for text, path in zip(sentences, tmp_paths):
        communicate = edge_tts.Communicate(
            text=text,
            voice=EDGE_VOICE,
            rate=rate,
            pitch=pitch,
            volume=volume,
        )
        await communicate.save(path)


def synthesize_edge_tts(text: str, profile: dict, output_path: str) -> AudioSegment:
    """
    Synthesize speech using edge-tts with native prosody control.

    Unlike Coqui/gTTS, edge-tts handles rate, pitch, and volume INDEPENDENTLY
    through the Microsoft Neural voice engine — no pydub post-processing needed.

    For multi-sentence text, each sentence is synthesized separately and joined
    with emotion-appropriate silence gaps for natural delivery.
    """
    if not _edge_available:
        raise RuntimeError("edge-tts is not installed.")

    rate = profile.get('ssml_rate', '+0%')
    # Convert semitones to Hz offset (~15Hz per semitone for typical speech)
    pitch_st = profile.get('pitch_shift', 0)
    pitch_hz = f"{int(pitch_st * 15):+d}Hz"
    # Convert dB to percentage (~16% perceptual change per dB)
    vol_db = profile.get('volume_db', 0)
    volume_pct = f"{int(vol_db * 16):+d}%"

    pause_ms = profile.get('pause_ms', 300)

    # Split into sentences for pause injection (ignoring titles)
    pattern = r'(?<=(?<!\bMr)(?<!\bMrs)(?<!\bMs)(?<!\bDr)(?<!\bProf)(?<!\bSr)(?<!\bJr)[.!?])\s+'
    sentences = re.split(pattern, text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]
    if not sentences:
        sentences = [text]

    if len(sentences) == 1:
        # Single sentence — direct synthesis
        tmp_path = output_path + '.tmp.mp3'
        asyncio.run(_edge_synth(sentences[0], tmp_path, rate, pitch_hz, volume_pct))
        audio = AudioSegment.from_file(tmp_path)
        os.unlink(tmp_path)
        return audio

    # Multi-sentence: synthesize each, join with pauses
    tmp_paths = [output_path + f'.tmp_{i}.mp3' for i in range(len(sentences))]
    asyncio.run(_edge_synth_batch(sentences, tmp_paths, rate, pitch_hz, volume_pct))

    silence = AudioSegment.silent(duration=pause_ms)
    result = AudioSegment.from_file(tmp_paths[0])
    for tmp_path in tmp_paths[1:]:
        result += silence + AudioSegment.from_file(tmp_path)

    # Cleanup temp files
    for tmp_path in tmp_paths:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    return result


# ===================================================================
#  Coqui TTS Synthesis (Offline Fallback #1)
# ===================================================================
def synthesize_coqui(text: str, profile: dict, output_path: str) -> AudioSegment:
    """Synthesize using Coqui TTS (offline, Tacotron2-DDC on LJSpeech)."""
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


# ===================================================================
#  gTTS Synthesis (Last Resort Fallback #2)
# ===================================================================
def synthesize_gtts_fallback(text: str, profile: dict) -> AudioSegment:
    """Synthesize using Google TTS (online, no API key required)."""
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


# ===================================================================
#  Post-Processing (for Coqui/gTTS fallback only)
# ===================================================================
def apply_vocal_effects(audio: AudioSegment, profile: dict) -> AudioSegment:
    """
    Apply pitch shift and volume via pydub.
    Only used for Coqui/gTTS fallback — edge-tts handles this natively.
    """
    processed = audio
    semitones = profile.get('pitch_shift', 0)
    if semitones != 0:
        freq_ratio = math.pow(2, semitones / 12.0)
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
    """Save AudioSegment to file, auto-detecting format from extension."""
    fmt = output_path.split('.')[-1]
    audio.export(output_path, format=fmt)
    return output_path
