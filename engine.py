"""
engine.py — The Empathy Engine core pipeline.
"""
import os
from emotion_detector import detect_emotion
from voice_mapper import get_scaled_profile
from tts_engine import synthesize_coqui, apply_vocal_effects, save_audio, _tts_model

# Use Coqui if it's installed, otherwise fallback
USE_COQUI = _tts_model is not None

def process(text: str, output_path: str = "static/output.wav") -> dict:
    if not text or not text.strip():
        raise ValueError("Input text cannot be empty.")

    # Step 1: Detect emotion + intensity
    emotion, intensity = detect_emotion(text, use_hf=True)
    print(f"[Engine] Detected: {emotion} (intensity={intensity:.2f})")

    # Step 2: Get scaled voice profile
    profile = get_scaled_profile(emotion, intensity)
    print(f"[Engine] Profile: rate={profile['rate']} "
          f"pitch={profile['pitch_shift']:+.2f} "
          f"vol={profile['volume_db']:+.2f}dB")

    # Step 3: Synthesize speech
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if USE_COQUI:
        try:
            audio = synthesize_coqui(text, profile, output_path)
        except Exception as e:
            print(f"[Engine] Coqui failed ({e}), falling back to gTTS")
            from tts_engine import synthesize_gtts_fallback
            audio = synthesize_gtts_fallback(text, profile)
    else:
        from tts_engine import synthesize_gtts_fallback
        audio = synthesize_gtts_fallback(text, profile)

    # Step 4: Apply pitch shift + volume
    audio = apply_vocal_effects(audio, profile)

    # Step 5: Save to file
    save_audio(audio, output_path)
    print(f"[Engine] Saved to: {output_path}")

    return {
        'text':       text,
        'emotion':    emotion,
        'intensity':  round(intensity, 3),
        'profile':    profile,
        'audio_path': output_path,
    }

if __name__ == '__main__':
    examples = [
        "This is absolutely incredible! I can't believe how well this worked!",
        "I am deeply disappointed and frustrated with this outcome.",
        "The quarterly report has been submitted to the finance team.",
        "I'm so scared, I don't know what's going to happen next.",
    ]
    for sentence in examples:
        print(f"\nInput: {sentence}")
        # To avoid NameError on 'result' which is a typo in the guide:
        # result = process(sentence, output_path=f"static/test_{result['emotion']}.wav" if False else "static/output.wav")
        # I fixed the typo logic:
        res = process(sentence, output_path="static/output.wav")
        print(f"Result: emotion={res['emotion']}, intensity={res['intensity']}, profile={res['profile']}")
