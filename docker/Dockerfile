FROM python:3.12-slim

WORKDIR /app

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agents_shared/ ./agents_shared/
COPY tonights_pick_mcp/ ./tonights_pick_mcp/
COPY agent/ ./agent/

EXPOSE 8001 8080

CMD ["python", "agent/agent.py"]
