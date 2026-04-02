# [claude-code/claude-sonnet-4-6] orchestrator: calls selected backend, converts output to music21 Score
# To swap backends, change the import or pass backend= to harmonize_melody().
# Backend interface is defined in backends/base.py.
from music21 import stream, note, tempo, meter, key, clef, instrument
import music21

# re-export ERA_TRIADS so existing tests that import it still work
from backends.rule_based import ERA_TRIADS


def _make_part(part_id, instr, cl, bpm, tonic, mode, notes):
    p = stream.Part(id=part_id)
    p.partName = part_id
    p.insert(0, instr)
    p.append(tempo.MetronomeMark(number=bpm))
    p.append(meter.TimeSignature('4/4'))
    p.append(key.Key(tonic, mode))
    p.append(cl)
    for nd in notes:
        p.append(note.Note(nd['pitch'], quarterLength=nd['quarterLength']))
    return p


def harmonize_melody(melody, tonic='C', mode='major', bpm=80, era='classical',
                     voice_part='soprano', weirdness=50, backend=None):
    """
    melody  : list of (midi, start_sec, end_sec)
    backend : a HarmonizerBackend instance, or None to use ClaudeBackend (with rule-based fallback)
    Returns a music21 Score with four parts (S, A, T, B).
    """
    if backend is None:
        from backends.claude_api import ClaudeBackend
        backend = ClaudeBackend()

    satb = backend.harmonize(melody, tonic=tonic, mode=mode, era=era, bpm=bpm,
                             voice_part=voice_part, weirdness=weirdness)

    parts = [
        _make_part('Soprano', instrument.Soprano(), clef.TrebleClef(),     bpm, tonic, mode, satb['soprano']),
        _make_part('Alto',    instrument.Alto(),    clef.TrebleClef(),     bpm, tonic, mode, satb['alto']),
        _make_part('Tenor',   instrument.Tenor(),   clef.Treble8vbClef(), bpm, tonic, mode, satb['tenor']),
        _make_part('Bass',    instrument.Bass(),    clef.BassClef(),       bpm, tonic, mode, satb['bass']),
    ]

    sc = stream.Score()
    for p in parts:
        sc.append(p)

    sc.makeMeasures(inPlace=True)
    for p in sc.parts:
        p.makeBeams(inPlace=True)

    return sc
