# Roteiro do Pitch Técnico — Fase 3 — TaskAnalyzer

**Duração:** 5 minutos · **Formato:** horizontal, com câmera e áudio · **Destino:** YouTube,
público ou não listado (nunca Shorts).

*Texto em itálico* indica a ação na tela. Texto normal é a fala.

---

## Antes de gravar

### Evidências — todas já disponíveis

| # | Evidência | Estado |
|---|---|---|
| 1 | Código da Fase 3 na `main` | Pronto: 15 commits, tag `v2.0.0` |
| 2 | Build verde na aba Actions | Pronto: Python 3.11.17, 37 passed, cobertura 100% |
| 3 | Imagem Docker construída | Pronto: `build`, `run` e `compose run` executados |
| 4 | PDFs no repositório | Pronto: SDD e relatório de governança |
| 5 | Badge **CI passing** no README | Pronto, verde |

### Abas e janelas, nesta ordem

1. `github.com/PedroVargas1204/sdd-task-analyzer` — página inicial, com o badge visível.
2. Aba **Actions**, com a execução da `main` aberta e o passo de cobertura expandido.
3. O arquivo `.github/workflows/ci.yml` no GitHub.
4. Terminal, já dentro de `C:\Users\Pedro Vargas\Documents\sdd-task-analyzer`.
5. `docs/relatorio_governanca_etica.pdf` aberto no leitor de PDF.
6. `specs/requirements.yaml` no GitHub.

### Checklist de gravação

- [ ] Docker Desktop aberto, com "Engine running" no rodapé.
- [ ] Imagem já construída, para o `build` sair do cache em segundos.
- [ ] Câmera enquadrada, luz à frente e não atrás.
- [ ] Microfone testado, ambiente silencioso.
- [ ] Gravação em 1920x1080, horizontal.
- [ ] Fonte do terminal em 16 pt ou mais.
- [ ] Notificações do Windows desativadas.
- [ ] Cronômetro visível para controlar os blocos.

---

## 0:00 – 0:30 — Abertura

*Câmera em você, sem compartilhar tela.*

> Olá, professor. Sou Pedro Vargas dos Santos e Silva, do curso de Ciência de Dados e
> Machine Learning, e esta é a entrega final do Bootcamp III.
>
> O TaskAnalyzer calcula métricas de produtividade a partir de uma lista de tarefas: tempo
> médio de conclusão e taxa de atraso, geral e por prioridade.
>
> Nas fases anteriores eu escrevi a especificação e gerei o código com IA sob contrato. O
> objetivo da Fase 3 é outro: transformar um código que funciona na minha máquina em um
> sistema que se prova sozinho, roda em qualquer lugar e pode ser auditado.

---

## 0:30 – 2:00 — Integração contínua

*Compartilhe a tela na aba 1, a página inicial do repositório.*

> Este é o repositório público. A primeira novidade da Fase 3 está logo abaixo do título:
> o badge do GitHub Actions, com o build passando.

*Aponte para o badge verde.*

> Ele reflete o estado da branch principal em tempo real. Se um teste quebrar, qualquer
> pessoa que abrir o repositório vê o badge vermelho.

*Vá para a aba 3, o `ci.yml`.*

> Este é o workflow. Dispara em dois eventos, push e pull request, nas branches `main` e
> `develop`. Roda em `ubuntu-latest`, com Python 3.11, instala as dependências do
> `requirements.txt` e executa o Test Harness.

*Aponte para a linha do comando.*

> O comando é o mesmo que eu rodo no meu terminal: `pytest tests/test_harness.py -v`. Isso
> elimina a diferença entre o que eu testo e o que o pipeline testa.

*Vá para a aba 2, a execução no Actions, com o passo de cobertura expandido.*

> E aqui está a execução, numa máquina limpa, provisionada do zero pelo GitHub. Python
> 3.11.17, trinta e sete casos coletados, trinta e sete aprovados, e cobertura de cem por
> cento do módulo.

*Aponte para a linha `configfile: pytest.ini`.*

> Um detalhe que vale mencionar: este `pytest.ini` resolveu um problema real. O comando
> `pytest` direto não coloca a raiz do projeto no caminho de importação, diferente do
> `python -m pytest`. Sem esse arquivo, o teste passava na minha máquina de um jeito e
> falhava no pipeline. Fixar a configuração garante que o comando se comporte igual em
> todos os três ambientes.

---

## 2:00 – 3:30 — Containerização

*Vá para o terminal, aba 4.*

> O CI garante que o código funciona no ambiente do GitHub. O Docker garante que funciona
> em qualquer ambiente.

*Mostre o Dockerfile:*

```
type Dockerfile
```

> A imagem parte do `python:3.11-slim`, uma base enxuta. Ela instala as dependências antes
> de copiar o código, para aproveitar o cache de camadas, e define o Test Harness como
> comando padrão do container.

*Execute:*

```
docker build -t task-analyzer-tests .
```

> O build reaproveita as camadas já construídas, por isso termina rápido.

```
docker run --rm task-analyzer-tests
```

*Enquanto a saída aparece:*

> Os mesmos trinta e sete testes, agora dentro de um container isolado. Repare no
> `rootdir`: barra `app`. Não é mais a minha pasta, é o sistema de arquivos do container.
> Nenhuma dependência do meu Windows, nenhuma variável de ambiente escondida.

*Mostre o compose e execute:*

```
type docker-compose.yml
docker compose run --rm tests
```

> E com o Compose a suíte inteira roda em um único comando. O serviço herda o comando do
> Dockerfile, então existe um único ponto de verdade sobre como os testes são executados:
> o pipeline, o `docker run` e o Compose fazem exatamente a mesma coisa.

---

## 3:30 – 5:00 — Governança e conclusão

*Vá para a aba 5, o PDF do relatório.*

> O terceiro pilar é a governança. Este relatório tem três seções.

*Role até a Seção A.*

> A primeira é a análise de alucinações. Eu separo três camadas: as CONTEXT_RULES são
> instruções em linguagem natural, que orientam o modelo mas não impedem nada
> mecanicamente; a especificação é um contrato objetivo; e os testes são código
> executável, que falha de forma visível.
>
> O caso mais instrutivo do projeto está aqui. Na Fase 2, o enunciado conflitava com a
> minha especificação em oito pontos. Duas fontes de verdade são exatamente a condição em
> que a IA decide sozinha, e decide em silêncio. O que resolveu não foi uma regra sobre
> código: foi uma regra que obriga o agente a declarar o conflito em vez de escolher.

*Role até a Seção B, no checklist.*

> A segunda seção é a homologação humana, no modelo Critical-in-the-Loop. A distinção que
> eu faço é esta: os testes respondem se o código faz o que o contrato diz; o humano
> responde se o contrato diz o que o negócio precisa. A segunda pergunta não é
> automatizável.
>
> E aqui está o checklist, com o que foi efetivamente executado separado do que ainda é
> proposta.

*Role até as limitações, na Seção C.*

> A terceira trata de rastreabilidade e ética. Eu registro cinco limitações explícitas,
> incluindo a ausência de análise estática no pipeline e o fato de que, num trabalho
> individual, autor e revisor são a mesma pessoa.

*Vá para a aba 6, o `requirements.yaml`.*

> Fechando a rastreabilidade: este arquivo liga cada uma das dezesseis regras de negócio
> ao cenário de aceite, ao teste que a verifica e à função que a implementa. Dá para
> partir de uma linha do código e chegar até a regra que a originou.

*Volte a câmera para você.*

> Resumindo a Fase 3: pipeline com build verde, execução containerizada e reprodutível, e
> um relatório que documenta tanto o que funcionou quanto o que ficou em aberto.
>
> A conclusão que eu levo do projeto é que a especificação é o verdadeiro artefato de
> engenharia. O código foi gerado em minutos; o contrato levou semanas. Obrigado,
> professor.

---

## Colinha de números

| Dado | Valor |
|---|---|
| Casos de teste | 37, aprovados em três ambientes |
| Cenários de aceite | 27 (11 de sucesso/borda, 16 de exceção) |
| Cobertura de `src/` | 100% (o contrato exige ≥ 90%) |
| Regras de negócio | RN01 a RN16 |
| Python do CI | 3.11.17 em `ubuntu-latest` |
| Imagem-base | `python:3.11-slim` |
| Commits na `main` | 15 |
| Pull Requests | 4, todos mergeados |
| Tag | `v2.0.0` |

## Se travar na gravação

- **Esqueceu a fala:** olhe a colinha e diga o número. Os dados sustentam o bloco sozinhos.
- **Comando deu erro:** não apague. Diga o que aconteceu e siga; mostrar diagnóstico conta
  a favor.
- **Passou do tempo:** corte do bloco 3 a parte do `requirements.yaml`; ela é a menos
  essencial.
- **Docker não sobe:** mostre o `Dockerfile` e o `docker-compose.yml` e explique a
  estrutura. Os arquivos estão no repositório e o pilar continua entregue.

## Depois de gravar

1. Revise o áudio e confirme que o terminal está legível.
2. Suba no YouTube como **Público** ou **Não listado**, horizontal.
3. Submeta no AVA: link do repositório, `docs/relatorio_governanca_etica.pdf` e link do vídeo.
