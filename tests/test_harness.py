"""Test Harness do TaskAnalyzer.

Cada teste traduz um cenário de aceite da seção 2 de specs/task_analyzer_spec.md (v1.1.0).
Nomes rastreáveis: test_caXX_* (sucesso/borda) e test_ceXX_* (exceção/erro).
Execução a partir da raiz: python -m pytest -v --cov=src --cov-report=term-missing
"""

import copy
import logging
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from src.task_analyzer import (
    DataInvalidaError,
    EntradaInvalidaError,
    Prioridade,
    Status,
    Tarefa,
    TarefaInvalidaError,
    TaskValidationError,
    analyze_tasks,
    calcular_tempo_conclusao_horas,
    esta_atrasada,
)

BRASILIA = timezone(timedelta(hours=-3))


def utc(dia: int, hora: int, minuto: int = 0) -> datetime:
    """Cria uma data de março de 2026 em UTC."""
    return datetime(2026, 3, dia, hora, minuto, tzinfo=timezone.utc)


def nova_tarefa(
    id_tarefa: int,
    prioridade: Prioridade,
    status: Status,
    prazo: datetime,
    inicio: datetime | None = None,
    conclusao: datetime | None = None,
) -> Tarefa:
    """Cria uma tarefa com data_criacao padrão (01/03/2026 08:00 UTC)."""
    return Tarefa(
        id_tarefa=id_tarefa,
        titulo=f"Tarefa de teste {id_tarefa}",
        prioridade=prioridade,
        status=status,
        data_criacao=utc(1, 8),
        prazo=prazo,
        data_inicio=inicio,
        data_conclusao=conclusao,
    )


@pytest.fixture
def tarefas_cenario_base() -> list[Tarefa]:
    """Conjunto base da seção 2.2: 4 concluídas, 1 pendente, 1 cancelada."""
    return [
        nova_tarefa(1, Prioridade.ALTA, Status.CONCLUIDA, utc(2, 12), utc(2, 9), utc(2, 11)),
        nova_tarefa(2, Prioridade.ALTA, Status.CONCLUIDA, utc(2, 16), utc(2, 13), utc(2, 17)),
        nova_tarefa(3, Prioridade.MEDIA, Status.CONCLUIDA, utc(3, 12), utc(3, 9), utc(3, 10, 30)),
        nova_tarefa(4, Prioridade.MEDIA, Status.PENDENTE, utc(5, 18)),
        nova_tarefa(
            5, Prioridade.BAIXA, Status.CONCLUIDA, utc(4, 8, 45), utc(4, 8), utc(4, 8, 45)
        ),
        nova_tarefa(6, Prioridade.BAIXA, Status.CANCELADA, utc(6, 18)),
    ]


@pytest.fixture
def tarefa_valida() -> Tarefa:
    """Tarefa 5 concluída, válida, usada como base para variações inválidas."""
    return nova_tarefa(5, Prioridade.ALTA, Status.CONCLUIDA, utc(2, 12), utc(2, 9), utc(2, 10))


# ---------------------------------------------------------------------------
# Cenário 1 (Sucesso) e casos de borda
# ---------------------------------------------------------------------------


def test_ca01_metricas_gerais_corretas(tarefas_cenario_base: list[Tarefa]) -> None:
    relatorio = analyze_tasks(tarefas_cenario_base)

    assert relatorio.total_tarefas == 6
    assert relatorio.total_concluidas == 4
    assert relatorio.total_pendentes == 1
    assert relatorio.total_canceladas == 1
    assert relatorio.total_atrasadas == 1
    assert relatorio.tempo_medio_conclusao_horas == 2.06
    assert relatorio.taxa_atraso_percentual == 25.0


def test_ca02_indicadores_por_prioridade_corretos(tarefas_cenario_base: list[Tarefa]) -> None:
    indicadores = analyze_tasks(tarefas_cenario_base).indicadores_por_prioridade

    alta, media, baixa = indicadores["alta"], indicadores["media"], indicadores["baixa"]
    assert (alta.total_tarefas, alta.total_concluidas, alta.total_atrasadas) == (2, 2, 1)
    assert alta.tempo_medio_conclusao_horas == 3.0
    assert alta.taxa_atraso_percentual == 50.0
    assert (media.total_tarefas, media.total_concluidas, media.total_atrasadas) == (2, 1, 0)
    assert media.tempo_medio_conclusao_horas == 1.5
    assert media.taxa_atraso_percentual == 0.0
    assert (baixa.total_tarefas, baixa.total_concluidas, baixa.total_atrasadas) == (2, 1, 0)
    assert baixa.tempo_medio_conclusao_horas == 0.75
    assert baixa.taxa_atraso_percentual == 0.0


def test_ca03_conclusao_exatamente_no_prazo_nao_e_atraso() -> None:
    tarefa = nova_tarefa(1, Prioridade.ALTA, Status.CONCLUIDA, utc(2, 10), utc(2, 9), utc(2, 10))

    relatorio = analyze_tasks([tarefa])

    assert relatorio.total_atrasadas == 0
    assert relatorio.taxa_atraso_percentual == 0.0
    assert relatorio.tempo_medio_conclusao_horas == 1.0


def test_ca04_arredondamento_apenas_no_resultado_final() -> None:
    tarefas = [
        nova_tarefa(1, Prioridade.ALTA, Status.CONCLUIDA, utc(2, 12), utc(2, 9), utc(2, 10)),
        nova_tarefa(2, Prioridade.ALTA, Status.CONCLUIDA, utc(2, 12), utc(2, 9), utc(2, 10)),
        nova_tarefa(3, Prioridade.ALTA, Status.CONCLUIDA, utc(2, 10), utc(2, 9), utc(2, 11)),
    ]

    relatorio = analyze_tasks(tarefas)

    assert relatorio.tempo_medio_conclusao_horas == 1.33
    assert relatorio.taxa_atraso_percentual == 33.33


def test_ca05_prioridade_sem_concluidas_retorna_zero() -> None:
    tarefas = [
        nova_tarefa(1, Prioridade.ALTA, Status.CONCLUIDA, utc(2, 12), utc(2, 9), utc(2, 10)),
        nova_tarefa(2, Prioridade.MEDIA, Status.PENDENTE, utc(5, 18)),
    ]

    indicadores = analyze_tasks(tarefas).indicadores_por_prioridade

    assert set(indicadores) == {"baixa", "media", "alta"}
    media, baixa = indicadores["media"], indicadores["baixa"]
    assert (media.total_tarefas, media.total_concluidas) == (1, 0)
    assert media.tempo_medio_conclusao_horas == 0.0
    assert media.taxa_atraso_percentual == 0.0
    assert (baixa.total_tarefas, baixa.total_concluidas, baixa.total_atrasadas) == (0, 0, 0)
    assert baixa.tempo_medio_conclusao_horas == 0.0
    assert baixa.taxa_atraso_percentual == 0.0


def test_ca06_pendente_vencida_nao_entra_no_atraso(tarefas_cenario_base: list[Tarefa]) -> None:
    vencida = nova_tarefa(8, Prioridade.MEDIA, Status.PENDENTE, utc(1, 12))

    relatorio = analyze_tasks([*tarefas_cenario_base, vencida])

    assert relatorio.total_tarefas == 7
    assert relatorio.total_pendentes == 2
    assert relatorio.tempo_medio_conclusao_horas == 2.06
    assert relatorio.taxa_atraso_percentual == 25.0


def test_ca07_funcao_pura_e_independente_da_ordem(tarefas_cenario_base: list[Tarefa]) -> None:
    copia = copy.deepcopy(tarefas_cenario_base)

    relatorio_original = analyze_tasks(tarefas_cenario_base)
    relatorio_invertido = analyze_tasks(list(reversed(tarefas_cenario_base)))

    assert tarefas_cenario_base == copia
    assert relatorio_original == relatorio_invertido


def test_ca08_datas_normalizadas_para_utc() -> None:
    tarefa = Tarefa(
        id_tarefa=1,
        titulo="Tarefa com fusos diferentes",
        prioridade=Prioridade.ALTA,
        status=Status.CONCLUIDA,
        data_criacao=utc(1, 8),
        prazo=datetime(2026, 3, 2, 9, 30, tzinfo=BRASILIA),
        data_inicio=datetime(2026, 3, 2, 6, 0, tzinfo=BRASILIA),
        data_conclusao=utc(2, 10),
    )

    relatorio = analyze_tasks([tarefa])

    assert relatorio.tempo_medio_conclusao_horas == 1.0
    assert relatorio.taxa_atraso_percentual == 0.0


def test_ca09_lista_vazia_retorna_zeros() -> None:
    relatorio = analyze_tasks([])

    assert relatorio.total_tarefas == 0
    assert relatorio.total_concluidas == 0
    assert relatorio.total_pendentes == 0
    assert relatorio.total_canceladas == 0
    assert relatorio.total_atrasadas == 0
    assert relatorio.tempo_medio_conclusao_horas == 0.0
    assert relatorio.taxa_atraso_percentual == 0.0
    for metricas in relatorio.indicadores_por_prioridade.values():
        assert metricas.total_tarefas == 0
        assert metricas.tempo_medio_conclusao_horas == 0.0
        assert metricas.taxa_atraso_percentual == 0.0


def test_ca10_somente_pendentes_e_canceladas_retorna_zero_sem_excecao() -> None:
    tarefas = [
        nova_tarefa(4, Prioridade.MEDIA, Status.PENDENTE, utc(5, 18)),
        nova_tarefa(6, Prioridade.BAIXA, Status.CANCELADA, utc(6, 18)),
    ]

    relatorio = analyze_tasks(tarefas)

    assert relatorio.total_tarefas == 2
    assert relatorio.total_concluidas == 0
    assert relatorio.total_pendentes == 1
    assert relatorio.total_canceladas == 1
    assert relatorio.tempo_medio_conclusao_horas == 0.0
    assert relatorio.taxa_atraso_percentual == 0.0


def test_ca11_logs_nao_registram_titulo(
    tarefa_valida: Tarefa, caplog: pytest.LogCaptureFixture
) -> None:
    sigilosa = replace(tarefa_valida, titulo="DADO-SIGILOSO-123")
    invalida = replace(sigilosa, id_tarefa=9, prioridade="urgente")

    with caplog.at_level(logging.DEBUG, logger="src.task_analyzer"):
        analyze_tasks([sigilosa])
        with pytest.raises(TaskValidationError):
            analyze_tasks([invalida])

    assert caplog.records
    assert "DADO-SIGILOSO-123" not in caplog.text


# ---------------------------------------------------------------------------
# Cenário 2 (Exceção/Erro)
# ---------------------------------------------------------------------------


def test_ce01_conclusao_anterior_a_criacao(
    tarefas_cenario_base: list[Tarefa], tarefa_valida: Tarefa
) -> None:
    invalida = replace(tarefa_valida, id_tarefa=7, data_criacao=utc(2, 12))

    with pytest.raises(TaskValidationError, match="Tarefa 7: data_conclusao anterior") as erro:
        analyze_tasks([*tarefas_cenario_base, invalida])

    assert isinstance(erro.value, DataInvalidaError)


def test_ce02_conclusao_anterior_ao_inicio(tarefa_valida: Tarefa) -> None:
    invalida = replace(tarefa_valida, id_tarefa=7, data_inicio=utc(2, 9), data_conclusao=utc(2, 8))

    with pytest.raises(DataInvalidaError, match="Tarefa 7: data_conclusao anterior a data_inicio"):
        analyze_tasks([invalida])


@pytest.mark.parametrize(
    "entrada", [None, {}, "tarefas", ()], ids=["none", "dict", "str", "tuple"]
)
def test_ce03_entrada_que_nao_e_lista(entrada: object) -> None:
    with pytest.raises(EntradaInvalidaError):
        analyze_tasks(entrada)  # type: ignore[arg-type]


def test_ce04_elemento_que_nao_e_tarefa(tarefa_valida: Tarefa) -> None:
    with pytest.raises(EntradaInvalidaError, match="posição 1"):
        analyze_tasks([tarefa_valida, "não sou uma tarefa"])  # type: ignore[list-item]


@pytest.mark.parametrize(
    ("alteracoes", "erro_esperado"),
    [
        pytest.param({"prioridade": "urgente"}, TarefaInvalidaError, id="ce05-prioridade"),
        pytest.param({"status": "feito"}, TarefaInvalidaError, id="ce06-status"),
        pytest.param(
            {"data_inicio": datetime(2026, 3, 2, 9)}, DataInvalidaError, id="ce07-data-naive"
        ),
        pytest.param({"data_conclusao": None}, TarefaInvalidaError, id="ce08-sem-conclusao"),
        pytest.param({"data_inicio": None}, TarefaInvalidaError, id="ce08-sem-inicio"),
        pytest.param({"status": Status.PENDENTE}, TarefaInvalidaError, id="ce09-pendente"),
        pytest.param({"status": Status.CANCELADA}, TarefaInvalidaError, id="ce09-cancelada"),
        pytest.param({"data_inicio": utc(1, 7)}, DataInvalidaError, id="ce12-inicio"),
        pytest.param({"prazo": utc(1, 7)}, DataInvalidaError, id="ce13-prazo"),
        pytest.param({"titulo": "   "}, TarefaInvalidaError, id="ce14-titulo"),
        pytest.param({"data_criacao": "2026-03-01"}, DataInvalidaError, id="ce15-tipo-data"),
        pytest.param({"prazo": None}, DataInvalidaError, id="ce15-prazo-ausente"),
    ],
)
def test_ce05_a_ce15_tarefa_invalida(
    tarefa_valida: Tarefa, alteracoes: dict[str, object], erro_esperado: type[Exception]
) -> None:
    invalida = replace(tarefa_valida, **alteracoes)

    with pytest.raises(erro_esperado, match="Tarefa 5"):
        analyze_tasks([invalida])


def test_ce10_id_tarefa_duplicado(tarefa_valida: Tarefa) -> None:
    primeira = replace(tarefa_valida, id_tarefa=3)
    segunda = replace(tarefa_valida, id_tarefa=3, titulo="Outra tarefa")

    with pytest.raises(EntradaInvalidaError, match="id_tarefa duplicado: 3"):
        analyze_tasks([primeira, segunda])


@pytest.mark.parametrize(
    "id_invalido", [0, -1, True, "1"], ids=["zero", "negativo", "bool", "str"]
)
def test_ce11_id_tarefa_invalido(tarefa_valida: Tarefa, id_invalido: object) -> None:
    with pytest.raises(TarefaInvalidaError, match="id_tarefa deve ser um inteiro"):
        analyze_tasks([replace(tarefa_valida, id_tarefa=id_invalido)])


@pytest.mark.parametrize("funcao", [calcular_tempo_conclusao_horas, esta_atrasada])
def test_ce16_funcoes_auxiliares_exigem_tarefa_concluida(funcao: object) -> None:
    pendente = nova_tarefa(5, Prioridade.MEDIA, Status.PENDENTE, utc(5, 18))

    with pytest.raises(TarefaInvalidaError, match="Tarefa 5"):
        funcao(pendente)  # type: ignore[operator]
