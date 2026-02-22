# PROTOTYPE — VIBE CODING TEST

THIS REPOSITORY IS A PROTOTYPE / EXPERIMENTAL VIBE CODING TEST. IT IS NOT PRODUCTION SOFTWARE.

# Melody → SATB Harmonizer (MVP)

Small prototype that accepts a short monophonic audio file (voice or bowed string),
estimates pitched notes, produces a simple four-part (SATB) harmonization, and
exports both MusicXML and a synthesized WAV for quick listening.

Goals
- Provide a testable pipeline for: audio → pitch/onsets → rule-based harmonization → render/playback.
- Produce a baseline that can be iterated with better transcription models and style-conditioned harmonizers.

Requirements
- Python 3.10+ recommended.
- Uses `librosa`, `music21`, `soundfile`, `fastapi`, and `uvicorn`.

Quickstart (local)

1. Create and activate a virtual environment (recommended):

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

3. Run the FastAPI server:

```bash
uvicorn backend:app --reload --host 0.0.0.0 --port 8000
```

4. Open the UI at http://localhost:8000 and upload a short WAV (mono/stereo accepted).

What the app does
- `backend.py`: accepts uploaded audio, uses `librosa.pyin` for f0 estimation and `librosa.onset` for segmentation, then calls the harmonizer.
- `harmonizer.py`: simple rule-based SATB harmonizer that assigns diatonic triads and maps melody notes to soprano; returns a `music21.Score`.
- `synth.py`: tiny sine-wave synthesizer that mixes parts and writes a WAV for preview.

Outputs
- MusicXML files are written to `outputs/musicxml/` and are viewable with MuseScore or other viewers.
- Rendered WAV previews are written to `outputs/audio/` and are served at `/outputs/audio/<id>.wav`.

Testing ideas
- Sing or play a simple monophonic tune (e.g., "Mary Had a Little Lamb").
- Upload and verify: the soprano line should approximate your melody, and three lower voices provide a basic SATB texture.

Limitations & next steps
- Monophonic-first: the transcription is simple and will struggle with polyphony or heavy vibrato. Consider `CREPE` or Magenta's `Onsets and Frames` for improvements.
- Key detection is not implemented — currently defaults to C major; add `librosa`/`music21` key inference.
- Harmonizer is conservative/diatonic — plan to add era/adventurousness sliders wired to rule relaxations or ML models (DeepBach/Coconet/Music Transformer).

Contributing / development notes
- The static UI is at `static/index.html` and the server is `backend.py`.
- To iterate on the harmonizer, edit `harmonizer.py` and re-run the server. MusicXML output can be opened in MuseScore or rendered in-browser with OpenSheetMusicDisplay.

Contact
- If you want me to refine transcription, add UI sliders, or wire up model-based harmonizers, tell me which task to do next.

