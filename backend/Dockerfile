# Usa una imagen oficial de Python como base
FROM python:3.14-slim

# Establece variables de entorno para que Python no genere archivos .pyc y la salida se envíe directamente a la terminal
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Actualiza el sistema e instala dependencias del sistema que puedan ser necesarias (ej. gcc)
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copia el archivo de dependencias
COPY requirements.txt /app/

# Instala las dependencias de Python
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia el resto del código del proyecto
COPY . /app/

# Hacer ejecutable el script de entrada
RUN chmod +x /app/entrypoint.sh

# Expone el puerto 8000 (donde corre Django por defecto)
EXPOSE 8000

# Script de entrada para migraciones automáticas
ENTRYPOINT ["/app/entrypoint.sh"]

# Comando para ejecutar el servidor de desarrollo
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

