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

### 2. Emotion to Voice Parameter Mapping

The translation of emotion to speech parameters happens in `voice_mapper.py`. We defined baseline "Neutral" properties:

- **Rate:** 150 words per minute (wpm)
- **Pitch Shift:** 0 semitones
- **Volume:** 0 dB

Each detected emotion modifies these properties according to specific profiles:

- **Happy / Excited:** Increased speech rate (180-210), higher pitch (+2 to +4 semitones), and increased volume.
- **Sad:** Significantly slower speech rate (105), lower pitch (-3 semitones), and decreased volume (-3 dB).
- **Angry:** Faster speech rate (175), slightly lower pitch (-1 semitone), and abruptly increased volume (+5 dB).
- **Fearful:** Faster speech rate (190), elevated pitch (+3 semitones).
- **Surprised:** Faster speech rate (195), elevated pitch (+5 semitones), and increased volume (+3 dB).
- **Disgusted:** Slower speech rate (120), lower pitch (-2 semitones).

### 3. Intensity Scaling

The intensity (confidence score from the emotion detector) is used to linearly scale the vocal parameter adjustments:

```python
scaled_parameter = Neutral_Value + (Target_Emotion_Value - Neutral_Value) * intensity
```

This ensures that a "mildly happy" sentence doesn't sound overwhelmingly ecstatic, while a "deeply sad" sentence receives the full pitch and speed reduction.

### 4. TTS Engine & Pydub Effects

For audio synthesis (`tts_engine.py`), the app primarily relies on **Coqui TTS** for high-quality, natural-sounding speech. If Coqui is missing or fails, the engine gracefully falls back to **gTTS** (Google TTS).

- After raw audio generation, we use `pydub` (`AudioSegment`) to manipulate the pitch (by tweaking the sample frame rate) and volume (db amplification) according to our scaled parameters, before exporting the final `.wav` file to the static output folder.
