FROM python:3.14.6-slim-trixie

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    MPLCONFIGDIR=/tmp/matplotlib

RUN addgroup --system bot \
    && adduser --system --ingroup bot bot

COPY --chown=bot:bot requirements.txt .

RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

COPY --chown=bot:bot . .

RUN mkdir -p /app/logs \
    && chown -R bot:bot /app/logs

USER bot

CMD ["python", "-u", "RandomWordBot.py"]
