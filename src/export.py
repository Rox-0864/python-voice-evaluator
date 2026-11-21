"""Exportación de resultados a CSV y PDF."""

from __future__ import annotations

from typing import List

import pandas as pd
from fpdf import FPDF


def to_dataframe(results: List[dict]) -> pd.DataFrame:
    return pd.DataFrame(results)


def to_csv(results: List[dict]) -> bytes:
    return to_dataframe(results).to_csv(index=False).encode("utf-8")


def to_pdf(results: List[dict]) -> bytes:
    """Genera un PDF simple con una fila por evaluación.

    Usa la fuente estándar (latin-1), reemplazando caracteres no soportados.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)

    for r in results:
        for k, v in r.items():
            text = f"{k}: {v}"
            # fpdf con fuente estándar solo soporta latin-1.
            text = text.encode("latin-1", errors="replace").decode("latin-1")
            pdf.cell(0, 8, txt=text, ln=True)
        pdf.ln(4)

    return pdf.output(dest="S").encode("latin-1")
