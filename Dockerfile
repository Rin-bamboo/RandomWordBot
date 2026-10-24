FROM python:3.14.8-slim-trixie

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

RUN mkdir -p /app/logs /app/output_list \
    && chown -R bot:bot /app/logs /app/output_list

RUN mkdir -p /app/access-policy \
    && cp /app/config/access_policy.json /app/access-policy/policy.json \
    && chown -R bot:bot /app/access-policy

USER bot

CMD ["python", "-u", "RandomWordBot.py"]
