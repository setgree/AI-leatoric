from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import uuid
import os
import soundfile as sf
import numpy as np
import librosa
from harmonizer import harmonize_melody
from synth import synth_stream

OUT_DIR = "outputs"
XML_DIR = os.path.join(OUT_DIR, "musicxml")
AUDIO_DIR = os.path.join(OUT_DIR, "audio")
os.makedirs(XML_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/outputs", StaticFiles(directory=OUT_DIR), name="outputs")


@app.get("/")
def index():
    with open("static/index.html", "r") as f:
        return HTMLResponse(f.read())


@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    # save uploaded file
    uid = uuid.uuid4().hex
    tmp_path = f"/tmp/{uid}_{file.filename}"
    content = await file.read()
    with open(tmp_path, "wb") as f:
        f.write(content)

    try:
        y, sr = sf.read(tmp_path)
        if y.ndim > 1:
            y = np.mean(y, axis=1)
    except Exception:
        # fallback to librosa loader
        y, sr = librosa.load(tmp_path, sr=None, mono=True)

    # basic pitch extraction (monophonic assumed)
    hop_length = 256
    f0, voiced_flag, voiced_prob = librosa.pyin(
        y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'), sr=sr, hop_length=hop_length
    )

    times = librosa.times_like(f0, sr=sr, hop_length=hop_length)
    # onset detection to segment notes
    onset_frames = librosa.onset.onset_detect(y=y, sr=sr, hop_length=hop_length)
    onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=hop_length)
    if len(onset_times) == 0:
        onset_times = np.array([0.0])

    # build simple melody (midi, start, end)
    melody = []
    for i, st in enumerate(onset_times):
        en = onset_times[i+1] if i+1 < len(onset_times) else times[-1]
        # select median f0 inside this window
        mask = (times >= st) & (times < en) & (~np.isnan(f0))
        if not np.any(mask):
            continue
        freq = np.median(f0[mask])
        midi = int(np.round(librosa.hz_to_midi(freq)))
        melody.append((int(midi), float(st), float(en)))

    # fallback if empty
    if not melody:
        return JSONResponse({"error": "no melody detected"}, status_code=400)

    score = harmonize_melody(melody)

    xml_path = os.path.join(XML_DIR, f"{uid}.musicxml")
    score.write('musicxml', fp=xml_path)

    audio_path = os.path.join(AUDIO_DIR, f"{uid}.wav")
    synth_stream(score, audio_path)

    return JSONResponse({
        "musicxml": f"/outputs/musicxml/{uid}.musicxml",
        "audio": f"/outputs/audio/{uid}.wav",
    })
