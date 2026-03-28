"""
emotion_detector.py — Dual-layer emotion detection with intensity enrichment.

Uses HuggingFace DistilRoBERTa for granular emotion classification (7 categories)
with VADER as both a fallback and an intensity enrichment source. Includes emoji
parsing and typographic intensity detection for improved arousal scoring.

References:
    - Ref 22 (Prosody of Emojis): Emojis as explicit prosodic markers
    - Ref 24 (PAD Mapping): Typographic cues map to Arousal dimension
    - Ref 25 (VADER): Compound score for intensity scaling
    - Ref 27 (VADER vs LLM): VADER superiority on unbalanced sentiment data
"""
import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from transformers import pipeline

# ---------------------------------------------------------------------------
#  Emoji-to-Emotion Mapping (Ref 22: prosodic convergence)
# ---------------------------------------------------------------------------
EMOJI_EMOTIONS = {
    '😊': 'happy', '😃': 'happy', '😁': 'happy', '🎉': 'happy', '❤️': 'happy',
    '😄': 'happy', '🥰': 'happy', '😍': 'happy', '🙂': 'happy', '👍': 'happy',
    '😢': 'sad',   '😭': 'sad',   '💔': 'sad',   '😞': 'sad',   '😔': 'sad',
    '😡': 'angry', '🤬': 'angry', '💢': 'angry', '😠': 'angry',
    '😱': 'fearful',   '😰': 'fearful',   '😨': 'fearful',
    '😲': 'surprised', '🤯': 'surprised', '😮': 'surprised',
    '🤢': 'disgusted', '🤮': 'disgusted',
}

def extract_emoji_cues(text: str) -> tuple[str, list[str]]:
    """
    Strip emojis from text and return (clean_text, detected_emoji_emotions).
    Emojis are removed before TTS synthesis since they cannot be spoken,
    but their emotional signal is preserved for intensity scoring.
    """
    emotions = []
    for emoji, emotion in EMOJI_EMOTIONS.items():
        if emoji in text:
            emotions.append(emotion)
            text = text.replace(emoji, '')
    return text.strip(), emotions


def compute_typographic_boost(text: str) -> float:
    """
    Returns an arousal boost (0.0 to 0.15) from typographic intensity cues.
    Based on Ref 24: capitalization and punctuation map to the PAD Arousal dimension.
    
    - ALL CAPS words → higher arousal → max +0.10
    - Exclamation marks → intensity amplifier → max +0.05
    """
    boost = 0.0
    words = text.split()
    if words:
        # Count fully capitalized words (skip short ones like "I", "A")
        caps_count = sum(1 for w in words if w.isupper() and len(w) > 1)
        caps_ratio = caps_count / len(words)
        boost += min(caps_ratio * 0.2, 0.10)
    # Exclamation density
    excl_count = text.count('!')
    boost += min(excl_count * 0.02, 0.05)
    return round(boost, 3)


# ---------------------------------------------------------------------------
#  VADER Sentiment Analyzer (Fallback + Intensity Source)
# ---------------------------------------------------------------------------
_vader = SentimentIntensityAnalyzer()

def detect_with_vader(text: str) -> tuple[str, float]:
    """
    Lexicon-based sentiment detection using VADER.
    Returns (emotion_label, intensity) where intensity = |compound|.
    Particularly strong at detecting punctuation/capitalization arousal (Ref 25).
    """
    scores = _vader.polarity_scores(text)
    compound = scores['compound']
    intensity = abs(compound)

    if compound >= 0.5:
        return 'happy', intensity
    elif compound >= 0.1:
        return 'positive', intensity
    elif compound <= -0.5:
        return 'angry', intensity
    elif compound <= -0.1:
        return 'sad', intensity
    else:
        return 'neutral', intensity


# ---------------------------------------------------------------------------
#  HuggingFace Transformer (Primary — Granular Classification)
# ---------------------------------------------------------------------------
print("Loading emotion model... (first run downloads ~250MB)")
_hf_classifier = pipeline(
    task="text-classification",
    model="j-hartmann/emotion-english-distilroberta-base",
    top_k=1,
    device=-1  # CPU
)
print("Model loaded.")

HF_TO_INTERNAL = {
    'joy':      'happy',
    'anger':    'angry',
    'sadness':  'sad',
    'fear':     'fearful',
    'disgust':  'disgusted',
    'surprise': 'surprised',
    'neutral':  'neutral',
}

def detect_with_hf(text: str) -> tuple[str, float]:
    """Granular emotion classification using DistilRoBERTa (7 emotions, Ref 28)."""
    result = _hf_classifier(text)[0][0]
    raw_label = result['label'].lower()
    confidence = result['score']
    label = HF_TO_INTERNAL.get(raw_label, 'neutral')
    return label, confidence


# ---------------------------------------------------------------------------
#  Main Combined Function — Dual-Layer Blending
# ---------------------------------------------------------------------------
def detect_emotion(text: str, use_hf: bool = True) -> tuple[str, float]:
    """
    Main entry point for emotion detection with enriched intensity scoring.

    Pipeline:
        1. Extract emoji cues and clean text
        2. Compute typographic arousal boost (caps, punctuation)
        3. Detect emotion via HuggingFace (label) + VADER (intensity blend)
        4. Apply typographic and emoji boosts to final intensity

    Returns (emotion_label, intensity)
        emotion_label: happy | angry | sad | fearful | surprised | disgusted | neutral | positive
        intensity: 0.0 to 1.0
    """
    # Step 1: Extract emojis (strip for cleaner NLP, keep signal for intensity)
    clean_text, emoji_emotions = extract_emoji_cues(text)

    # Step 2: Typographic arousal from original text (caps, !!!)
    typo_boost = compute_typographic_boost(text)

    # Step 3: Dual-layer emotion detection
    try:
        if use_hf:
            # HuggingFace for the emotion label
            hf_label, hf_confidence = detect_with_hf(clean_text if clean_text else text)
            # VADER for intensity enrichment (better at caps/punctuation detection)
            _, vader_intensity = detect_with_vader(text)
            # Blend: 70% HF confidence + 30% VADER compound magnitude
            blended_intensity = 0.7 * hf_confidence + 0.3 * vader_intensity
            label = hf_label
        else:
            label, blended_intensity = detect_with_vader(text)
    except Exception as e:
        print(f"HF detector error: {e}. Falling back to VADER.")
        label, blended_intensity = detect_with_vader(text)

    # Step 4: Apply typographic boost
    final_intensity = blended_intensity + typo_boost

    # Step 5: Emoji confirmation boost
    if emoji_emotions and label in emoji_emotions:
        final_intensity += 0.05  # Small boost when emoji confirms HF label

    # Clamp to [0.0, 1.0]
    final_intensity = round(min(1.0, max(0.0, final_intensity)), 4)

    return label, final_intensity


if __name__ == '__main__':
    test_sentences = [
        ("I just got the job offer — this is incredible!", "happy"),
        ("I am absolutely furious about this complete disaster.", "angry"),
        ("I feel so lost and alone right now.", "sad"),
        ("The meeting is scheduled for 3pm tomorrow.", "neutral"),
        ("Oh great, another Monday.", "angry/sad"),
        ("That was a pretty good presentation.", "positive/happy"),
        ("THIS IS THE BEST NEWS EVER!!!", "happy (caps + !!!)"),
        ("I'm so happy! 😊😊😊", "happy (emoji)"),
    ]

    print(f"{'Sentence':<50} {'Detected':<20} {'Intensity':<10}")
    print("-" * 80)
    for sentence, expected in test_sentences:
        emotion, intensity = detect_emotion(sentence, use_hf=True)
        typo = compute_typographic_boost(sentence)
        _, emojis = extract_emoji_cues(sentence)
        print(f"{sentence[:48]:<50} {emotion:<20} {intensity:.4f}  "
              f"(typo_boost={typo}, emojis={emojis})")