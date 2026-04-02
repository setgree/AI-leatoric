# Melody → SATB Harmonizer

Vibe-coded app to sing or play a melody and get 4-part SATB sheet music in the browser.

## How to run

```bash
cd ~/Library/CloudStorage/Dropbox/claude-projects/AI-leatoric
source .venv/bin/activate
uvicorn backend:app --port 8000
# open http://localhost:8000
```

## Usage

1. **Tap** the beat 4+ times to set tempo → **Metronome** button activates
2. Turn on the metronome, pick an **era** (Classical / Baroque / Romantic / Jazz)
3. **Record** your melody, **Stop** when done
4. Sheet music renders in the browser; download the MusicXML to open in MuseScore for playback

## Stack

- Python, FastAPI, librosa (pitch detection), music21 (harmonization + MusicXML)
- OpenSheetMusicDisplay (browser sheet music rendering)
- Web Audio API (metronome + WAV capture — no ffmpeg needed)

## Setup (first time)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
