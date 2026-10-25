# sdd-task-analyzer

[![CI](https://github.com/PedroVargas1204/sdd-task-analyzer/actions/workflows/ci.yml/badge.svg)](https://github.com/PedroVargas1204/sdd-task-analyzer/actions/workflows/ci.yml)

Módulo **TaskAnalyzer**, desenvolvido com **Spec-Driven Development (SDD)** e assistência
de IA no Bootcamp III. O código em `src/` foi gerado por um assistente de IA a partir da
especificação e das regras de contexto, e homologado por revisão humana e pelo Test
Harness. A partir da Fase 3 o projeto conta com integração contínua no GitHub Actions e
execução containerizada com Docker.

## O que o módulo faz

A partir de uma lista de tarefas, `analyze_tasks` calcula:

- totais de tarefas (geral, concluídas, pendentes, canceladas e atrasadas);
- **tempo médio de conclusão em horas**, geral e por prioridade (baixa, média, alta);
- **taxa de atraso percentual**, geral e por prioridade.

Entradas inválidas geram exceções da hierarquia `TaskValidationError`. Listas vazias ou
sem tarefas concluídas retornam `0.0` nas médias, sem divisão por zero.

## Estrutura

```
sdd-task-analyzer/
├── .github/workflows/ci.yml          # Pipeline de integração contínua
├── Dockerfile                        # Imagem de execução (python:3.11-slim)
├── docker-compose.yml                # Orquestração da suíte de testes
├── .dockerignore                     # Contexto de build enxuto
├── .gitignore
├── README.md
├── CONTEXT_RULES.md                  # Regras persistentes para a IA
├── requirements.txt                  # pytest e pytest-cov (versões fixadas)
├── pytest.ini                        # sys.path da raiz p/ o comando oficial
├── docs/
│   ├── relatorio_governanca_etica.md   # Fonte do relatório da Fase 3
│   ├── relatorio_governanca_etica.pdf  # Relatório de governança e ética
│   └── roteiro_pitch_fase3.md          # Roteiro do vídeo técnico
├── specs/
│   ├── task_analyzer_spec.md         # Contrato SDD (fonte editável da verdade)
│   ├── system_design_document.pdf     # Mesmo contrato, em PDF para entrega
│   └── requirements.yaml              # RN01–RN16 estruturadas e rastreadas
├── tests/
│   └── test_harness.py               # 27 cenários de aceite → 37 casos de teste
├── src/
│   └── task_analyzer.py              # Implementação gerada via IA e homologada
└── tools/
    └── gerar_pdfs.py                 # Geração reproduzível dos PDFs
```

## Pré-requisitos

- **Python 3.11 ou superior** (o módulo usa `StrEnum`, disponível a partir do 3.11).
- **Git**.
- **Docker** e **Docker Compose**, opcionais, apenas para a execução containerizada.

## Instalação local

```bash
git clone https://github.com/PedroVargas1204/sdd-task-analyzer.git
cd sdd-task-analyzer
python -m venv .venv
# Windows: .venv\Scripts\activate    |    Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

## Execução dos testes

Comando oficial da suíte, o mesmo usado pelo CI e pelo container:

```bash
pytest tests/test_harness.py -v
```

Com relatório de cobertura:

```bash
pytest tests/test_harness.py --cov=src --cov-report=term-missing
```

Resultado esperado: **37 passed**, com cobertura de `src/` acima de 90%.

## Execução com Docker

Ambiente isolado e reprodutível, sem depender da configuração da máquina local:

```bash
docker build -t task-analyzer-tests .
docker run --rm task-analyzer-tests
```

A imagem parte de `python:3.11-slim`, instala apenas o que está em `requirements.txt` e
define o Test Harness como comando padrão.

## Execução com Docker Compose

A suíte inteira em um único comando:

```bash
docker compose run --rm tests
```

O serviço `tests` constrói a imagem a partir do `Dockerfile` e herda o seu `CMD`, de modo
que CI, `docker run` e Compose executam exatamente o mesmo comando.

## Integração contínua

O workflow [`.github/workflows/ci.yml`](.github/workflows/ci.yml):

| Item | Configuração |
|---|---|
| Gatilhos | `push` e `pull_request` nas branches `main` e `develop` |
| Runner | `ubuntu-latest` |
| Python | 3.11, com cache de dependências do pip |
| Instalação | `pip install -r requirements.txt` |
| Execução | `pytest tests/test_harness.py -v`, seguido do relatório de cobertura |

O resultado de cada execução fica na aba **Actions** do repositório, e o badge no topo
deste README reflete o estado da branch `main`.

**Fluxo de trabalho:** `feature/*` → `develop` → `main`. O CI roda no push de cada branch
de funcionalidade e novamente no Pull Request, de modo que nenhum código chega à `main`
sem que os 37 casos de aceite tenham sido aprovados em ambiente limpo.

## Governança

- **Contrato:** [`specs/task_analyzer_spec.md`](specs/task_analyzer_spec.md) (v1.1.0), com
  o histórico das mudanças em relação à Fase 1. Versão em PDF em
  [`specs/system_design_document.pdf`](specs/system_design_document.pdf).
- **Requisitos rastreados:** [`specs/requirements.yaml`](specs/requirements.yaml) liga cada
  regra RN01–RN16 ao teste que a verifica e à função que a implementa.
- **Regras para a IA:** [`CONTEXT_RULES.md`](CONTEXT_RULES.md).
- **Relatório de governança e ética:**
  [`docs/relatorio_governanca_etica.pdf`](docs/relatorio_governanca_etica.pdf), com a
  análise de alucinações, o modelo Critical-in-the-Loop e a rastreabilidade dos prompts.
- **Commits com código gerado por IA** trazem o rodapé
  `AI-Assisted: sim (revisado por Pedro Vargas dos Santos e Silva)`.

## Regeneração dos PDFs

Os PDFs de entrega são derivados dos arquivos Markdown e podem ser regerados a qualquer
momento:

```bash
pip install reportlab
python tools/gerar_pdfs.py
```

O `reportlab` não faz parte de `requirements.txt`, que é restrito às dependências de
execução e teste previstas no contrato.

## Limitações conhecidas

- **Sem análise estática no pipeline.** Ferramentas como `ruff`, `mypy` e `bandit` não
  foram incluídas, por força da restrição de dependências do contrato (regra P01).
- **Sem teste de desempenho automatizado.** O requisito RNF03 (complexidade O(n)) é
  verificado por revisão de código e por teste manual com 1.000 tarefas, registrado no
  Pull Request da Fase 2.
- **Revisão por um único indivíduo.** Trabalho individual: autor da especificação e
  homologador são a mesma pessoa. A mitigação adotada está descrita na seção B.6 do
  relatório de governança.
- **Escopo do módulo.** Não há persistência, interface, API ou leitura de arquivos: a
  função é pura e opera apenas sobre a lista recebida.

## Autor

Pedro Vargas dos Santos e Silva — Ciência de Dados e Machine Learning (CEUB).
