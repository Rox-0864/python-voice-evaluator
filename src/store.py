"""Persistencia del historial de resultados en un archivo JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List


def load_results(path) -> List[dict]:
    """Carga el historial de resultados. Devuelve [] si no existe."""
    if not Path(path).exists():
        return []
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def save_result(path, result: dict) -> List[dict]:
    """Agrega un resultado al historial y devuelve la lista completa."""
    results = load_results(path)
    results.append(result)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2, ensure_ascii=False)
    return results
