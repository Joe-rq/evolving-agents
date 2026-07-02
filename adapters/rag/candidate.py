"""adapters/rag/candidate.py — retrieval strategy candidates + generators.

A candidate is a Strategy wrapping a config dict. Family = the dominant
misconfiguration. Evolution = fixing bad config values one at a time.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from adapters.rag.env import get_task, evaluate


@dataclass(frozen=True)
class Strategy:
    config: dict
    body: str
    parent_body: str = ""
    graft: str = ""
    inherited: tuple = ()

    @property
    def family(self) -> str:
        return family_of(self.config)

    def to_json(self) -> dict:
        return {"body": self.body, "family": self.family, "config": self.config,
                "parent_body": self.parent_body, "graft": self.graft}


def make_strategy(config: dict, parent_body: str = "", graft: str = "",
                  inherited: tuple = ()) -> Strategy:
    body = f"chunk={config['chunk_size']},rerank={config['rerank']},expand={config['query_expand']},th={config['threshold']},k={config['top_k']}"
    return Strategy(config=config, body=body, parent_body=parent_body,
                    graft=graft, inherited=inherited)


def family_of(config: dict) -> str:
    """Family = dominant misconfiguration."""
    cs = config.get("chunk_size", 200)
    th = config.get("threshold", 0.7)
    tk = config.get("top_k", 5)
    if cs > 500: return "chunk_too_large"
    if th < 0.4: return "threshold_too_low"
    if tk > 10: return "topk_too_large"
    if not config.get("rerank", False): return "no_rerank"
    return "tuned"


def _rand_config(rng: random.Random) -> dict:
    """Generate a random (usually bad) RAG config."""
    return {
        "chunk_size": rng.choice([50, 100, 200, 500, 1000]),
        "rerank": rng.random() < 0.3,
        "query_expand": rng.random() < 0.3,
        "threshold": rng.choice([0.3, 0.5, 0.7, 0.9]),
        "top_k": rng.choice([1, 3, 5, 10, 20]),
    }


def generate_pool(round_idx: int, seed: int, n: int = 10, task_name: str = "general_qa") -> list:
    rng = random.Random((seed * 1_000_003) ^ (round_idx * 97))
    pool = [make_strategy(_rand_config(rng)) for _ in range(n)]
    rng.shuffle(pool)
    return pool


def _graft(config: dict, rng: random.Random) -> tuple:
    """Apply ONE config fix. Returns (new_config, graft_desc)."""
    new = dict(config)
    desc = "no-op"

    # fix chunk_size first (highest impact)
    cs = new["chunk_size"]
    if cs > 500:
        new["chunk_size"] = rng.choice([150, 200])
        desc = f"chunk {cs}→{new['chunk_size']}"
    elif cs < 100:
        new["chunk_size"] = 150
        desc = f"chunk {cs}→150"
    elif new["threshold"] < 0.5:
        old = new["threshold"]
        new["threshold"] = 0.7
        desc = f"th {old}→0.7"
    elif new["top_k"] > 8:
        old = new["top_k"]
        new["top_k"] = rng.choice([4, 5])
        desc = f"k {old}→{new['top_k']}"
    elif not new["rerank"]:
        new["rerank"] = True
        desc = "+rerank"
    elif not new["query_expand"]:
        new["query_expand"] = True
        desc = "+expand"
    elif new["chunk_size"] != 150:
        new["chunk_size"] = 150
        desc = f"chunk→150"

    return new, desc


def generate_pool_aware(memory, round_idx: int, seed: int, universe: str,
                        n: int = 10, explore_ratio: float = 0.3) -> list:
    rng = random.Random((seed * 1_000_003) ^ (round_idx * 97) ^ 0xA67)  # 'RAG'
    attempts = memory.attempts(universe) if memory is not None else []
    if not attempts:
        return generate_pool(round_idx, seed, n, universe)

    clues = []
    for a in attempts:
        score = -1
        for k in (a.evidence_kinds or set()):
            if isinstance(k, str) and k.startswith("score:"):
                try: score = int(k.split(":")[1])
                except: pass
        if score >= 0:
            clues.append((score, a.body, a.features))

    if not clues:
        return generate_pool(round_idx, seed, n, universe)

    clues.sort(key=lambda t: t[0], reverse=True)
    # recover config from body string
    seen = set()
    roots = []
    for _, body, _ in clues:
        if body not in seen:
            seen.add(body)
            config = _parse_body(body)
            if config:
                roots.append((body, config))
        if len(roots) >= 6:
            break

    pool = []
    n_ext = max(1, int(round(n * (1.0 - explore_ratio))))
    n_exp = n - n_ext
    weights = [1.0 / (i + 1) for i in range(len(roots))]

    for _ in range(n_ext):
        root_body, root_config = rng.choices(roots, weights=weights, k=1)[0]
        new_config, graft_desc = _graft(root_config, rng)
        pool.append(make_strategy(new_config, parent_body=root_body,
                                  graft=graft_desc, inherited=("root",)))
    for _ in range(n_exp):
        pool.append(make_strategy(_rand_config(rng)))
    rng.shuffle(pool)
    return pool


def _parse_body(body: str) -> dict:
    """Parse a body string back to a config dict."""
    try:
        config = {"chunk_size": 200, "rerank": False, "query_expand": False, "threshold": 0.7, "top_k": 5}
        for part in body.split(","):
            if "=" in part:
                k, v = part.split("=", 1)
                k = k.strip()
                if k == "chunk": config["chunk_size"] = int(v)
                elif k == "rerank": config["rerank"] = v == "True"
                elif k == "expand": config["query_expand"] = v == "True"
                elif k == "th": config["threshold"] = float(v)
                elif k == "k": config["top_k"] = int(v)
        return config
    except Exception:
        return None
