FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv && uv sync --frozen --no-dev
COPY server.py .
ENV MCP_TRANSPORT=http PORT=8000 LOG_LEVEL=INFO
EXPOSE 8000
CMD ["uv", "run", "python", "server.py"]
