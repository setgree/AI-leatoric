# [claude-code/claude-sonnet-4-6] abstract interface for SATB harmonizer backends
from typing import Protocol


class HarmonizerBackend(Protocol):
    def harmonize(
        self,
        melody: list[tuple[int, float, float]],   # (midi, start_sec, end_sec)
        tonic: str,
        mode: str,
        era: str,
        bpm: float,
        voice_part: str,    # 'soprano' | 'alto' | 'tenor' | 'bass' — which part the user sang
        weirdness: int,     # 1–100, only meaningful for Claude backend
    ) -> dict[str, list[dict]]:
        """
        Returns {'soprano': [...], 'alto': [...], 'tenor': [...], 'bass': [...]}
        Each list: [{'pitch': 'C4', 'quarterLength': 1.0}, ...]
        The voice matching voice_part should follow the input melody.
        """
        ...
