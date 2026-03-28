# The Empathy Engine

**🔴 Live Demo:** [https://shishpal0666-theempathyengine.hf.space](https://shishpal0666-theempathyengine.hf.space)

The Empathy Engine is a Python-based web service that performs sentiment and emotion analysis on input text and generates emotionally expressive speech audio. Moving beyond robotic Text-to-Speech (TTS), this application maps detected emotions to specific vocal parameters (speech rate, pitch, and volume) to produce dynamic, human-like voice synthesis.

## Project Highlights

- **Emotion Detection:** Uses a HuggingFace text-classification pipeline (`j-hartmann/emotion-english-distilroberta-base`) to detect 7 distinct emotions with confidence scores.
- **Robustness:** Includes a fallback to VADER Sentiment Analysis for offline, fast, or error-resilient processing.
- **Voice Mapping:** Dynamically adjusts speech rate, pitch shift, and volume based on the detected emotion and its intensity.
- **TTS Synthesis:** Integrates Coqui TTS for high-quality voice generation, with a reliable fallback to Google TTS (gTTS).
- **Web Interface:** Features a simple and intuitive Flask-based frontend for users to input text and play the generated audio directly in the browser.

## Setup and Installation

Follow these step-by-step instructions to set up the environment and run the application locally.

### Prerequisites

- **Python 3.11+** installed on your system.
- **FFmpeg** and **libsndfile** installed (required by `pydub` and audio libraries).
  - **Windows:** Download FFmpeg executables manually from the official site and add them to your system's PATH, or use a package manager (`choco install ffmpeg` / `winget install ffmpeg`).
  - **macOS:** Install manually using Homebrew (`brew install ffmpeg`).
  - **Linux:** Use your package manager (e.g., `sudo apt install ffmpeg libsndfile1`).

### 1. Clone or Download the Repository

Navigate to your project folder:

```bash
git clone https://github.com/yourusername/TheEmpathyEngine.git
cd TheEmpathyEngine
```

### 2. Create a Virtual Environment

It is highly recommended to run the project in an isolated virtual environment.

```bash
python -m venv venv
```

Activate the virtual environment:

- **Windows:** `venv\Scripts\activate`
- **macOS/Linux:** `source venv/bin/activate`

### 3. Install Dependencies

Install the required Python packages from `requirements.txt`.

```bash
pip install -r requirements.txt
```

### 4. Run the Application

Start the Flask development server:

```bash
python app.py
```

> **Note:** The first run may take some time as it downloads the HuggingFace emotion model (~250MB) and the Coqui TTS model (if installed and available).

Open your web browser and navigate to: `http://localhost:7860`

### Docker Setup (Optional)

To run the application inside a Docker container:

```bash
docker build -t empathy-engine .
docker run -p 7860:7860 empathy-engine
```

## Design Choices & Emotion-to-Voice Logic

The core of The Empathy Engine lies in how text is analyzed and translated into expressive speech. Here is a breakdown of the key design choices:

### 1. Emotion Detection Pipeline

We use a dual-layer approach for emotion detection (`emotion_detector.py`):

- **Primary:** HuggingFace `j-hartmann/emotion-english-distilroberta-base`. This gives us granular emotion categories (joy/happy, anger, sadness, fear, disgust, surprise, neutral) with high accuracy and confidence scores.
- **Fallback:** VADER Sentiment Analysis. If the HuggingFace model fails or is unavailable, we fallback to VADER to calculate a compound sentiment score, which is then mapped to simple baseline emotions (happy, positive, angry, sad, neutral).

### 2. Emotion to Voice Parameter Mapping (PAD Framework)

The translation of emotion to speech parameters happens in `voice_mapper.py`. We evolved from simple baseline modifiers to using the **Pleasure-Arousal-Dominance (PAD)** dimensional emotion model (Russell & Mehrabian), based on research by Murray & Arnott (2000).

- **Rate:** 150 words per minute (wpm) baseline
- **Pitch Shift:** 0 semitones baseline
- **Volume:** 0 dB baseline

Each emotion is mapped to PAD coordinates, where **Arousal (A)** is the primary driver for rate and pitch:
- **Happy / Excited (High Arousal, High Pleasure):** Increased speech rate (195-210), higher pitch (+3 to +4 semitones), and increased volume.
- **Sad (Low Arousal, Low Pleasure):** Slower speech rate (135), lower flat pitch (-3 semitones), and decreased volume (-3 dB). 
- **Angry (High Arousal, Low Pleasure):** Faster speech rate (195), slightly lower pitch (-1 semitone), and abruptly increased volume (+6 dB).
- **Fearful (High Arousal, Low Dominance):** Faster speech rate (195), elevated pitch (+4 semitones).

### 3. Intensity Scaling and Dampening

The intensity (confidence score blending HuggingFace + VADER and typographic cues like ALL CAPS or `!!!`) is used to linearly scale the vocal parameter adjustments:

```python
scaled_parameter = Neutral_Value + (Target_Emotion_Value - Neutral_Value) * intensity
```

To prevent the "uncanny valley" effect of machines over-expressing emotions (expectation-disconfirmation theory), we applied a strict **Maximum Intensity Cap (0.85)**. This ensures that even "mildly happy" sentences scale appropriately, while extreme emotions never cross into artificial hyper-expression.

### 4. Native SSML and TTS Pipeline (Bonus Objective)

For audio synthesis (`tts_engine.py`), the app implements **Speech Synthesis Markup Language (SSML)** to gain true parametric control over the voice.

We adopted the following priority fallback chain:
1. **edge-tts (Microsoft Neural Voices):** Our primary engine. It natively parses our generated `<prosody rate="..." pitch="..." volume="...">` and `<break time="...ms"/>` SSML tags, rendering highly natural, independent pitch and rate variance without post-processing distortion.
2. **Coqui TTS:** High-quality offline fallback (Tacotron2-DDC) using `pydub` frame-rate adjustments to simulate prosody.
3. **gTTS:** Last-resort online fallback using `pydub` for offline modifications.
