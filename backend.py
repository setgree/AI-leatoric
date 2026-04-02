# [claude-code/claude-sonnet-4-6] FastAPI backend: mic audio → pitch detection → SATB harmonization → MusicXML
from dotenv import load_dotenv
load_dotenv()  # loads .env file if present — ANTHROPIC_API_KEY goes there, never in git

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional
import uuid
import os
import soundfile as sf
import numpy as np
import librosa
from harmonizer import harmonize_melody

OUT_DIR = "outputs"
XML_DIR = os.path.join(OUT_DIR, "musicxml")
os.makedirs(XML_DIR, exist_ok=True)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/outputs", StaticFiles(directory=OUT_DIR), name="outputs")


@app.get("/")
def index():
    with open("static/index.html", "r") as f:
        return HTMLResponse(f.read())


# [claude-code/claude-sonnet-4-6] snap note onsets and durations to a beat grid given BPM
def quantize_melody(melody, bpm):
    if not bpm or bpm <= 0:
        return melody
    beat_sec = 60.0 / bpm          # quarter note duration in seconds
    eighth_sec = beat_sec / 2      # smallest grid unit

    def snap(t):
        return round(t / eighth_sec) * eighth_sec

    def snap_dur(d):
        snapped = max(eighth_sec, round(d / eighth_sec) * eighth_sec)
        return snapped

    quantized = []
    for midi, st, en in melody:
        q_st = snap(st)
        q_dur = snap_dur(en - st)
        quantized.append((midi, q_st, q_st + q_dur))
    return quantized


@app.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    bpm: Optional[float] = Form(None),
    era: Optional[str] = Form('classical'),
):
    uid = uuid.uuid4().hex
    tmp_path = f"/tmp/{uid}_{file.filename}"
    content = await file.read()
    with open(tmp_path, "wb") as f:
        f.write(content)

    try:
        y, sr = sf.read(tmp_path)
        if y.ndim > 1:
            y = np.mean(y, axis=1)
        y = y.astype(np.float32)
    except Exception:
        y, sr = librosa.load(tmp_path, sr=None, mono=True)

    hop_length = 256
    # [claude-code/claude-sonnet-4-6] pyin handles cello range well (C2–C7)
    f0, voiced_flag, _ = librosa.pyin(
        y,
        fmin=librosa.note_to_hz('C2'),
        fmax=librosa.note_to_hz('C7'),
        sr=sr,
        hop_length=hop_length,
    )

    times = librosa.times_like(f0, sr=sr, hop_length=hop_length)
    onset_frames = librosa.onset.onset_detect(y=y, sr=sr, hop_length=hop_length)
    onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=hop_length)
    if len(onset_times) == 0:
        onset_times = np.array([0.0])

    melody = []
    for i, st in enumerate(onset_times):
        en = onset_times[i + 1] if i + 1 < len(onset_times) else times[-1]
        mask = (times >= st) & (times < en) & (~np.isnan(f0)) & voiced_flag
        if not np.any(mask):
            continue
        freq = np.median(f0[mask])
        midi = int(np.round(librosa.hz_to_midi(freq)))
        melody.append((int(midi), float(st), float(en)))

    if not melody:
        return JSONResponse({"error": "no melody detected"}, status_code=400)

    melody = quantize_melody(melody, bpm)

    # [claude-code/claude-sonnet-4-6] detect key from melody using music21's Krumhansl-Schmuckler analysis
    import music21
    key_stream = music21.stream.Stream()
    for midi, st, en in melody:
        key_stream.append(music21.note.Note(midi))
    detected_key = key_stream.analyze('key')
    tonic = detected_key.tonic.name
    mode = detected_key.mode  # 'major' or 'minor'

    score = harmonize_melody(melody, tonic=tonic, mode=mode, bpm=bpm or 80, era=era or 'classical')

    xml_path = os.path.join(XML_DIR, f"{uid}.musicxml")
    score.write('musicxml', fp=xml_path)

    return JSONResponse({
        "musicxml": f"/outputs/musicxml/{uid}.musicxml",
        "uid": uid,
        "key": f"{tonic} {mode}",
        "era": era,
    })
