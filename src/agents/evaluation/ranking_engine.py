"""
Ranking Engine untuk memilih dan mengurutkan kandidat denah berdasarkan RFP-A.
"""

from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def rank_candidates(
    candidates: List[Dict[str, Any]],
    score_key: str = "rfpa.composite_score",
    top_k: int = 5,
    reverse: bool = True,
) -> List[Dict[str, Any]]:
    """
    Mengurutkan kandidat berdasarkan skor dan mengembalikan top_k terbaik.

    Args:
        candidates: List kandidat denah.
        score_key: Dotted key ke skor (default 'rfpa.composite_score').
        top_k: Jumlah kandidat terbaik.
        reverse: True = skor tertinggi di urutan pertama.

    Returns:
        List kandidat terurut, masing-masing dengan 'rank'.
    """
    def get_score(cand):
        keys = score_key.split(".")
        val = cand
        try:
            for k in keys:
                val = val[k]
            return float(val)
        except (KeyError, TypeError, ValueError):
            logger.warning(f"Score key '{score_key}' tidak ditemukan. Default 0.0")
            return 0.0

    sorted_candidates = sorted(candidates, key=get_score, reverse=reverse)
    top_candidates = sorted_candidates[:top_k]

    for i, cand in enumerate(top_candidates):
        cand["rank"] = i + 1

    return top_candidates


def assign_rank(
    candidates: List[Dict[str, Any]],
    score_key: str = "scores.composite",
    reverse: bool = True,
) -> List[Dict[str, Any]]:
    """
    Memberi rank tanpa memotong jumlah.
    """
    def get_score(cand):
        keys = score_key.split(".")
        val = cand
        try:
            for k in keys:
                val = val[k]
            return float(val)
        except (KeyError, TypeError, ValueError):
            return 0.0

    sorted_candidates = sorted(candidates, key=get_score, reverse=reverse)
    for i, cand in enumerate(sorted_candidates):
        cand["rank"] = i + 1
    return sorted_candidates