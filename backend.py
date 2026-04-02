# [claude-code/claude-sonnet-4-6] FastAPI backend: mic audio → Basic Pitch detection → SATB harmonization → MusicXML
from dotenv import load_dotenv
load_dotenv()  # loads .env file — ANTHROPIC_API_KEY goes there, never in git

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional
import uuid
import os
import numpy as np
import music21
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


# [claude-code/claude-sonnet-4-6] snap note onsets/durations to eighth-note grid at given BPM
def quantize_melody(melody, bpm):
    if not bpm or bpm <= 0:
        return melody
    eighth_sec = (60.0 / bpm) / 2

    def snap(t):      return round(t / eighth_sec) * eighth_sec
    def snap_dur(d):  return max(eighth_sec, round(d / eighth_sec) * eighth_sec)

    return [(midi, snap(st), snap(st) + snap_dur(en - st)) for midi, st, en in melody]


# [claude-code/claude-sonnet-4-6] use Basic Pitch (Spotify) for pitch detection
# Tuned for human voice / cello: longer minimum note, higher thresholds, outlier filtering
def detect_melody_basic_pitch(audio_path):
    from basic_pitch.inference import predict
    from basic_pitch import ICASSP_2022_MODEL_PATH

    _, midi_data, _ = predict(
        audio_path,
        ICASSP_2022_MODEL_PATH,
        minimum_note_length=200,    # ms — filters short attack/breath artifacts (default ~128ms)
        onset_threshold=0.6,        # slightly stricter onset detection (default 0.5)
        frame_threshold=0.4,        # slightly stricter frame confidence (default 0.3)
        minimum_frequency=50.0,     # below cello open C (~65Hz) to catch everything
        maximum_frequency=1200.0,   # above soprano high C, caps phantom harmonics
    )

    melody = []
    for instrument in midi_data.instruments:
        for note in instrument.notes:
            melody.append((int(note.pitch), float(note.start), float(note.end)))

    melody.sort(key=lambda x: x[1])

    # drop outlier pitches more than 2 octaves from median
    if len(melody) >= 3:
        midis = [m for m, _, _ in melody]
        median_midi = sorted(midis)[len(midis) // 2]
        melody = [(m, st, en) for m, st, en in melody if abs(m - median_midi) <= 24]

    # [claude-code/claude-sonnet-4-6] merge consecutive same-pitch notes
    # Basic Pitch often splits one sustained note into two; merge if gap < 150ms
    merged = []
    for note in melody:
        if merged and merged[-1][0] == note[0] and (note[1] - merged[-1][2]) < 0.15:
            merged[-1] = (merged[-1][0], merged[-1][1], note[2])  # extend end time
        else:
            merged.append(list(note))
    melody = [tuple(n) for n in merged]

    return melody


@app.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    bpm: Optional[float] = Form(None),
    era: Optional[str] = Form('classical'),
    voice_part: Optional[str] = Form('soprano'),
    weirdness: Optional[int] = Form(50),
    use_claude: Optional[str] = Form('true'),
):
    uid = uuid.uuid4().hex
    tmp_path = f"/tmp/{uid}_{file.filename}"
    content = await file.read()
    with open(tmp_path, "wb") as f:
        f.write(content)

    try:
        melody = detect_melody_basic_pitch(tmp_path)
    except Exception as e:
        return JSONResponse({"error": f"pitch detection failed: {str(e)}"}, status_code=500)
    finally:
        try: os.unlink(tmp_path)
        except: pass

    if not melody:
        return JSONResponse({"error": "no melody detected"}, status_code=400)

    melody = quantize_melody(melody, bpm)

    # detect key from melody notes
    key_stream = music21.stream.Stream()
    for midi, _, _ in melody:
        key_stream.append(music21.note.Note(midi))
    detected_key = key_stream.analyze('key')
    tonic = detected_key.tonic.name
    mode  = detected_key.mode

    if use_claude == 'true':
        from backends.claude_api import ClaudeBackend
        backend = ClaudeBackend()
    else:
        from backends.rule_based import RuleBasedBackend
        backend = RuleBasedBackend()

    score = harmonize_melody(melody, tonic=tonic, mode=mode, bpm=bpm or 80,
                             era=era or 'classical', voice_part=voice_part or 'soprano',
                             weirdness=weirdness or 50, backend=backend)

    xml_path = os.path.join(XML_DIR, f"{uid}.musicxml")
    score.write('musicxml', fp=xml_path)

    import music21 as m21
    detected_notes = [m21.pitch.Pitch(midi).nameWithOctave for midi, _, _ in melody]

    return JSONResponse({
        "musicxml": f"/outputs/musicxml/{uid}.musicxml",
        "uid": uid,
        "key": f"{tonic} {mode}",
        "era": era,
        "detected_notes": detected_notes,
    })
