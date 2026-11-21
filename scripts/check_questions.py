"""Valida el banco de preguntas (data/preguntas.json)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import questions as qbank  # noqa: E402


def main() -> int:
    path = Path("data/preguntas.json")
    if not path.exists():
        print(f"ERROR: no existe {path}")
        return 1

    preguntas = qbank.load_questions(path)
    problems = qbank.validate_questions(preguntas)

    if problems:
        print("Problemas encontrados:")
        for p in problems:
            print(f"  - {p}")
        return 1

    print(f"OK: {len(preguntas)} preguntas válidas.")
    for c in qbank.categories(preguntas):
        n = len(qbank.filter_by_category(preguntas, c))
        print(f"  {c}: {n} preguntas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
