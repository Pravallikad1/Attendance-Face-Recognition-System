"""Small helpers for stabilising anti-spoofing predictions across video frames."""

from collections import deque
from typing import Dict, Hashable


class LivenessVoteAggregator:
    """
    Aggregate per-frame liveness predictions for a tracked face.

    A track only becomes REAL/SPOOF when enough non-UNKNOWN predictions agree.
    Otherwise it remains UNKNOWN. This prevents one noisy frame from marking
    attendance.
    """

    def __init__(self, history_size: int = 5, min_votes: int = 3):
        if history_size < 1:
            raise ValueError("history_size must be >= 1")
        if min_votes < 1 or min_votes > history_size:
            raise ValueError("min_votes must be between 1 and history_size")

        self.history_size = history_size
        self.min_votes = min_votes
        self._history: Dict[Hashable, deque] = {}

    def update(self, track_id: Hashable, result: dict) -> dict:
        history = self._history.setdefault(
            track_id, deque(maxlen=self.history_size)
        )
        history.append(result)

        real = [r for r in history if r.get("label") == "REAL"]
        spoof = [r for r in history if r.get("label") == "SPOOF"]

        if len(real) >= self.min_votes and len(real) > len(spoof):
            label = "REAL"
            selected = real
        elif len(spoof) >= self.min_votes and len(spoof) > len(real):
            label = "SPOOF"
            selected = spoof
        else:
            label = "UNKNOWN"
            selected = list(history)

        confidence = (
            sum(float(r.get("confidence", 0.0)) for r in selected)
            / len(selected)
            if selected
            else 0.0
        )

        return {
            "label": label,
            "confidence": confidence,
            "frames_seen": len(history),
            "real_votes": len(real),
            "spoof_votes": len(spoof),
        }

    def reset(self, track_id: Hashable = None):
        if track_id is None:
            self._history.clear()
        else:
            self._history.pop(track_id, None)
