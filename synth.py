import numpy as np
import soundfile as sf
from music21 import instrument, note
import math


def _sine(frequency, duration, sr=22050, amp=0.2):
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    return amp * np.sin(2 * math.pi * frequency * t)


def synth_stream(score, out_wav, sr=22050):
    # Extract parts (assumes four parts in order S,A,T,B)
    parts = list(score.parts)
    # Collect events: (start_sec, duration_sec, frequency)
    events = []
    # music21 quarterLength -> seconds at tempo 100 BPM: quarter = 60/100 = 0.6s
    tempo = 100.0
    sec_per_quarter = 60.0 / tempo
    for p_idx, p in enumerate(parts):
        time_cursor = 0.0
        for el in p.recurse().notes:
            if isinstance(el, note.Rest):
                time_cursor += el.quarterLength * sec_per_quarter
                continue
            freq = el.pitch.frequency
            dur = el.quarterLength * sec_per_quarter
            events.append((time_cursor, dur, freq))
            time_cursor += dur

    if not events:
        return

    total_dur = max([st + dur for st, dur, f in events])
    audio = np.zeros(int(total_dur * sr) + 1)

    for st, dur, f in events:
        s = _sine(f, dur, sr=sr, amp=0.15)
        start_idx = int(st * sr)
        audio[start_idx:start_idx + len(s)] += s

    # normalize
    maxv = np.max(np.abs(audio))
    if maxv > 0:
        audio = audio / maxv * 0.9

    sf.write(out_wav, audio, sr)
