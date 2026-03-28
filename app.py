from flask import Flask, render_template, request, jsonify, send_from_directory
from engine import process
import os

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/synthesize', methods=['POST'])
def synthesize():
    data = request.get_json()
    text = data.get('text', '').strip()

    if not text:
        return jsonify({'error': 'Please enter some text.'}), 400

    if len(text) > 500:
        return jsonify({'error': 'Text too long. Keep it under 500 characters.'}), 400

    try:
        result = process(text, output_path='static/output.wav')
        return jsonify({
            'emotion':    result['emotion'],
            'intensity':  result['intensity'],
            'rate':       result['profile']['rate'],
            'pitch':      result['profile']['pitch_shift'],
            'volume_db':  result['profile']['volume_db'],
            'ssml_rate':  result['profile'].get('ssml_rate', ''),
            'ssml_pitch': result['profile'].get('ssml_pitch', ''),
            'ssml_vol':   result['profile'].get('ssml_volume', ''),
            'pause_ms':   result['profile'].get('pause_ms', 0),
            'ssml':       result.get('ssml', ''),
            'audio_url':  '/static/output.wav',
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    os.makedirs('static', exist_ok=True)
    app.run(host="0.0.0.0", port=7860)
