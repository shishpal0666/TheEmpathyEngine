from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from transformers import pipeline

# --- VADER Fallback Setup ---
_vader = SentimentIntensityAnalyzer()

def detect_with_vader(text: str) -> tuple[str, float]:
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

# --- HuggingFace Primary Setup ---
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
    result = _hf_classifier(text)[0][0]
    raw_label = result['label'].lower()
    confidence = result['score']
    label = HF_TO_INTERNAL.get(raw_label, 'neutral')
    return label, confidence

# --- Main Combined Function ---
def detect_emotion(text: str, use_hf: bool = True) -> tuple[str, float]:
    try:
        if use_hf:
            return detect_with_hf(text)
        else:
            return detect_with_vader(text)
    except Exception as e:
        print(f"HF detector error: {e}. Falling back to VADER.")
        return detect_with_vader(text)

if __name__ == '__main__':
    test_sentences = [
        ("I just got the job offer — this is incredible!", "happy"),
        ("I am absolutely furious about this complete disaster.", "angry"),
        ("I feel so lost and alone right now.", "sad"),
        ("The meeting is scheduled for 3pm tomorrow.", "neutral"),
        ("Oh great, another Monday.", "angry/sad"),
    ]

    print(f"{'Sentence':<50} {'HF Result':<20} {'VADER Result':<20}")
    print("-" * 90)
    for sentence, expected in test_sentences:
        hf_emotion, hf_score = detect_with_hf(sentence)
        vader_emotion, vader_score = detect_with_vader(sentence)
        print(f"{sentence[:48]:<50} {hf_emotion}({hf_score:.2f})  {vader_emotion}({vader_score:.2f})")