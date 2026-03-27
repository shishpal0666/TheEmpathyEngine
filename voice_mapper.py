NEUTRAL = {'rate': 150, 'pitch_shift': 0, 'volume_db': 0}

VOICE_PROFILES = {
    'happy':     {'rate': 180, 'pitch_shift': +2, 'volume_db': +2},
    'excited':   {'rate': 210, 'pitch_shift': +4, 'volume_db': +4},
    'positive':  {'rate': 165, 'pitch_shift': +1, 'volume_db': +1},
    'neutral':   {'rate': 150, 'pitch_shift':  0, 'volume_db':  0},
    'sad':       {'rate': 105, 'pitch_shift': -3, 'volume_db': -3},
    'angry':     {'rate': 175, 'pitch_shift': -1, 'volume_db': +5},
    'fearful':   {'rate': 190, 'pitch_shift': +3, 'volume_db': -1},
    'surprised': {'rate': 195, 'pitch_shift': +5, 'volume_db': +3},
    'disgusted': {'rate': 120, 'pitch_shift': -2, 'volume_db': -1},
}

def get_profile(emotion: str) -> dict:
    return VOICE_PROFILES.get(emotion, NEUTRAL).copy()

def get_scaled_profile(emotion: str, intensity: float) -> dict:
    base = VOICE_PROFILES.get(emotion, NEUTRAL)
    scaled = {
        'rate': round(
            NEUTRAL['rate'] + (base['rate'] - NEUTRAL['rate']) * intensity
        ),
        'pitch_shift': round(
            NEUTRAL['pitch_shift'] + (base['pitch_shift'] - NEUTRAL['pitch_shift']) * intensity,
            2
        ),
        'volume_db': round(
            NEUTRAL['volume_db'] + (base['volume_db'] - NEUTRAL['volume_db']) * intensity,
            2
        ),
    }
    return scaled

if __name__ == '__main__':
    print("Full profiles:")
    for emotion in VOICE_PROFILES:
        p = get_scaled_profile(emotion, 0.8)
        print(f"  {emotion:12} rate={p['rate']} pitch={p['pitch_shift']:+.1f} vol={p['volume_db']:+.1f}dB")