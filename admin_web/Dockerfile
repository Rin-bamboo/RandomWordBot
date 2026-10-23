FROM python:3.14.8-slim-trixie
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN pip install --no-cache-dir aiohttp==3.14.5 mysql-connector-python==26.7.0 && useradd --uid 10001 --create-home dashboard
COPY . /app/admin_web
COPY runtime/ /app/
USER dashboard
CMD ["python", "-m", "admin_web.app"]
