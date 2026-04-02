# [claude-code/claude-sonnet-4-6] rule-based SATB harmonizer: melody (midi, start_sec, end_sec) → music21 Score
from music21 import stream, note, tempo, meter, key
import music21
import numpy as np


def _choose_chord(midi, tonic_midi, triads):
    """Return chord tone offsets for the triad that contains this melody pitch class."""
    pc = midi % 12
    for tones in triads.values():
        chord_pcs = [(tonic_midi + t) % 12 for t in tones]
        if pc in chord_pcs:
            return tones
    return triads['I']


def harmonize_melody(melody, tonic='C', bpm=80):
    """
    melody: list of (midi, start_sec, end_sec)
    bpm: used to convert seconds → quarter lengths
    Returns a music21 Score with four parts (S, A, T, B).
    """
    beat_sec = 60.0 / bpm

    s_part = stream.Part(id='Soprano')
    a_part = stream.Part(id='Alto')
    t_part = stream.Part(id='Tenor')
    b_part = stream.Part(id='Bass')

    for p in (s_part, a_part, t_part, b_part):
        p.append(tempo.MetronomeMark(number=bpm))
        p.append(meter.TimeSignature('4/4'))
        p.append(key.Key(tonic))

    # diatonic triads in major (semitone offsets from tonic)
    triads = {
        'I':   [0, 4, 7],
        'ii':  [2, 5, 9],
        'iii': [4, 7, 11],
        'IV':  [5, 9, 0],
        'V':   [7, 11, 2],
        'vi':  [9, 0, 4],
    }

    tonic_midi = music21.pitch.Pitch(tonic).midi

    for midi, st, en in melody:
        # convert duration in seconds to quarter lengths
        dur_sec = max(en - st, 0.25)
        ql = max(0.5, round((dur_sec / beat_sec) * 2) / 2)  # round to nearest 0.5 ql

        tones = _choose_chord(midi, tonic_midi, triads)

        # voice each part in a sensible SATB register
        soprano_midi = midi
        alto_midi    = tonic_midi + tones[2]          # third of chord, middle register
        tenor_midi   = tonic_midi + tones[1] - 12     # fifth of chord, one octave down
        bass_midi    = tonic_midi + tones[0] - 12     # root, low register

        # nudge voices into conventional ranges
        # soprano: C4–G5 (60–79), alto: G3–C5 (55–72), tenor: C3–G4 (48–67), bass: E2–C4 (40–60)
        def clamp(m, lo, hi):
            while m < lo:
                m += 12
            while m > hi:
                m -= 12
            return m

        soprano_midi = clamp(soprano_midi, 60, 79)
        alto_midi    = clamp(alto_midi,    55, 72)
        tenor_midi   = clamp(tenor_midi,   48, 67)
        bass_midi    = clamp(bass_midi,    40, 60)

        def make_note(m, ql):
            return note.Note(music21.pitch.Pitch(m).nameWithOctave, quarterLength=ql)

        s_part.append(make_note(soprano_midi, ql))
        a_part.append(make_note(alto_midi,    ql))
        t_part.append(make_note(tenor_midi,   ql))
        b_part.append(make_note(bass_midi,    ql))

    sc = stream.Score()
    sc.append(s_part)
    sc.append(a_part)
    sc.append(t_part)
    sc.append(b_part)
    return sc
