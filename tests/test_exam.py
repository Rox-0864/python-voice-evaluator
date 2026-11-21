"""Tests de la lógica del modo examen."""

from __future__ import annotations

from src.exam import select_questions, summarize_exam


def _preguntas(n=10):
    return [{"id": str(i), "categoria": "A", "pregunta": f"q{i}"} for i in range(n)]


def test_select_questions_respects_n():
    sel = select_questions(_preguntas(), 3, seed=42)
    assert len(sel) == 3


def test_select_questions_n_greater_than_pool():
    sel = select_questions(_preguntas(4), 10)
    assert len(sel) == 4


def test_select_questions_by_category():
    qs = [
        {"id": "a", "categoria": "A"},
        {"id": "b", "categoria": "B"},
        {"id": "c", "categoria": "B"},
    ]
    sel = select_questions(qs, 5, categoria="B")
    assert len(sel) == 2
    assert all(q["categoria"] == "B" for q in sel)


def test_select_questions_deterministic_with_seed():
    qs = _preguntas(10)
    assert select_questions(qs, 3, seed=42) == select_questions(qs, 3, seed=42)


def test_summarize_exam_empty():
    assert summarize_exam([]) == {"n": 0, "promedio": 0, "aprobado": False}


def test_summarize_exam_aprobado():
    res = summarize_exam([{"puntaje": 80}, {"puntaje": 60}, {"puntaje": 40}])
    assert res["n"] == 3
    assert res["promedio"] == 60
    assert res["aprobado"] is True


def test_summarize_exam_reprobado():
    res = summarize_exam([{"puntaje": 30}, {"puntaje": 40}])
    assert res["aprobado"] is False
