# AI-leatoric

Vibe-coded app to sing or play a melody and get 4-part SATB sheet music in the browser.

## Setup (first time)

Requires Python 3.11 (not 3.14 — ML dependencies haven't caught up yet):

```bash
brew install python@3.11
/opt/homebrew/bin/python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Add your Anthropic API key (get it from console.anthropic.com → API Keys):

```bash
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
```

The `.env` file is gitignored. Without it the app falls back to a local rule-based harmonizer.

## How to run

```bash
cd ~/Library/CloudStorage/Dropbox/claude-projects/AI-leatoric
source .venv/bin/activate
uvicorn backend:app --port 8000
# open http://localhost:8000
```

## Usage

1. **Set tempo** — drag the BPM slider (40–200); optionally turn on the metronome
2. **Choose settings** — harmonizer (Claude API or Local), which voice you're singing, era, weirdness
3. **Record** your melody, **Stop** when done
4. Sheet music renders in the browser; download the MusicXML to open in MuseScore for playback

## How harmonization works

Pitch detection uses Basic Pitch (Spotify's neural net model), which handles cello and voice
including low frequencies and vibrato. Detected notes are passed to the selected harmonizer:

- **Claude API** — sends melody to claude-opus-4-6 with style/era/weirdness prompt; generates
  proper voice leading for all three other parts
- **Local** — rule-based diatonic harmony; no API key needed; no voice leading

The harmonizer backend is pluggable — see `backends/` to swap in a different model.

## Stack

- Python 3.11, FastAPI, Basic Pitch (pitch detection), music21 (MusicXML generation)
- Claude API via `anthropic` SDK (harmonization)
- OpenSheetMusicDisplay (browser sheet music rendering)
- Web Audio API (metronome + WAV capture — no ffmpeg needed)

## Tests

```bash
python -m pytest tests/ -v
```

17 tests covering the full backend pipeline using synthetic WAV files (no API key or mic needed).
