# Amazon Pro Intelligence V1.0.0-candidata — imagen mínima (solo biblioteca estándar de Python; sin claves dentro de la imagen)
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 AMAZON_PRO_BIND=0.0.0.0 PORT=10000
RUN useradd --create-home --uid 10001 app && mkdir -p /data && chown app /data
WORKDIR /app
COPY --chown=app . /app
RUN mkdir -p /app/data && chown app /app /app/data   # el servidor crea /app/data al arrancar (lo reveló el CI real)
USER app
EXPOSE 10000
CMD ["python", "server.py"]
