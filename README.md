# sdd-task-analyzer

Módulo **TaskAnalyzer** desenvolvido com **Spec-Driven Development (SDD)** e assistência de IA
no Bootcamp III. O código em `src/` foi gerado por um assistente de IA a partir da
especificação e das regras de contexto, e homologado por revisão humana e pelo Test Harness.

> **Status do build:** testes executados localmente — 100% aprovados, cobertura de 100% em
> `src/`. A integração contínua (GitHub Actions) será adicionada na Fase 3.

## O que o módulo faz

A partir de uma lista de tarefas, `analyze_tasks` calcula:

- totais de tarefas (geral, concluídas, pendentes, canceladas e atrasadas);
- **tempo médio de conclusão em horas**, geral e por prioridade (baixa, média, alta);
- **taxa de atraso percentual**, geral e por prioridade.

Entradas inválidas geram exceções da hierarquia `TaskValidationError`. Listas vazias ou sem
tarefas concluídas retornam 0.0 nas médias, sem divisão por zero.

## Estrutura

```
sdd-task-analyzer/
├── README.md
├── CONTEXT_RULES.md           # Regras persistentes para a IA
├── .gitignore
├── requirements.txt           # pytest e pytest-cov
├── specs/
│   └── task_analyzer_spec.md  # Contrato SDD (fonte da verdade)
├── tests/
│   └── test_harness.py        # 27 cenários de aceite (pytest)
└── src/
    └── task_analyzer.py       # Implementação gerada via IA e homologada
```

## Como executar

Requisito: **Python 3.11 ou superior**.

```bash
git clone https://github.com/<seu-usuario>/sdd-task-analyzer.git
cd sdd-task-analyzer
python -m venv .venv
# Windows: .venv\Scripts\activate    |    Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -v --cov=src --cov-report=term-missing
```

## Exemplo de uso

```python
from datetime import datetime, timezone
from src.task_analyzer import Prioridade, Status, Tarefa, analyze_tasks

utc = timezone.utc
tarefa = Tarefa(
    id_tarefa=1,
    titulo="Revisar relatório",
    prioridade=Prioridade.ALTA,
    status=Status.CONCLUIDA,
    data_criacao=datetime(2026, 3, 1, 8, tzinfo=utc),
    prazo=datetime(2026, 3, 2, 12, tzinfo=utc),
    data_inicio=datetime(2026, 3, 2, 9, tzinfo=utc),
    data_conclusao=datetime(2026, 3, 2, 11, tzinfo=utc),
)
relatorio = analyze_tasks([tarefa])
print(relatorio.tempo_medio_conclusao_horas)  # 2.0
```

## Governança

- **Contrato:** [`specs/task_analyzer_spec.md`](specs/task_analyzer_spec.md) (v1.1.0, com
  histórico das mudanças em relação à Fase 1).
- **Regras para a IA:** [`CONTEXT_RULES.md`](CONTEXT_RULES.md).
- **Fluxo:** branches `feature/*`, Conventional Commits e Pull Requests com checklist de
  homologação humana antes do merge na `main`.

## Autor

Pedro Vargas dos Santos e Silva — Ciência de Dados e Machine Learning (CEUB).
