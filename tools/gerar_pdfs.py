"""Gerador reproduzível dos PDFs de entrega do TaskAnalyzer.

Converte os documentos Markdown do repositório em PDF formatado, para que os
artefatos da Fase 3 possam ser regenerados sempre que a fonte mudar.

Uso:
    python tools/gerar_pdfs.py

Entradas e saídas:
    specs/task_analyzer_spec.md        -> specs/system_design_document.pdf
    docs/relatorio_governanca_etica.md -> docs/relatorio_governanca_etica.pdf

Dependência: reportlab (não faz parte de requirements.txt, que é restrito às
dependências de execução e teste exigidas pelo contrato — regra P01).
    pip install reportlab
"""

from __future__ import annotations

import html
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

RAIZ = Path(__file__).resolve().parent.parent
AZUL = colors.HexColor("#1F3864")
CINZA = colors.HexColor("#444444")
FUNDO_CODIGO = colors.HexColor("#F2F2F2")

_base = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=_base["Heading1"], fontSize=14, textColor=AZUL,
                    spaceBefore=14, spaceAfter=8)
H2 = ParagraphStyle("H2", parent=_base["Heading2"], fontSize=11.5, textColor=AZUL,
                    spaceBefore=11, spaceAfter=5)
H3 = ParagraphStyle("H3", parent=_base["Heading3"], fontSize=10.5, textColor=CINZA,
                    spaceBefore=9, spaceAfter=4)
BODY = ParagraphStyle("BODY", parent=_base["BodyText"], fontSize=9.5, leading=14,
                      alignment=TA_JUSTIFY, spaceAfter=6)
ITEM = ParagraphStyle("ITEM", parent=BODY, leftIndent=14, bulletIndent=4, spaceAfter=3)
CODE = ParagraphStyle("CODE", parent=_base["BodyText"], fontName="Courier", fontSize=8,
                      leading=10.5, leftIndent=8, spaceAfter=6, backColor=FUNDO_CODIGO)
QUOTE = ParagraphStyle("QUOTE", parent=BODY, leftIndent=12, textColor=CINZA,
                       borderPadding=4)
CELL = ParagraphStyle("CELL", parent=_base["BodyText"], fontSize=8, leading=10.5,
                      spaceAfter=0)
CELLB = ParagraphStyle("CELLB", parent=CELL, fontName="Helvetica-Bold")
TITULO = ParagraphStyle("TITULO", parent=_base["Title"], fontSize=19, textColor=AZUL,
                        spaceAfter=6)
SUB = ParagraphStyle("SUB", parent=_base["Title"], fontSize=11.5, textColor=CINZA,
                     spaceAfter=16)
CAP = ParagraphStyle("CAP", parent=_base["BodyText"], fontSize=8.5, leading=11,
                     alignment=TA_CENTER, textColor=CINZA)


@dataclass(frozen=True)
class Documento:
    """Metadados de um PDF a ser gerado."""

    origem: Path
    destino: Path
    titulo: str
    subtitulo: str
    rodape: str
    pular_ate_h1: bool = False


def inline(texto: str) -> str:
    """Converte marcação inline do Markdown em marcação do ReportLab.

    Trechos entre crases são isolados antes das regras de ênfase, para que
    asteriscos e sublinhados dentro de identificadores de código (por exemplo
    ``test_ca01_*``) não sejam lidos como itálico.
    """
    texto = html.escape(texto, quote=False)
    reservados: list[str] = []

    def reservar(match: re.Match[str]) -> str:
        reservados.append(match.group(1))
        return f"\x00{len(reservados) - 1}\x00"

    texto = re.sub(r"`([^`]+)`", reservar, texto)
    texto = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", texto)
    texto = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", texto)
    texto = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<i>\1</i>", texto)
    for indice, conteudo in enumerate(reservados):
        texto = texto.replace(
            f"\x00{indice}\x00",
            f"<font face='Courier' size='8.5'>{conteudo}</font>",
        )
    return texto


def montar_tabela(linhas: list[str], largura_util: float) -> Table:
    """Monta uma tabela do ReportLab a partir de linhas no formato pipe do Markdown."""
    dados = []
    for bruta in linhas:
        if re.fullmatch(r"\s*\|[\s:\-|]+\|\s*", bruta):
            continue
        celulas = [c.strip() for c in bruta.strip().strip("|").split("|")]
        dados.append(celulas)
    if not dados:
        return Table([[""]])
    colunas = max(len(linha) for linha in dados)
    dados = [linha + [""] * (colunas - len(linha)) for linha in dados]
    corpo = [
        [Paragraph(inline(c), CELLB if i == 0 else CELL) for c in linha]
        for i, linha in enumerate(dados)
    ]
    tabela = Table(corpo, colWidths=[largura_util / colunas] * colunas, repeatRows=1)
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9E2F3")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#8EA9DB")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return tabela


def converter(markdown: str, largura_util: float, pular_ate_h1: bool) -> list:
    """Converte o corpo Markdown em uma lista de flowables do ReportLab."""
    flow: list = []
    linhas = markdown.splitlines()
    i = 0
    comecou = not pular_ate_h1
    while i < len(linhas):
        linha = linhas[i]
        if not comecou:
            if linha.startswith("## "):
                comecou = True
            else:
                i += 1
                continue
        if linha.startswith("```"):
            bloco = []
            i += 1
            while i < len(linhas) and not linhas[i].startswith("```"):
                bloco.append(html.escape(linhas[i], quote=False))
                i += 1
            i += 1
            flow.append(Paragraph("<br/>".join(bloco).replace(" ", "&nbsp;"), CODE))
            continue
        if linha.strip().startswith("|"):
            bloco = []
            while i < len(linhas) and linhas[i].strip().startswith("|"):
                bloco.append(linhas[i])
                i += 1
            flow.append(KeepTogether([montar_tabela(bloco, largura_util), Spacer(1, 6)]))
            continue
        if re.fullmatch(r"\s*-{3,}\s*", linha):
            flow.append(Spacer(1, 4))
            flow.append(HRFlowable(width="100%", color=colors.HexColor("#BBBBBB"),
                                   thickness=0.5))
            flow.append(Spacer(1, 4))
            i += 1
            continue
        if linha.startswith("#### "):
            flow.append(Paragraph(inline(linha[5:]), H3))
        elif linha.startswith("### "):
            flow.append(Paragraph(inline(linha[4:]), H3))
        elif linha.startswith("## "):
            flow.append(Paragraph(inline(linha[3:]), H1))
        elif linha.startswith("# "):
            flow.append(Paragraph(inline(linha[2:]), H1))
        elif linha.startswith("> "):
            flow.append(Paragraph(inline(linha[2:]), QUOTE))
        elif re.match(r"\s*[-*] ", linha):
            bloco = [re.sub(r"^\s*[-*] ", "", linha)]
            i += 1
            while i < len(linhas) and re.match(r"^\s{2,}\S", linhas[i]) and not re.match(
                r"\s*[-*] ", linhas[i]
            ):
                bloco.append(linhas[i].strip())
                i += 1
            marcador = "\u2022"
            texto = " ".join(bloco)
            if texto.startswith("[x] "):
                marcador, texto = "\u2713", texto[4:]
            elif texto.startswith("[ ] "):
                marcador, texto = "\u25a1", texto[4:]
            flow.append(Paragraph(inline(texto), ITEM, bulletText=marcador))
            continue
        elif re.match(r"\s*\d+\. ", linha):
            numero = re.match(r"\s*(\d+)\. ", linha).group(1)
            bloco = [re.sub(r"^\s*\d+\. ", "", linha)]
            i += 1
            while i < len(linhas) and re.match(r"^\s{2,}\S", linhas[i]):
                bloco.append(linhas[i].strip())
                i += 1
            flow.append(Paragraph(inline(" ".join(bloco)), ITEM, bulletText=f"{numero}."))
            continue
        elif linha.strip():
            # Junta as linhas seguintes do mesmo parágrafo: no Markdown a quebra
            # é cosmética, e unir evita que ênfases abertas numa linha e fechadas
            # na próxima fiquem sem par.
            bloco = [linha.strip()]
            i += 1
            while i < len(linhas) and linhas[i].strip() and not re.match(
                r"\s*(#{1,4} |[-*] |\d+\. |\||>|```|-{3,}\s*$)", linhas[i]
            ):
                bloco.append(linhas[i].strip())
                i += 1
            flow.append(Paragraph(inline(" ".join(bloco)), BODY))
            continue
        i += 1
    return flow


def gerar(doc: Documento) -> None:
    """Gera um PDF a partir da configuração informada."""
    origem = RAIZ / doc.origem
    destino = RAIZ / doc.destino
    if not origem.exists():
        raise FileNotFoundError(f"Arquivo de origem não encontrado: {origem}")
    destino.parent.mkdir(parents=True, exist_ok=True)

    margem_esq, margem_dir = 2.3 * cm, 2.0 * cm
    largura_util = A4[0] - margem_esq - margem_dir

    story: list = [
        Spacer(1, 1.0 * cm),
        Paragraph(doc.titulo, TITULO),
        Paragraph(doc.subtitulo, SUB),
        HRFlowable(width="100%", color=AZUL, thickness=1.2),
        Spacer(1, 0.5 * cm),
        Paragraph(
            f"Repositório: github.com/PedroVargas1204/sdd-task-analyzer<br/>"
            f"Documento gerado automaticamente por <font face='Courier' size='8.5'>"
            f"tools/gerar_pdfs.py</font> a partir de "
            f"<font face='Courier' size='8.5'>{doc.origem}</font><br/>"
            f"Data de geração: {date.today().strftime('%d/%m/%Y')}",
            CAP,
        ),
        Spacer(1, 0.5 * cm),
    ]
    story += converter(origem.read_text(encoding="utf-8"), largura_util, doc.pular_ate_h1)

    template = SimpleDocTemplate(
        str(destino), pagesize=A4,
        leftMargin=margem_esq, rightMargin=margem_dir,
        topMargin=2.0 * cm, bottomMargin=1.8 * cm,
        title=doc.titulo, author="Pedro Vargas dos Santos e Silva",
    )

    def rodape(canvas, documento) -> None:
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(CINZA)
        canvas.drawString(margem_esq, 1.1 * cm, doc.rodape)
        canvas.drawRightString(A4[0] - margem_dir, 1.1 * cm, f"Página {documento.page}")
        canvas.restoreState()

    template.build(story, onFirstPage=rodape, onLaterPages=rodape)
    print(f"gerado: {doc.destino} ({destino.stat().st_size // 1024} KB)")


DOCUMENTOS = (
    Documento(
        origem=Path("specs/task_analyzer_spec.md"),
        destino=Path("specs/system_design_document.pdf"),
        titulo="System Design Document — TaskAnalyzer",
        subtitulo="Especificação técnica executável (SDD) — versão 1.1.0",
        rodape="SDD TaskAnalyzer v1.1.0 — Bootcamp III — Pedro Vargas dos Santos e Silva",
        pular_ate_h1=True,
    ),
    Documento(
        origem=Path("docs/relatorio_governanca_etica.md"),
        destino=Path("docs/relatorio_governanca_etica.pdf"),
        titulo="Relatório de Governança e Ética de IA",
        subtitulo="TaskAnalyzer — Fase 3 — Bootcamp III",
        rodape="Governança e Ética de IA — TaskAnalyzer — Pedro Vargas dos Santos e Silva",
        pular_ate_h1=True,
    ),
)


def main() -> int:
    """Gera todos os PDFs configurados."""
    for documento in DOCUMENTOS:
        gerar(documento)
    return 0


if __name__ == "__main__":
    sys.exit(main())
