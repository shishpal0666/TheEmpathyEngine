# The Empathy Engine

> AI-powered Text-to-Speech that detects emotion and modulates
> voice parameters in real time — built entirely at zero cost.

## Demo
[screenshot of the web UI showing an angry sentence with params displayed]
[screenshot of happy sentence]

## Features
- Detects 7 emotions: joy, anger, sadness, fear, disgust, surprise, neutral
- Modulates rate (wpm), pitch (semitones), and volume (dB) per emotion
- Intensity scaling: mild sentences get subtle changes, intense ones get strong modulation
- Web UI with live audio player — no CLI needed
- 100% free, 100% offline (after first model download)

## Setup
```bash
git clone https://github.com/yourusername/empathy-engine
cd empathy-engine
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
python app.py
# Open http://localhost:5000
```

## Emotion-to-Voice Mapping

| Emotion   | Rate (wpm) | Pitch (st) | Volume (dB) | Psychological basis |
|-----------|-----------|------------|-------------|---------------------|
| happy     | 180       | +2         | +2          | Energetic, upbeat   |
| angry     | 175       | -1         | +5          | Loud, clipped       |
| sad       | 105       | -3         | -3          | Slow, quiet         |
| neutral   | 150       | 0          | 0           | Baseline            |
| fearful   | 190       | +3         | -1          | Fast, anxious whisper |
| surprised | 195       | +5         | +3          | Fast, high pitch    |
| disgusted | 120       | -2         | -1          | Slow, flat          |

## Intensity Scaling
Parameters scale continuously with emotion confidence:

| Sentence                    | Intensity | Rate | Pitch |
|-----------------------------|-----------|------|-------|
| "This is good."             | 0.25      | 154  | +0.5  |
| "This is really good!"      | 0.55      | 167  | +1.1  |
| "This is the BEST EVER!!"   | 0.92      | 178  | +1.84 |

## Design Choices
- **VADER + HuggingFace**: VADER as fallback, HF (j-hartmann model) as primary for 7-class classification
- **Coqui TTS / gTTS**: Core modularity. Will use Coqui if supported, otherwise flawless fallback to gTTS.
- **pydub pitch shift**: frame-rate manipulation approximates pitch change; noted limitation is a minor duration artifact at extreme values.
- **Intensity interpolation**: linear blend between neutral and full emotion profile based on model confidence score.

## Tech Stack
- Emotion: vaderSentiment + HuggingFace transformers
- TTS: Coqui TTS (optional) / gTTS (fallback)
- Audio processing: pydub
- Web: Flask + vanilla JS
- Cost: $0.00
