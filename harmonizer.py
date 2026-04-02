# [claude-code/claude-sonnet-4-6] rule-based SATB harmonizer with era parameter
# era options: 'classical' | 'baroque' | 'romantic' | 'jazz'
from music21 import stream, note, chord, tempo, meter, key
import music21
import numpy as np


# [claude-code/claude-sonnet-4-6] chord vocabularies per era
# Each entry: list of semitone offsets from tonic (root, 3rd, 5th, [7th])
ERA_TRIADS = {
    'classical': {
        'major': {
            'I':   [0, 4, 7],
            'ii':  [2, 5, 9],
            'IV':  [5, 9, 0],
            'V':   [7, 11, 2],
            'vi':  [9, 0, 4],
        },
        'minor': {
            'i':   [0, 3, 7],
            'iv':  [5, 8, 0],
            'V':   [7, 11, 2],
            'VI':  [8, 0, 3],
            'VII': [10, 2, 5],
        },
    },
    'baroque': {
        # like classical but V always has the 7th (V7) for stronger cadences
        'major': {
            'I':   [0, 4, 7],
            'ii':  [2, 5, 9],
            'IV':  [5, 9, 0],
            'V7':  [7, 11, 2, 5],   # dominant seventh
            'vi':  [9, 0, 4],
        },
        'minor': {
            'i':   [0, 3, 7],
            'iv':  [5, 8, 0],
            'V7':  [7, 11, 2, 5],
            'VI':  [8, 0, 3],
        },
    },
    'romantic': {
        # 7th chords throughout for richer color
        'major': {
            'Imaj7': [0, 4, 7, 11],
            'ii7':   [2, 5, 9, 0],
            'IVmaj7':[5, 9, 0, 4],
            'V7':    [7, 11, 2, 5],
            'vi7':   [9, 0, 4, 7],
        },
        'minor': {
            'im7':   [0, 3, 7, 10],
            'iv7':   [5, 8, 0, 3],
            'V7':    [7, 11, 2, 5],
            'VImaj7':[8, 0, 3, 7],
            'VII7':  [10, 2, 5, 8],
        },
    },
    'jazz': {
        # extended harmony: 7ths, with tritone sub on V
        'major': {
            'Imaj7': [0, 4, 7, 11],
            'ii7':   [2, 5, 9, 0],
            'IVmaj7':[5, 9, 0, 4],
            'V7':    [7, 11, 2, 5],
            'vi7':   [9, 0, 4, 7],
            'bVII7': [10, 2, 5, 8],  # tritone sub / blues influence
        },
        'minor': {
            'im7':   [0, 3, 7, 10],
            'ii7b5': [2, 5, 8, 0],   # half-diminished
            'iv7':   [5, 8, 0, 3],
            'V7':    [7, 11, 2, 5],
            'VImaj7':[8, 0, 3, 7],
        },
    },
}


def _best_chord(midi, tonic_midi, chords):
    """Return (name, tones) for the chord whose tones contain this melody pitch class."""
    pc = midi % 12
    for name, tones in chords.items():
        chord_pcs = [(tonic_midi + t) % 12 for t in tones]
        if pc in chord_pcs:
            return name, tones
    # fallback: first chord (tonic)
    first = next(iter(chords.items()))
    return first


def _clamp(m, lo, hi):
    while m < lo:
        m += 12
    while m > hi:
        m -= 12
    return m


def harmonize_melody(melody, tonic='C', mode='major', bpm=80, era='classical'):
    """
    melody : list of (midi, start_sec, end_sec)
    tonic  : e.g. 'C', 'G', 'Bb'
    mode   : 'major' | 'minor'
    bpm    : used to convert seconds → quarter lengths
    era    : 'classical' | 'baroque' | 'romantic' | 'jazz'
    Returns a music21 Score with four parts (S, A, T, B).
    """
    beat_sec = 60.0 / bpm

    # fall back gracefully if era/mode combo not found
    vocab = ERA_TRIADS.get(era, ERA_TRIADS['classical']).get(mode, ERA_TRIADS['classical']['major'])

    s_part = stream.Part(id='Soprano')
    a_part = stream.Part(id='Alto')
    t_part = stream.Part(id='Tenor')
    b_part = stream.Part(id='Bass')

    for p in (s_part, a_part, t_part, b_part):
        p.append(tempo.MetronomeMark(number=bpm))
        p.append(meter.TimeSignature('4/4'))
        p.append(key.Key(tonic, mode))

    tonic_midi = music21.pitch.Pitch(tonic).midi

    for midi, st, en in melody:
        dur_sec = max(en - st, 0.25)
        ql = max(0.5, round((dur_sec / beat_sec) * 2) / 2)

        _, tones = _best_chord(midi, tonic_midi, vocab)

        # soprano always follows the melody
        soprano_midi = midi

        # assign alto, tenor, bass from chord tones[1], [2], [0]
        # for 7th chords (4 tones), distribute across voices more fully
        if len(tones) >= 4:
            alto_midi  = tonic_midi + tones[2]
            tenor_midi = tonic_midi + tones[3] - 12
            bass_midi  = tonic_midi + tones[0] - 12
        else:
            alto_midi  = tonic_midi + tones[2]
            tenor_midi = tonic_midi + tones[1] - 12
            bass_midi  = tonic_midi + tones[0] - 12

        # clamp to SATB ranges: soprano C4–G5, alto G3–C5, tenor C3–G4, bass E2–C4
        soprano_midi = _clamp(soprano_midi, 60, 79)
        alto_midi    = _clamp(alto_midi,    55, 72)
        tenor_midi   = _clamp(tenor_midi,   48, 67)
        bass_midi    = _clamp(bass_midi,    40, 60)

        def mn(m, ql):
            return note.Note(music21.pitch.Pitch(m).nameWithOctave, quarterLength=ql)

        s_part.append(mn(soprano_midi, ql))
        a_part.append(mn(alto_midi,    ql))
        t_part.append(mn(tenor_midi,   ql))
        b_part.append(mn(bass_midi,    ql))

    sc = stream.Score()
    sc.append(s_part)
    sc.append(a_part)
    sc.append(t_part)
    sc.append(b_part)
    return sc
