# Stuff done (progress snapshot)

Date: 2026-02-22

Summary
- Defined MVP pipeline and tech choices for a melody → SATB harmonizer.
- Scaffolded a minimal Python FastAPI prototype (backend + static UI).
- Implemented a simple rule-based harmonizer and a small sine-wave synth for playback.

Files added
- `requirements.txt` — dependency list.
- `backend.py` — FastAPI app: upload endpoint, basic f0 extraction (librosa.pyin), onset segmentation, harmonization call, MusicXML + WAV output.
- `harmonizer.py` — rule-based SATB harmonizer (diatonic triad assignment, returns a music21 Score).
- `synth.py` — tiny sine synthesizer that renders the Score to a WAV.
- `static/index.html` — minimal browser UI to upload audio and play returned audio / open MusicXML.
- `README.md` — quickstart and notes.

How to run (local)
```bash
python -m pip install -r requirements.txt
uvicorn backend:app --reload --host 0.0.0.0 --port 8000
# open http://localhost:8000
```

Known limitations
- Assumes mostly monophonic input (voice/cello). Not production-grade transcription.
- Harmonizer is a simple diatonic rule-based baseline (C major default).
- No era/adventurousness controls yet.

Next planned steps
- Improve pitch segmentation and vibrato smoothing.
- Add key detection and support for non-C keys.
- Add era/adventurousness parameters and map them to harmonization strategies (rule-based + ML models like DeepBach/Coconet).
- Add better UI rendering (MusicXML -> OpenSheetMusicDisplay) and tempo-preserving playback of SATB parts.

I'll amend this file at the end of the session with a full summary of everything done.
