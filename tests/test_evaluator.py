"""Tests de la lógica de puntaje y el banco de preguntas (sin APIs externas)."""

from __future__ import annotations

import pytest

from src import evaluator, questions


def test_score_keywords_finds_matches():
    aciertos, total = evaluator.score_keywords(
        "uso print para imprimir en la consola", ["print", "consola", "input"]
    )
    assert aciertos == 2
    assert total == 3


def test_score_keywords_case_insensitive():
    aciertos, _ = evaluator.score_keywords("Print y PRINT", ["print"])
    assert aciertos == 1


def test_coverage_to_grade():
    assert evaluator.coverage_to_grade(0, 4) == 0
    assert evaluator.coverage_to_grade(2, 4) == 50
    assert evaluator.coverage_to_grade(4, 4) == 100


def test_grade_band():
    assert evaluator.grade_band(90) == ("🎉", "green")
    assert evaluator.grade_band(30) == ("😟", "red")


def test_generar_mensaje():
    ok = evaluator.generar_mensaje("Ana", 9, 10)
    fail = evaluator.generar_mensaje("Ana", 4, 10)
    assert "Felicidades" in ok
    assert "repasar" in fail


def test_questions_validate_and_categories(tmp_path):
    import json

    path = tmp_path / "preguntas.json"
    data = [
        {
            "id": "a",
            "categoria": "Fundamentos",
            "pregunta": "¿Qué es print?",
            "palabras_clave": ["print"],
            "contexto_ideal": "print muestra en consola",
        },
        {
            "id": "b",
            "categoria": "Funciones",
            "pregunta": "¿Qué es def?",
            "palabras_clave": ["def"],
            "contexto_ideal": "def define una función",
        },
    ]
    path.write_text(json.dumps(data), encoding="utf-8")

    loaded = questions.load_questions(path)
    assert questions.validate_questions(loaded) == []
    assert questions.categories(loaded) == ["Fundamentos", "Funciones"]
    assert len(questions.filter_by_category(loaded, "Funciones")) == 1


def test_questions_validate_detects_missing_field(tmp_path):
    import json

    path = tmp_path / "preguntas.json"
    path.write_text(json.dumps([{"id": "a", "pregunta": "x"}]), encoding="utf-8")
    problems = questions.validate_questions(questions.load_questions(path))
    assert len(problems) >= 2  # faltan palabras_clave y contexto_ideal
