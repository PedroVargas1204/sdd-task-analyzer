# Roteiro do Pitch Técnico — Fase 3 — TaskAnalyzer

**Duração:** 5 minutos · **Formato:** horizontal, com câmera e áudio · **Destino:** YouTube,
público ou não listado (nunca Shorts).

*Texto em itálico* indica a ação na tela. Texto normal é a fala sugerida.

---

## Antes de gravar

### Evidências que precisam estar prontas

| # | Evidência | Como garantir |
|---|---|---|
| 1 | Código da Fase 3 no GitHub | `git push` das branches `develop` e `main` |
| 2 | Build verde na aba Actions | Aguardar a execução terminar após o push |
| 3 | Imagem Docker construída | `docker build -t task-analyzer-tests .` antes de gravar |
| 4 | PDFs gerados | `python tools/gerar_pdfs.py` |
| 5 | Terminal limpo | Fechar abas antigas e limpar o histórico visível |

### Abas e janelas, nesta ordem

1. `github.com/PedroVargas1204/sdd-task-analyzer` — página inicial, badge visível.
2. Aba **Actions**, com a execução mais recente aberta.
3. O arquivo `.github/workflows/ci.yml` no GitHub.
4. Terminal, já dentro da pasta do projeto.
5. `docs/relatorio_governanca_etica.pdf` aberto no leitor de PDF.
6. `specs/requirements.yaml` no GitHub.

### Checklist de gravação

- [ ] Câmera ligada e enquadrada; iluminação à frente, não atrás.
- [ ] Microfone testado; ambiente silencioso.
- [ ] Resolução de gravação em 1920x1080, horizontal.
- [ ] Fonte do terminal aumentada (14 pt ou mais) para ficar legível no vídeo.
- [ ] Notificações do sistema desativadas.
- [ ] Imagem Docker já construída, para o `docker run` não demorar durante a gravação.
- [ ] Cronômetro visível, para controlar os blocos.

---

## 0:00 – 0:30 — Abertura

*Câmera em você, sem compartilhar tela.*

> Olá, professor. Sou Pedro Vargas dos Santos e Silva, do curso de Ciência de Dados e
> Machine Learning, e esta é a entrega final do Bootcamp III.
>
> O TaskAnalyzer é um módulo que calcula métricas de produtividade a partir de uma lista
> de tarefas: tempo médio de conclusão e taxa de atraso, geral e por prioridade.
>
> Nas fases anteriores eu escrevi a especificação e gerei o código com IA sob contrato. O
> objetivo da Fase 3 é diferente: transformar um código que funciona na minha máquina em
> um sistema que se prova sozinho, roda em qualquer lugar e pode ser auditado.

**Tempo acumulado: 0:30.**

---

## 0:30 – 2:00 — Demonstração do CI/CD

*Compartilhe a tela na aba 1, a página inicial do repositório.*

> Este é o repositório público. A primeira novidade da Fase 3 está logo no topo: o badge
> de build do GitHub Actions.

*Aponte para o badge verde, abaixo do título do README.*

> Ele reflete o estado da branch principal em tempo real. Se um teste quebrar, o badge
> fica vermelho para quem quer que abra o repositório.

*Vá para a aba 3, o arquivo `.github/workflows/ci.yml`.*

> Este é o workflow. Ele dispara em dois eventos, push e pull request, nas branches `main`
> e `develop`. Roda em `ubuntu-latest`, com Python 3.11, instala as dependências do
> `requirements.txt` e executa o Test Harness.

*Aponte para a linha do comando de teste.*

> O comando é exatamente o mesmo que eu rodo localmente: `pytest tests/test_harness.py -v`.
> Isso é importante, porque elimina a diferença entre o que eu testo e o que o pipeline
> testa.

*Vá para a aba 2, a execução mais recente no Actions, e expanda o passo dos testes.*

> E aqui está a execução. Repare que os 37 casos de teste rodaram em uma máquina limpa,
> provisionada do zero pelo GitHub, sem nenhuma dependência do meu computador.

*Role a saída até o resumo verde.*

> Trinta e sete aprovados. Esse é o portão de qualidade: nenhum código entra na `main` sem
> passar por aqui.

**Tempo acumulado: 2:00.**

---

## 2:00 – 3:30 — Demonstração do Docker

*Vá para o terminal, aba 4.*

> O CI garante que o código funciona no ambiente do GitHub. O Docker garante que funciona
> em qualquer ambiente.

*Mostre o Dockerfile rapidamente, com `cat Dockerfile` ou no editor.*

> A imagem parte do `python:3.11-slim`, uma base enxuta. Ela instala as dependências antes
> de copiar o código, para aproveitar o cache de camadas, e define o Test Harness como
> comando padrão.

*Execute, com a imagem já construída para ser rápido:*

```bash
docker build -t task-analyzer-tests .
```

> O build reaproveita as camadas já construídas, por isso termina rápido.

```bash
docker run --rm task-analyzer-tests
```

*Enquanto a saída aparece:*

> Os mesmos 37 testes, agora dentro de um container isolado. Nenhuma dependência do meu
> sistema operacional, nenhuma variável de ambiente escondida.

*Mostre o `docker-compose.yml` e execute:*

```bash
docker compose run --rm tests
```

> E com o Compose a suíte inteira roda em um único comando. O serviço herda o `CMD` do
> Dockerfile, então existe um único ponto de verdade sobre como os testes são executados:
> o CI, o `docker run` e o Compose fazem exatamente a mesma coisa.

**Tempo acumulado: 3:30.**

---

## 3:30 – 5:00 — Governança e conclusão

*Vá para a aba 5, o PDF do relatório de governança.*

> O terceiro pilar é a governança. Este relatório tem três seções obrigatórias.

*Role até a Seção A.*

> A primeira é a análise de alucinações. Eu separo três camadas: as CONTEXT_RULES são
> instruções em linguagem natural, que orientam o modelo mas não impedem nada
> mecanicamente; a especificação é um contrato objetivo; e os testes são código executável,
> que falha de forma visível.
>
> O caso mais instrutivo do projeto está aqui: na Fase 2, o enunciado conflitava com a
> minha especificação em oito pontos. Duas fontes de verdade são exatamente a condição em
> que a IA decide sozinha. A regra que resolveu isso não foi uma regra sobre código, foi
> uma regra que obriga o agente a declarar o conflito em vez de escolher.

*Role até a Seção B.*

> A segunda seção é a homologação humana, no modelo Critical-in-the-Loop. A distinção que
> eu faço é esta: os testes respondem se o código faz o que o contrato diz. O humano
> responde se o contrato diz o que o negócio precisa. A segunda pergunta não é
> automatizável.

*Role até a Seção C e depois até as limitações.*

> E a terceira trata de rastreabilidade e ética. Eu registro cinco pendências explícitas,
> incluindo a ausência de análise estática no pipeline e o fato de que, sendo um trabalho
> individual, autor e revisor são a mesma pessoa.

*Vá para a aba 6, o `specs/requirements.yaml`.*

> Fechando a rastreabilidade: este arquivo liga cada uma das dezesseis regras de negócio
> ao teste que a verifica e à função que a implementa. É possível partir de uma linha do
> código e chegar até a regra que a originou.

*Volte a câmera para você, ou deixe a página do repositório na tela.*

> Resumindo a Fase 3: pipeline de integração contínua com build verde, execução
> containerizada e reprodutível, e um relatório de governança que documenta tanto o que
> funcionou quanto o que ficou em aberto.
>
> A conclusão que eu levo do projeto é que a especificação é o verdadeiro artefato de
> engenharia. O código foi gerado em minutos; o contrato levou semanas. Obrigado,
> professor.

**Tempo total: 5:00.**

---

## Colinha de números

| Dado | Valor |
|---|---|
| Casos de teste | 37, todos aprovados |
| Cenários de aceite especificados | 27 (11 de sucesso/borda, 16 de exceção) |
| Cobertura de `src/` | 100% (critério do contrato: ≥ 90%) |
| Regras de negócio | RN01 a RN16 |
| Imagem-base | `python:3.11-slim` |
| Gatilhos do CI | push e pull request em `main` e `develop` |
| Versão do contrato | 1.1.0 |

## Depois de gravar

1. Revisar o áudio e conferir que o terminal está legível.
2. Subir no YouTube como **Público** ou **Não listado**, no formato horizontal.
3. Copiar o link.
4. Submeter no AVA: link do repositório, o PDF do relatório de governança e o link do vídeo.
