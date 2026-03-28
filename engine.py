"""
engine.py — The Empathy Engine core pipeline.

Orchestrates the 5-stage speech synthesis pipeline:
    1. Text preprocessing (emoji extraction, typographic analysis)
    2. Emotion detection (dual HF + VADER blending)
    3. Voice parameter mapping (PAD-inspired, SSML-ready)
    4. SSML generation (bonus objective)
    5. Audio synthesis (edge-tts → Coqui → gTTS fallback chain)
"""
import os
from pydub import AudioSegment
from emotion_detector import detect_emotion
from voice_mapper import get_scaled_profile
from tts_engine import (
    generate_ssml, synthesize_edge_tts,
    synthesize_coqui, apply_vocal_effects, save_audio,
    _tts_model, _edge_available
)

# Use Coqui if it's installed, otherwise fallback
USE_COQUI = _tts_model is not None


def process(text: str, output_path: str = "static/output.wav") -> dict:
    """
    Main processing pipeline.

    Args:
        text: Input text to synthesize.
        output_path: Path for the output .wav file.

    Returns:
        dict with keys: text, emotion, intensity, profile, ssml, audio_path
    """
    if not text or not text.strip():
        raise ValueError("Input text cannot be empty.")

    # Step 1: Detect emotion + intensity
    #   (includes emoji parsing, typographic boost, dual VADER+HF blending)
    emotion, intensity = detect_emotion(text, use_hf=True)
    print(f"[Engine] Detected: {emotion} (intensity={intensity:.4f})")

    # Step 2: Get scaled voice profile
    #   (includes PAD coordinates, SSML strings, pause duration)
    profile = get_scaled_profile(emotion, intensity)
    print(f"[Engine] Profile: rate={profile['rate']} "
          f"pitch={profile['pitch_shift']:+.2f}st "
          f"vol={profile['volume_db']:+.2f}dB "
          f"pause={profile['pause_ms']}ms")
    print(f"[Engine] SSML params: rate={profile['ssml_rate']} "
          f"pitch={profile['ssml_pitch']} vol={profile['ssml_volume']}")

    # Step 3: Generate SSML markup (for display and logging)
    ssml = generate_ssml(text, profile)
    print(f"[Engine] Generated SSML:\n{ssml}")

    # Step 4: Synthesize speech
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

    if _edge_available:
        try:
            audio = synthesize_edge_tts(text, profile, output_path)
            print("[Engine] ✓ Synthesized with edge-tts (native prosody control)")
        except Exception as e:
            print(f"[Engine] ✗ edge-tts failed ({e}), trying fallback...")
            audio = _fallback_synthesis(text, profile, output_path)
    else:
        print("[Engine] edge-tts unavailable, using fallback chain")
        audio = _fallback_synthesis(text, profile, output_path)

    # Step 5: Save to file
    save_audio(audio, output_path)
    print(f"[Engine] Saved to: {output_path}")

    return {
        'text':       text,
        'emotion':    emotion,
        'intensity':  round(intensity, 3),
        'profile':    profile,
        'ssml':       ssml,
        'audio_path': output_path,
    }


def _fallback_synthesis(text: str, profile: dict, output_path: str) -> AudioSegment:
    """
    Coqui → gTTS fallback chain with pydub post-processing.
    Only used when edge-tts is unavailable or fails.
    """
    if USE_COQUI:
        try:
            audio = synthesize_coqui(text, profile, output_path)
            print("[Engine] ✓ Synthesized with Coqui TTS (offline)")
        except Exception as e:
            print(f"[Engine] ✗ Coqui failed ({e}), falling back to gTTS")
            from tts_engine import synthesize_gtts_fallback
            audio = synthesize_gtts_fallback(text, profile)
            print("[Engine] ✓ Synthesized with gTTS (Google TTS)")
    else:
        from tts_engine import synthesize_gtts_fallback
        audio = synthesize_gtts_fallback(text, profile)
        print("[Engine] ✓ Synthesized with gTTS (Google TTS)")

    # Apply pydub effects (pitch shift + volume) — needed for Coqui/gTTS
    audio = apply_vocal_effects(audio, profile)
    return audio


if __name__ == '__main__':
    examples = [
        "This is absolutely incredible! I can't believe how well this worked!",
        "I am deeply disappointed and frustrated with this outcome.",
        "The quarterly report has been submitted to the finance team.",
        "I'm so scared, I don't know what's going to happen next.",
        "THIS IS THE BEST NEWS EVER!!!",
    ]
    for sentence in examples:
        print(f"\n{'='*60}")
        print(f"Input: {sentence}")
        res = process(sentence, output_path="static/output.wav")
        print(f"Result: emotion={res['emotion']}, intensity={res['intensity']}")
