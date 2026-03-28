"""
voice_mapper.py — PAD-inspired emotion-to-voice parameter mapping.

Maps detected emotions to vocal parameters (rate, pitch, volume) using
research-backed profiles and Pleasure-Arousal-Dominance (PAD) dimensional
coordinates. Includes intensity dampening and SSML-ready output.

References:
    - Ref 18 (Murray & Arnott, 2000): Empirical prosodic parameter values
    - Ref 24 (PAD Framework): Dimensional emotion-to-prosody mapping equations
    - Ref 5  (Yin et al.): Expectation-disconfirmation → intensity dampening
"""

# ---------------------------------------------------------------------------
#  Baseline Neutral Profile
# ---------------------------------------------------------------------------
NEUTRAL = {'rate': 150, 'pitch_shift': 0, 'volume_db': 0}

# ---------------------------------------------------------------------------
#  Research-Backed Voice Profiles (Ref 18: Murray & Arnott, 2000)
#
#  Rate: words per minute (neutral = 150 wpm)
#  Pitch Shift: semitones from baseline (0 = neutral)
#  Volume: dB relative to baseline (0 = neutral)
#
#  Joy:      +30% rate, high pitch, loud          (Ref 18)
#  Sadness:  -10% rate, low flat pitch, soft      (Ref 18)
#  Anger:    +30% rate, high wide pitch, +6dB     (Ref 18)
#  Fear:     +30% rate, very high pitch, normal   (Ref 18)
#  Surprise: +4% rate, steep rising pitch         (Ref 19)
# ---------------------------------------------------------------------------
VOICE_PROFILES = {
    'happy':     {'rate': 195, 'pitch_shift': +3,  'volume_db': +3},
    'excited':   {'rate': 210, 'pitch_shift': +4,  'volume_db': +4},
    'positive':  {'rate': 165, 'pitch_shift': +1,  'volume_db': +1},
    'neutral':   {'rate': 150, 'pitch_shift':  0,  'volume_db':  0},
    'sad':       {'rate': 135, 'pitch_shift': -3,  'volume_db': -3},
    'angry':     {'rate': 195, 'pitch_shift': -1,  'volume_db': +6},
    'fearful':   {'rate': 195, 'pitch_shift': +4,  'volume_db':  0},
    'surprised': {'rate': 156, 'pitch_shift': +5,  'volume_db': +1},
    'disgusted': {'rate': 120, 'pitch_shift': -2,  'volume_db': -1},
}

# ---------------------------------------------------------------------------
#  PAD Coordinates (Ref 24: Russell & Mehrabian dimensional model)
#
#  P = Pleasure   (-1.0 to +1.0)  — positive vs negative valence
#  A = Arousal     (-1.0 to +1.0)  — calm vs excited energy
#  D = Dominance   (-1.0 to +1.0)  — submissive vs authoritative
#
#  Key insight from Ref 24:
#    - Arousal (A) is the PRIMARY driver for rate, pitch, and volume
#    - Dominance (D) has an INVERSE relationship with pitch
#      (authoritative speech → lower register)
# ---------------------------------------------------------------------------
PAD_COORDINATES = {
    'happy':     {'P': +0.7, 'A': +0.5, 'D': +0.4},
    'excited':   {'P': +0.6, 'A': +0.9, 'D': +0.3},
    'positive':  {'P': +0.5, 'A': +0.2, 'D': +0.3},
    'neutral':   {'P':  0.0, 'A':  0.0, 'D':  0.0},
    'sad':       {'P': -0.7, 'A': -0.4, 'D': -0.5},
    'angry':     {'P': -0.6, 'A': +0.8, 'D': +0.7},
    'fearful':   {'P': -0.6, 'A': +0.7, 'D': -0.6},
    'surprised': {'P': +0.2, 'A': +0.8, 'D': -0.1},
    'disgusted': {'P': -0.6, 'A': +0.2, 'D': +0.3},
}

# ---------------------------------------------------------------------------
#  Intensity Dampening (Ref 5: Yin et al. — expectation-disconfirmation)
#
#  Over-expressing positive emotion triggers cognitive dissonance in users
#  who don't expect machines to have genuine feelings. Capping intensity
#  prevents uncanny over-expression.
# ---------------------------------------------------------------------------
MAX_INTENSITY = 0.85


def get_profile(emotion: str) -> dict:
    """Get raw (unscaled) voice profile for an emotion."""
    return VOICE_PROFILES.get(emotion, NEUTRAL).copy()


def get_scaled_profile(emotion: str, intensity: float) -> dict:
    """
    Returns scaled vocal parameters + SSML-ready strings.

    Scaling formula (Ref 24):
        scaled_value = Neutral + (Target - Neutral) × damped_intensity

    Also computes:
        - ssml_rate:   percentage string for SSML <prosody rate="...">
        - ssml_pitch:  percentage string for SSML <prosody pitch="...">
        - ssml_volume: dB string for SSML <prosody volume="...">
        - pause_ms:    inter-sentence pause duration (emotion-dependent)
    """
    # Apply intensity dampening
    intensity = min(intensity, MAX_INTENSITY)

    base = VOICE_PROFILES.get(emotion, NEUTRAL)

    # Scale each parameter from neutral toward the target profile
    rate = round(
        NEUTRAL['rate'] + (base['rate'] - NEUTRAL['rate']) * intensity
    )
    pitch_shift = round(
        NEUTRAL['pitch_shift'] + (base['pitch_shift'] - NEUTRAL['pitch_shift']) * intensity,
        2
    )
    volume_db = round(
        NEUTRAL['volume_db'] + (base['volume_db'] - NEUTRAL['volume_db']) * intensity,
        2
    )

    # Generate SSML percentage strings
    rate_pct = round(((rate - NEUTRAL['rate']) / NEUTRAL['rate']) * 100)
    # ~6% per semitone (equal temperament: 2^(1/12) ≈ 1.0595 ≈ +6%)
    pitch_pct = round(pitch_shift * 6)

    # Emotion-dependent pause duration (slower emotions get longer pauses)
    if emotion in ('sad', 'disgusted'):
        pause_ms = int(400 * intensity)
    elif emotion in ('fearful', 'surprised'):
        pause_ms = int(200 * intensity)
    else:
        pause_ms = int(300 * intensity)
    pause_ms = max(150, pause_ms)  # minimum 150ms

    return {
        # Core vocal parameters (backward-compatible with existing pipeline)
        'rate':        rate,
        'pitch_shift': pitch_shift,
        'volume_db':   volume_db,
        # SSML-ready strings for direct injection into <prosody> tags
        'ssml_rate':   f"{rate_pct:+d}%",
        'ssml_pitch':  f"{pitch_pct:+d}%",
        'ssml_volume': f"{volume_db:+.0f}dB" if volume_db != 0 else "+0dB",
        # Inter-sentence pause for natural delivery
        'pause_ms':    pause_ms,
    }


if __name__ == '__main__':
    print("Research-backed voice profiles with PAD coordinates:\n")
    print(f"  {'Emotion':<12} {'Rate':>5} {'Pitch':>7} {'Vol':>6}  "
          f"{'SSML Rate':>10} {'SSML Pitch':>11} {'SSML Vol':>9} {'Pause':>6}  "
          f"{'PAD (P,A,D)'}")
    print("-" * 105)

    for emotion in VOICE_PROFILES:
        p = get_scaled_profile(emotion, 0.8)
        pad = PAD_COORDINATES.get(emotion, {})
        pad_str = f"({pad.get('P', 0):+.1f}, {pad.get('A', 0):+.1f}, {pad.get('D', 0):+.1f})"
        print(f"  {emotion:<12} {p['rate']:>5} {p['pitch_shift']:>+7.1f} {p['volume_db']:>+6.1f}  "
              f"{p['ssml_rate']:>10} {p['ssml_pitch']:>11} {p['ssml_volume']:>9} {p['pause_ms']:>5}ms  "
              f"{pad_str}")