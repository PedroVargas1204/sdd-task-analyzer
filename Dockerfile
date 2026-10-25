# Pilar 2 da Fase 3: ambiente de execução reprodutível para o TaskAnalyzer.
# Imagem leve e fixa: elimina o "na minha máquina funciona".
FROM python:3.11-slim

# Saída do pytest sem buffer e sem .pyc no container.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependências primeiro: o cache de camadas só é invalidado quando elas mudam.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Configuração do pytest: coloca a raiz no sys.path, para que o comando abaixo
# resolva "from src.task_analyzer import ..." dentro do container.
COPY pytest.ini .

# Código da aplicação e suíte de testes.
COPY src/ ./src/
COPY tests/ ./tests/

# Comando padrão: executa o Test Harness, idêntico ao do CI.
CMD ["pytest", "tests/test_harness.py", "-v"]
