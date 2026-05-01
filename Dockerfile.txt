# Usamos una versión ligera de Python
FROM python:3.9-slim

# Evita que Python genere archivos .pyc y permite ver logs en tiempo real
ENV PYTHONUNBUFFERED True

# Copiamos los archivos locales al contenedor
COPY . /app
WORKDIR /app

# Instalamos las librerías del requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Comando para arrancar el servidor usando Gunicorn
# Nota: 'presets_lobinho:app' le indica que el objeto Flask está en tu archivo .py
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 presets_lobinho:app
