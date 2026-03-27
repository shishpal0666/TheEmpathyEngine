"""
demo_intensity.py
Generates 3 audio files showing intensity scaling in action.
"""
from engine import process

demos = [
    ("static/demo_mild.wav",   "This is good."),
    ("static/demo_medium.wav", "This is really good, I'm happy with it!"),
    ("static/demo_strong.wav", "This is absolutely the best thing that has ever happened!"),
]

print("Generating intensity scaling demo files...")
for path, sentence in demos:
    result = process(sentence, output_path=path)
    print(f"  [{result['emotion']}] intensity={result['intensity']} "
          f"rate={result['profile']['rate']} "
          f"pitch={result['profile']['pitch_shift']:+.2f} → {path}")

print("\nDone. Listen to the 3 files and compare — the modulation increases with intensity.")

# Phase 4.2 Emotion Showcase
print("\nGenerating the full emotion showcase...")
emotion_demos = {
    "happy":     "I just received the best news of my entire career!",
    "angry":     "I cannot believe they cancelled the project without any warning!",
    "sad":       "I miss them so much, everything reminds me of what we had.",
    "fearful":   "I have no idea what's going to happen and I'm terrified.",
    "surprised": "Wait — they actually accepted the proposal? I had no idea!",
    "neutral":   "The document has been reviewed and filed accordingly.",
    "disgusted": "That was honestly the worst presentation I have ever witnessed.",
}

for emotion_name, sentence in emotion_demos.items():
    path = f"static/demo_{emotion_name}.wav"
    result = process(sentence, output_path=path)
    print(f"{emotion_name:12} → detected={result['emotion']}, "
          f"intensity={result['intensity']}, saved to {path}")
