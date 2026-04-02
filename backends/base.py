# [claude-code/claude-sonnet-4-6] abstract interface for SATB harmonizer backends
# Any backend must accept melody + style params and return SATB as a dict of note lists.
# This makes it trivial to swap Claude API for DeepBach, a local model, etc.
from typing import Protocol


class NoteDict(dict):
    """
    A single note: {"pitch": "C4", "quarterLength": 1.0}
    pitch is a music21-compatible string (e.g. "F#4", "Bb3", "C4")
    quarterLength is in beats (1.0 = quarter note)
    """
    pass


class HarmonizerBackend(Protocol):
    def harmonize(
        self,
        melody: list[tuple[int, float, float]],   # (midi, start_sec, end_sec)
        tonic: str,
        mode: str,
        era: str,
        bpm: float,
    ) -> dict[str, list[NoteDict]]:
        """
        Returns a dict with keys 'soprano', 'alto', 'tenor', 'bass'.
        Each value is a list of NoteDict: [{"pitch": "C4", "quarterLength": 1.0}, ...]
        Soprano should follow the input melody; alto/tenor/bass are generated.
        """
        ...
