# CONTEXT_RULES.md — TaskAnalyzer

> Arquivo de regras persistentes para agentes de IA (versão 1.1.0). Deve ser fornecido
> integralmente no início de TODA sessão com assistentes de IA, junto com
> `specs/task_analyzer_spec.md`.
>
> Ordem de precedência em caso de conflito:
> 1. `specs/task_analyzer_spec.md` (contrato de negócio)
> 2. `tests/test_harness.py` (cenários de aceite)
> 3. `CONTEXT_RULES.md` (este arquivo)
> 4. Instruções pontuais do desenvolvedor na conversa

## 1. Papel do agente

Você é um assistente de implementação. O desenvolvedor humano é o arquiteto da especificação
e o homologador final. Você EXECUTA o contrato; não o redefine.

## 2. Diretrizes arquiteturais (obrigatórias)

- D01: Python 3.11 ou superior. Use recursos nativos da versão (`StrEnum`, `X | None`).
- D02: Type hints em todas as funções, métodos, parâmetros e retornos.
- D03: Seguir PEP 8; linhas com no máximo 99 caracteres.
- D04: Single Responsibility: cada função tem um único propósito e ~25 linhas no máximo.
- D05: Google style docstrings em módulo, classes e funções (Args, Returns, Raises).
- D06: Exceções específicas da hierarquia `TaskValidationError`
  (`EntradaInvalidaError`, `TarefaInvalidaError`, `DataInvalidaError`), com mensagens em
  português no padrão `"Tarefa {id}: {motivo}."`.
- D07: Logging via `logging.getLogger(__name__)`; nunca `print`. INFO no início e fim da
  análise, DEBUG por tarefa, ERROR antes de lançar exceção. Nunca registrar o campo `titulo`
  nos logs (minimização de dados — LGPD).
- D08: Nomes idênticos aos do contrato (ex.: `analyze_tasks`, `tempo_medio_conclusao_horas`).
- D09: Estruturas públicas imutáveis (`@dataclass(frozen=True)`); a entrada nunca é modificada.
- D10: Constantes nomeadas em MAIÚSCULAS, sem números mágicos
  (ex.: `SEGUNDOS_POR_HORA = 3600`, `CASAS_DECIMAIS = 2`).
- D11: Somente biblioteca padrão em `src/`. Nos testes: apenas `pytest` e `pytest-cov`.
- D12: Arredondamento com `round(valor, 2)` aplicado somente ao resultado final.
- D13: Divisão por zero é evitada com guarda explícita (quantidade == 0 → 0.0), nunca com
  `try/except ZeroDivisionError`.

## 3. Proibições explícitas

- P01: Não utilizar bibliotecas externas não autorizadas
  (ex.: pandas, numpy, pydantic, python-dateutil, arrow).
- P02: Não alterar, remover, pular (`skip`/`xfail`) ou adaptar os cenários de
  `tests/test_harness.py`. Se um teste falhar, corrija o código, nunca o teste.
- P03: Não modificar a estrutura de pastas nem criar arquivos fora da árvore definida.
- P04: Não persistir dados em arquivos ou bancos; não fazer I/O de arquivos, rede ou
  variáveis de ambiente.
- P05: Não alterar a assinatura (nome, parâmetros, tipos e retorno) das funções e classes
  públicas sem autorização.
- P06: Não gerar código sem testes correspondentes para novas funcionalidades.
- P07: Não inserir código duplicado, morto, comentado ou sem necessidade.
- P08: Não assumir comportamentos não especificados. Havendo ambiguidade, PARE e pergunte.
- P09: Não capturar `Exception` genérica nem silenciar exceções (`except: pass`).
- P10: Não usar `eval`, `exec`, `pickle`, `global` ou estado mutável em nível de módulo.
- P11: Não retornar campos, chaves ou tipos diferentes dos definidos no contrato.
- P12: Não usar `print` nem comentários excessivos (comente o "porquê", não o "o quê").

## 4. Regras de interação com a IA

- I01: Antes de gerar código, resuma seu entendimento do contrato e liste suposições e
  dúvidas. Aguarde confirmação.
- I02: Gere um arquivo por vez, completo, sem trechos omitidos ("...").
- I03: Ao final, indique quais regras de negócio (RN) e cenários (CA/CE) cada função atende.
- I04: Não invente APIs, bibliotecas ou funções inexistentes.
- I05: Se uma instrução do usuário conflitar com este arquivo ou com a especificação,
  aponte o conflito antes de agir.

## 5. Critério de aceite do código gerado

O código só é aceito quando:

1. `python -m pytest -v --cov=src --cov-report=term-missing` executa com 100% dos cenários
   aprovados;
2. a cobertura de `src/` é maior ou igual a 90%;
3. o código passa na homologação humana (seção 4.1 da especificação).
