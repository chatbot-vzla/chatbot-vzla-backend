#!/bin/bash

# start.sh
# Script para iniciar el proyecto en desarrollo o producción

if [ $# -lt 1 ]; then
    echo "Error: Faltan argumentos."
    echo "Uso: $0 <dev|prod> [domain]"
    exit 1
fi

INPUT_MODE=$1

if [ "$INPUT_MODE" = "prod" ]; then
    if [ $# -lt 2 ]; then
        echo "Error: El dominio (DOMAIN) es obligatorio para el modo producción."
        echo "Uso: $0 prod <midominio.com>"
        exit 1
    fi
    DOMAIN=$2
    MODE="production"
    DEBUG="False"
    
    echo "Configurando entorno para PRODUCCIÓN (Dominio: $DOMAIN)..."
    
    # Actualizar o insertar DOMAIN en .env
    if grep -q "^DOMAIN=" .env; then
        sed -i "s/^DOMAIN=.*/DOMAIN=$DOMAIN/" .env
    else
        echo "DOMAIN=$DOMAIN" >> .env
    fi

elif [ "$INPUT_MODE" = "dev" ]; then
    MODE="dev"
    DEBUG="True"
    echo "Configurando entorno para DESARROLLO..."
else
    echo "Error: Modo inválido '$INPUT_MODE'. Debe ser 'dev' o 'prod'."
    echo "Uso: $0 <dev|prod> [domain]"
    exit 1
fi

# Actualizar o insertar MODE en .env
if grep -q "^MODE=" .env; then
    sed -i "s/^MODE=.*/MODE=$MODE/" .env
else
    echo "MODE=$MODE" >> .env
fi

# Actualizar o insertar DEBUG en .env
if grep -q "^DEBUG=" .env; then
    sed -i "s/^DEBUG=.*/DEBUG=$DEBUG/" .env
else
    echo "DEBUG=$DEBUG" >> .env
fi

echo "Iniciando contenedores con Docker Compose..."
docker compose up -d --build
