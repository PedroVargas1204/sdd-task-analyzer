"""TaskAnalyzer: métricas de produtividade a partir de uma lista de tarefas.

Implementa o contrato definido em specs/task_analyzer_spec.md (versão 1.1.0).
O módulo é puro: não faz I/O, não mantém estado mutável e não modifica a entrada.
Todos os erros pertencem à hierarquia TaskValidationError.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import NoReturn

logger = logging.getLogger(__name__)

SEGUNDOS_POR_HORA = 3600
CASAS_DECIMAIS = 2
FATOR_PERCENTUAL = 100
VALOR_SEM_CONCLUIDAS = 0.0
CAMPOS_DATA_OBRIGATORIOS = ("data_criacao", "prazo")
CAMPOS_DATA_OPCIONAIS = ("data_inicio", "data_conclusao")


class Prioridade(StrEnum):
    """Domínio fechado de prioridades de uma tarefa (RN12)."""

    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"


class Status(StrEnum):
    """Domínio fechado de status de uma tarefa (RN12)."""

    CONCLUIDA = "concluida"
    PENDENTE = "pendente"
    CANCELADA = "cancelada"


@dataclass(frozen=True)
class Tarefa:
    """Tarefa de entrada do analisador (seção 1.3.1 da especificação).

    Attributes:
        id_tarefa: Identificador inteiro positivo e único na lista.
        titulo: Descrição curta, não vazia. Nunca é registrada em logs.
        prioridade: Prioridade da tarefa.
        status: Situação atual da tarefa.
        data_criacao: Momento de criação (timezone-aware).
        prazo: Data/hora limite (timezone-aware).
        data_inicio: Início da execução; obrigatório se concluída.
        data_conclusao: Fim da execução; obrigatório se concluída, None caso contrário.
    """

    id_tarefa: int
    titulo: str
    prioridade: Prioridade
    status: Status
    data_criacao: datetime
    prazo: datetime
    data_inicio: datetime | None = None
    data_conclusao: datetime | None = None


@dataclass(frozen=True)
class MetricasPrioridade:
    """Indicadores de um grupo de tarefas de mesma prioridade.

    Attributes:
        total_tarefas: Total de tarefas do grupo (todos os status).
        total_concluidas: Tarefas concluídas do grupo.
        total_atrasadas: Tarefas concluídas após o prazo.
        tempo_medio_conclusao_horas: Média em horas (2 casas) ou 0.0 sem concluídas.
        taxa_atraso_percentual: Percentual de atraso (2 casas) ou 0.0 sem concluídas.
    """

    total_tarefas: int
    total_concluidas: int
    total_atrasadas: int
    tempo_medio_conclusao_horas: float
    taxa_atraso_percentual: float


@dataclass(frozen=True)
class RelatorioMetricas:
    """Relatório completo retornado por analyze_tasks (seção 1.3.2 da especificação).

    Attributes:
        total_tarefas: Total de tarefas recebidas.
        total_concluidas: Total de tarefas concluídas.
        total_pendentes: Total de tarefas pendentes.
        total_canceladas: Total de tarefas canceladas.
        total_atrasadas: Total de tarefas concluídas após o prazo.
        tempo_medio_conclusao_horas: Tempo médio geral em horas (2 casas).
        taxa_atraso_percentual: Percentual geral de concluídas em atraso (2 casas).
        indicadores_por_prioridade: Métricas por prioridade; chaves baixa, media e alta.
    """

    total_tarefas: int
    total_concluidas: int
    total_pendentes: int
    total_canceladas: int
    total_atrasadas: int
    tempo_medio_conclusao_horas: float
    taxa_atraso_percentual: float
    indicadores_por_prioridade: dict[str, MetricasPrioridade]


class TaskValidationError(Exception):
    """Classe-base de todos os erros do TaskAnalyzer."""


class EntradaInvalidaError(TaskValidationError):
    """Entrada que não é lista, contém elementos que não são Tarefa ou IDs duplicados."""


class TarefaInvalidaError(TaskValidationError):
    """Tarefa com identificação, domínio ou coerência status x datas inválidos."""


class DataInvalidaError(TaskValidationError):
    """Data com tipo errado, sem fuso horário ou em ordem cronológica inválida."""


def analyze_tasks(tarefas: list[Tarefa]) -> RelatorioMetricas:
    """Valida a lista de tarefas e calcula o relatório de métricas.

    Args:
        tarefas: Lista de tarefas a analisar. Pode ser vazia.

    Returns:
        Relatório com contagens, tempo médio em horas e taxa de atraso.

    Raises:
        EntradaInvalidaError: Se a entrada não for lista de Tarefa ou houver ID duplicado.
        TarefaInvalidaError: Se alguma tarefa violar RN09, RN12 ou RN13.
        DataInvalidaError: Se alguma data violar RN07 ou RN08.
    """
    logger.info("Iniciando análise de tarefas.")
    _validar_estrutura(tarefas)
    for tarefa in tarefas:
        validar_tarefa(tarefa)
    _validar_ids_unicos(tarefas)
    relatorio = _montar_relatorio(tarefas)
    logger.info(
        "Análise concluída: %d tarefa(s), %d concluída(s), %d atrasada(s).",
        relatorio.total_tarefas,
        relatorio.total_concluidas,
        relatorio.total_atrasadas,
    )
    return relatorio


def validar_tarefa(tarefa: Tarefa) -> None:
    """Valida uma tarefa isolada na ordem definida pela especificação.

    Args:
        tarefa: Tarefa a validar.

    Raises:
        TarefaInvalidaError: Se id, título, domínio ou status x datas forem inválidos.
        DataInvalidaError: Se alguma data tiver tipo errado, não tiver fuso ou for incoerente.
    """
    _validar_id(tarefa.id_tarefa)
    _validar_titulo(tarefa)
    _validar_dominio(tarefa, "prioridade", Prioridade)
    _validar_dominio(tarefa, "status", Status)
    _validar_tipos_datas(tarefa)
    _validar_status_datas(tarefa)
    _validar_cronologia(tarefa)
    logger.debug("Tarefa %s validada.", tarefa.id_tarefa)


def calcular_tempo_conclusao_horas(tarefa: Tarefa) -> float:
    """Calcula o tempo corrido de conclusão da tarefa, em horas, sem arredondamento (RN02).

    Args:
        tarefa: Tarefa concluída e válida.

    Returns:
        Diferença entre data_conclusao e data_inicio, em horas.

    Raises:
        TarefaInvalidaError: Se a tarefa não estiver concluída.
    """
    inicio, conclusao = _exigir_concluida(tarefa)
    return (conclusao - inicio).total_seconds() / SEGUNDOS_POR_HORA


def esta_atrasada(tarefa: Tarefa) -> bool:
    """Indica se a tarefa foi concluída após o prazo (RN03).

    Args:
        tarefa: Tarefa concluída e válida.

    Returns:
        True se data_conclusao for posterior ao prazo; False caso contrário.

    Raises:
        TarefaInvalidaError: Se a tarefa não estiver concluída.
    """
    _, conclusao = _exigir_concluida(tarefa)
    return conclusao > _em_utc(tarefa.prazo)


def _falhar(tipo_erro: type[TaskValidationError], mensagem: str) -> NoReturn:
    """Registra o erro em log e lança a exceção correspondente.

    Args:
        tipo_erro: Classe da exceção a lançar.
        mensagem: Mensagem do erro (sem dados pessoais).

    Raises:
        TaskValidationError: Sempre, do tipo informado.
    """
    logger.error(mensagem)
    raise tipo_erro(mensagem)


def _em_utc(data: datetime) -> datetime:
    """Normaliza uma data timezone-aware para UTC (RN07).

    Args:
        data: Data timezone-aware.

    Returns:
        A mesma data expressa em UTC.
    """
    return data.astimezone(timezone.utc)


def _validar_estrutura(tarefas: object) -> None:
    """Valida que a entrada é uma lista cujos elementos são todos Tarefa (RN14).

    Args:
        tarefas: Entrada recebida por analyze_tasks.

    Raises:
        EntradaInvalidaError: Se a entrada não for lista ou tiver elemento que não é Tarefa.
    """
    if not isinstance(tarefas, list):
        _falhar(
            EntradaInvalidaError,
            f"A entrada deve ser uma lista de tarefas, recebido {type(tarefas).__name__}.",
        )
    for posicao, elemento in enumerate(tarefas):
        if not isinstance(elemento, Tarefa):
            _falhar(EntradaInvalidaError, f"Elemento na posição {posicao} não é uma Tarefa.")


def _validar_ids_unicos(tarefas: list[Tarefa]) -> None:
    """Garante que não há id_tarefa repetido na lista (RN13).

    Args:
        tarefas: Lista de tarefas já validadas individualmente.

    Raises:
        EntradaInvalidaError: Se algum id_tarefa aparecer mais de uma vez.
    """
    ids_vistos: set[int] = set()
    for tarefa in tarefas:
        if tarefa.id_tarefa in ids_vistos:
            _falhar(EntradaInvalidaError, f"id_tarefa duplicado: {tarefa.id_tarefa}.")
        ids_vistos.add(tarefa.id_tarefa)


def _validar_id(id_tarefa: object) -> None:
    """Valida que o id é inteiro maior que zero e não é bool (RN13).

    Args:
        id_tarefa: Valor do campo id_tarefa.

    Raises:
        TarefaInvalidaError: Se o id for inválido.
    """
    if isinstance(id_tarefa, bool) or not isinstance(id_tarefa, int) or id_tarefa <= 0:
        _falhar(
            TarefaInvalidaError,
            f"Tarefa {id_tarefa!r}: id_tarefa deve ser um inteiro maior que zero.",
        )


def _validar_titulo(tarefa: Tarefa) -> None:
    """Valida que o título é texto não vazio (RN13). O conteúdo nunca é registrado.

    Args:
        tarefa: Tarefa a validar.

    Raises:
        TarefaInvalidaError: Se o título estiver vazio ou não for texto.
    """
    if not isinstance(tarefa.titulo, str) or not tarefa.titulo.strip():
        _falhar(TarefaInvalidaError, f"Tarefa {tarefa.id_tarefa}: titulo não pode ser vazio.")


def _validar_dominio(tarefa: Tarefa, campo: str, dominio: type[StrEnum]) -> None:
    """Valida que o campo pertence ao domínio fechado informado (RN12).

    Args:
        tarefa: Tarefa a validar.
        campo: Nome do campo ("prioridade" ou "status").
        dominio: Enumeração com os valores aceitos.

    Raises:
        TarefaInvalidaError: Se o valor não pertencer ao domínio.
    """
    valor = getattr(tarefa, campo)
    valores_aceitos = {membro.value for membro in dominio}
    if not isinstance(valor, str) or valor not in valores_aceitos:
        _falhar(
            TarefaInvalidaError,
            f"Tarefa {tarefa.id_tarefa}: valor inválido para {campo}: {valor!r}.",
        )


def _validar_tipos_datas(tarefa: Tarefa) -> None:
    """Valida tipo datetime e presença de fuso horário em todas as datas (RN07).

    Args:
        tarefa: Tarefa a validar.

    Raises:
        DataInvalidaError: Se alguma data não for datetime ou for naive.
    """
    for campo in CAMPOS_DATA_OBRIGATORIOS + CAMPOS_DATA_OPCIONAIS:
        valor = getattr(tarefa, campo)
        if valor is None and campo in CAMPOS_DATA_OPCIONAIS:
            continue
        if not isinstance(valor, datetime):
            _falhar(DataInvalidaError, f"Tarefa {tarefa.id_tarefa}: {campo} deve ser datetime.")
        if valor.tzinfo is None or valor.utcoffset() is None:
            _falhar(
                DataInvalidaError,
                f"Tarefa {tarefa.id_tarefa}: {campo} sem fuso horário (timezone-aware).",
            )


def _validar_status_datas(tarefa: Tarefa) -> None:
    """Valida a coerência entre status e datas de execução (RN09).

    Args:
        tarefa: Tarefa a validar.

    Raises:
        TarefaInvalidaError: Se a combinação de status e datas for incoerente.
    """
    if tarefa.status == Status.CONCLUIDA:
        if tarefa.data_inicio is None or tarefa.data_conclusao is None:
            _falhar(
                TarefaInvalidaError,
                f"Tarefa {tarefa.id_tarefa}: tarefa concluida exige data_inicio e "
                "data_conclusao.",
            )
    elif tarefa.data_conclusao is not None:
        _falhar(
            TarefaInvalidaError,
            f"Tarefa {tarefa.id_tarefa}: tarefa {tarefa.status} não pode ter data_conclusao.",
        )


def _validar_cronologia(tarefa: Tarefa) -> None:
    """Valida a ordem cronológica das datas, já normalizadas para UTC (RN08).

    Args:
        tarefa: Tarefa com datas de tipo e fuso já validados.

    Raises:
        DataInvalidaError: Se a ordem cronológica for violada.
    """
    prefixo = f"Tarefa {tarefa.id_tarefa}:"
    criacao = _em_utc(tarefa.data_criacao)
    inicio = _em_utc(tarefa.data_inicio) if tarefa.data_inicio is not None else None
    conclusao = _em_utc(tarefa.data_conclusao) if tarefa.data_conclusao is not None else None
    if _em_utc(tarefa.prazo) < criacao:
        _falhar(DataInvalidaError, f"{prefixo} prazo anterior a data_criacao.")
    if conclusao is not None and conclusao < criacao:
        _falhar(DataInvalidaError, f"{prefixo} data_conclusao anterior a data_criacao.")
    if inicio is not None and inicio < criacao:
        _falhar(DataInvalidaError, f"{prefixo} data_inicio anterior a data_criacao.")
    if inicio is not None and conclusao is not None and conclusao < inicio:
        _falhar(DataInvalidaError, f"{prefixo} data_conclusao anterior a data_inicio.")


def _exigir_concluida(tarefa: Tarefa) -> tuple[datetime, datetime]:
    """Garante a pré-condição de tarefa concluída e devolve suas datas em UTC.

    Args:
        tarefa: Tarefa a verificar.

    Returns:
        Tupla (data_inicio, data_conclusao) normalizadas para UTC.

    Raises:
        TarefaInvalidaError: Se a tarefa não estiver concluída ou faltar alguma data.
    """
    inicio, conclusao = tarefa.data_inicio, tarefa.data_conclusao
    if tarefa.status != Status.CONCLUIDA or inicio is None or conclusao is None:
        _falhar(
            TarefaInvalidaError,
            f"Tarefa {tarefa.id_tarefa}: operação exige tarefa concluida.",
        )
    return _em_utc(inicio), _em_utc(conclusao)


def _montar_relatorio(tarefas: list[Tarefa]) -> RelatorioMetricas:
    """Calcula as métricas gerais e por prioridade de uma lista já validada.

    Args:
        tarefas: Lista de tarefas válidas (pode ser vazia).

    Returns:
        Relatório de métricas completo.
    """
    geral = _calcular_metricas(tarefas)
    if geral.total_concluidas == 0:
        logger.info("Nenhuma tarefa concluída: tempo médio e taxa de atraso retornam 0.0.")
    grupos = _agrupar_por_prioridade(tarefas)
    return RelatorioMetricas(
        total_tarefas=geral.total_tarefas,
        total_concluidas=geral.total_concluidas,
        total_pendentes=_contar_status(tarefas, Status.PENDENTE),
        total_canceladas=_contar_status(tarefas, Status.CANCELADA),
        total_atrasadas=geral.total_atrasadas,
        tempo_medio_conclusao_horas=geral.tempo_medio_conclusao_horas,
        taxa_atraso_percentual=geral.taxa_atraso_percentual,
        indicadores_por_prioridade={
            prioridade: _calcular_metricas(grupo) for prioridade, grupo in grupos.items()
        },
    )


def _calcular_metricas(tarefas: list[Tarefa]) -> MetricasPrioridade:
    """Calcula contagens, tempo médio e taxa de atraso de um grupo (RN01 a RN06, RN10).

    Args:
        tarefas: Grupo de tarefas válidas.

    Returns:
        Métricas do grupo; tempo e taxa valem 0.0 se não houver concluídas.
    """
    concluidas = [tarefa for tarefa in tarefas if tarefa.status == Status.CONCLUIDA]
    total_atrasadas = sum(1 for tarefa in concluidas if esta_atrasada(tarefa))
    soma_horas = sum(calcular_tempo_conclusao_horas(tarefa) for tarefa in concluidas)
    return MetricasPrioridade(
        total_tarefas=len(tarefas),
        total_concluidas=len(concluidas),
        total_atrasadas=total_atrasadas,
        tempo_medio_conclusao_horas=_media(soma_horas, len(concluidas)),
        taxa_atraso_percentual=_percentual(total_atrasadas, len(concluidas)),
    )


def _agrupar_por_prioridade(tarefas: list[Tarefa]) -> dict[str, list[Tarefa]]:
    """Agrupa as tarefas por prioridade, garantindo as três chaves (RN11).

    Args:
        tarefas: Lista de tarefas válidas.

    Returns:
        Dicionário com as chaves baixa, media e alta.
    """
    grupos: dict[str, list[Tarefa]] = {prioridade.value: [] for prioridade in Prioridade}
    for tarefa in tarefas:
        grupos[Prioridade(tarefa.prioridade).value].append(tarefa)
    return grupos


def _contar_status(tarefas: list[Tarefa], status: Status) -> int:
    """Conta as tarefas de um status específico.

    Args:
        tarefas: Lista de tarefas válidas.
        status: Status a contar.

    Returns:
        Quantidade de tarefas com o status informado.
    """
    return sum(1 for tarefa in tarefas if tarefa.status == status)


def _media(soma: float, quantidade: int) -> float:
    """Calcula a média arredondada, evitando divisão por zero (RN04, RN06, RN10).

    Args:
        soma: Soma dos valores.
        quantidade: Quantidade de valores.

    Returns:
        Média com 2 casas decimais, ou 0.0 se quantidade for zero.
    """
    if quantidade == 0:
        return VALOR_SEM_CONCLUIDAS
    return round(soma / quantidade, CASAS_DECIMAIS)


def _percentual(parte: int, total: int) -> float:
    """Calcula o percentual arredondado, evitando divisão por zero (RN05, RN06, RN10).

    Args:
        parte: Quantidade de itens que atendem ao critério.
        total: Quantidade total de itens.

    Returns:
        Percentual com 2 casas decimais, ou 0.0 se total for zero.
    """
    if total == 0:
        return VALOR_SEM_CONCLUIDAS
    return round(parte / total * FATOR_PERCENTUAL, CASAS_DECIMAIS)
