# Melody → SATB Harmonizer

Vibe-coded app to sing or play a melody and get 4-part SATB sheet music in the browser.

## Setup (first time)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Add your Anthropic API key (get it from console.anthropic.com → API Keys):

```bash
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
```

The `.env` file is gitignored. Without it the app falls back to a simpler rule-based harmonizer.

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

## How harmonization works

The app sends your detected melody to Claude (claude-opus-4-6) with a style prompt matching the selected era. Claude generates the Alto, Tenor, and Bass voices with proper voice leading. The harmonizer backend is pluggable — see `backends/` to swap in a different model.

## Stack

- Python, FastAPI, librosa (pitch detection), music21 (MusicXML generation)
- Claude API via `anthropic` SDK (harmonization)
- OpenSheetMusicDisplay (browser sheet music rendering)
- Web Audio API (metronome + WAV capture — no ffmpeg needed)

## Tests

```bash
python -m pytest tests/ -v
```

Covers the full backend pipeline using synthetic WAV files (no API key or mic needed).
