# Chatbot Venezuela - Backend

Este es el backend del proyecto Chatbot Venezuela, desarrollado con **Django** (versión 6.0.6) y **Django Channels** (versión 4.3.2) para dar soporte a comunicación asíncrona / WebSockets.

---

## 📂 Estructura del Proyecto

Para que te familiarices con la estructura de archivos, aquí tienes una descripción de dónde está cada cosa:

```text
chatbot-vzla-backend/
├── docker-compose.yml     # Configuración de los servicios Docker (web, etc.)
├── README.md              # Documentación del proyecto
├── LICENSE                # Licencia del proyecto
├── .venv/                 # Entorno virtual de Python con dependencias instaladas
└── backend/               # Contiene todo el proyecto de Django
    ├── Dockerfile         # Receta para construir la imagen de Docker
    ├── requirements.txt   # Dependencias de Python del proyecto
    ├── db.sqlite3         # Base de datos SQLite local para desarrollo rápido
    ├── manage.py          # Script de entrada para comandos de Django
    ├── config/            # Carpeta de configuración del proyecto Django global
    │   ├── settings.py    # Configuración general (BD, apps instaladas, middleware)
    │   ├── urls.py        # Enrutador principal del proyecto
    │   ├── asgi.py        # Configuración para servidores ASGI (WebSockets/Channels)
    │   └── wsgi.py        # Configuración para servidores WSGI
    ├── communications/    # App Django para comunicación (ej. WebSockets)
    │   ├── migrations/    # Historial de migraciones
    │   ├── admin.py       # Panel de administración
    │   ├── apps.py        # Configuración de la aplicación
    │   ├── models.py      # Modelos de base de datos
    │   ├── serializers.py # Serializadores (DRF) para comunicación
    │   ├── services/      # Servicios de lógica de negocio de comunicación
    │   │   ├── __init__.py
    │   │   └── chat_service.py # Lógica de mensajería y canales
    │   ├── tests.py       # Pruebas unitarias
    │   ├── urls.py        # Enrutamiento de la aplicación (webhook)
    │   └── views.py       # Vistas de la aplicación (ej. TwilioWebhookView)
    ├── core/              # App Django principal / utilidades del núcleo
    │   ├── migrations/    # Historial de migraciones
    │   ├── admin.py       # Panel de administración
    │   ├── apps.py        # Configuración de la aplicación
    │   ├── models.py      # Modelos de base de datos
    │   ├── serializers.py # Serializadores (DRF) para el core
    │   ├── tests.py       # Pruebas unitarias
    │   └── views.py       # Vistas de la aplicación
    ├── rag/               # App Django para RAG (Retrieval-Augmented Generation)
    │   ├── migrations/    # Historial de migraciones
    │   ├── admin.py       # Panel de administración
    │   ├── apps.py        # Configuración de la aplicación
    │   ├── models.py      # Modelos de base de datos
    │   ├── serializers.py # Serializadores (DRF) para RAG
    │   ├── tests.py       # Pruebas unitarias
    │   └── views.py       # Vistas de la aplicación
    ├── scraper/           # App Django para extracción de fuentes (Hospitales, Sheets, OSINT)
    │   ├── migrations/    # Historial de migraciones
    │   ├── admin.py       # Panel de administración
    │   ├── apps.py        # Configuración de la aplicación
    │   ├── models.py      # Modelos: Source, Investigation, SourceResult
    │   ├── serializers.py # Serializadores (DRF) para scraper
    │   ├── tests.py       # Pruebas unitarias
    │   └── views.py       # Vistas de la aplicación
    └── subjects/          # App Django para perfiles de personas buscadas (sujetos)
        ├── migrations/    # Historial de migraciones
        ├── admin.py       # Panel de administración
        ├── apps.py        # Configuración de la aplicación
        ├── models.py      # Modelos: MissingPerson, Alias, Relative, LocationHistory
        ├── serializers.py # Serializadores (DRF) para subjects
        ├── tests.py       # Pruebas unitarias
        └── views.py       # Vistas de la aplicación
```

---

## 🛠️ Cómo Empezar (Setup Local)

Sigue estos pasos para arrancar el servidor de desarrollo localmente:

### 1. Activar el Entorno Virtual
El entorno virtual ya viene preparado en la carpeta `.venv`. Dependiendo de tu sistema operativo, actívalo con:

- **Linux/macOS:**
  ```bash
  source .venv/bin/activate
  ```
- **Windows (Command Prompt):**
  ```cmd
  .venv\Scripts\activate.bat
  ```
- **Windows (PowerShell):**
  ```powershell
  .venv\Scripts\Activate.ps1
  ```

### 2. Instalar Dependencias (opcional)
Las dependencias actuales son mínimas: `Django` y `channels`. Si necesitas instalar o reinstalar:
```bash
pip install django channels
```
*(Nota: Actualmente las dependencias instaladas en el entorno son `Django==6.0.6` y `channels==4.3.2`).*

### 3. Aplicar Migraciones
Django utiliza migraciones para sincronizar tus modelos de Python con la base de datos (SQLite en este caso):
```bash
python manage.py migrate
```

### 4. Crear un Superusuario (para el panel admin)
Para poder iniciar sesión en el panel administrador (`/admin`):
```bash
python manage.py createsuperuser
```
Sigue las instrucciones en la terminal para definir usuario, correo y contraseña.

### 5. Iniciar el Servidor de Desarrollo
```bash
python manage.py runserver
```
El servidor estará corriendo en `http://127.0.0.1:8000/`.

---

## 🚀 Guía Rápida de Django para Principiantes

Django sigue el patrón **MVT (Model-View-Template)** (una variante de MVC):

1. **Modelos (`models.py`)**: Aquí defines las tablas de la base de datos usando clases de Python.
2. **Vistas (`views.py`)**: Reciben una petición web (request) y devuelven una respuesta (response), generalmente en formato JSON para APIs, o renderizan plantillas.
3. **URLs (`urls.py`)**: Mapean rutas de URL (ej. `/api/chat/`) a funciones o clases en tus vistas.

### Flujo de Trabajo Típico en Django:

#### Paso 1: Registrar tu App
Para que Django reconozca la aplicación `chatbot`, debes añadirla a `INSTALLED_APPS` dentro del archivo `config/settings.py` (línea 33):
```python
INSTALLED_APPS = [
    ...
    'chatbot',  # Añade esto aquí
]
```

#### Paso 2: Crear un Modelo
Si necesitas almacenar conversaciones en la base de datos, edita `chatbot/models.py`:
```python
from django.db import models

class Message(models.Model):
    user_message = models.TextField()
    bot_response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"User: {self.user_message[:20]}..."
```

Una vez creado o modificado un modelo, debes avisar a Django para que cree y aplique los cambios a la base de datos:
```bash
python manage.py makemigrations chatbot
python manage.py migrate
```

#### Paso 3: Crear una Vista
Si quieres exponer un endpoint HTTP, ve a `chatbot/views.py`:
```python
from django.http import JsonResponse
from .models import Message

def chat_history(request):
    messages = Message.objects.all().values('user_message', 'bot_response', 'created_at')
    return JsonResponse(list(messages), safe=False)
```

#### Paso 4: Enrutar la Vista
Primero, crea un archivo `chatbot/urls.py` para tu aplicación:
```python
from django.urls import path
from . import views

urlpatterns = [
    path('history/', views.chat_history, name='chat_history'),
]
```

Y luego inclúyelo en el archivo de rutas principal `config/urls.py`:
```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('chatbot.urls')),  # Las URLs de chatbot empezarán por /api/
]
```

Ahora, al acceder a `http://127.0.0.1:8000/api/history/` verás el listado de mensajes en formato JSON.

---

## ⚡ Conexión con WebSockets (Django Channels)
Dado que el proyecto incluye `channels`, ahora las rutas WebSocket aceptan tanto IDs numéricos como UUIDs para el identificador de conversación.
- El patrón de ruta en `backend/communications/routing.py` pasó de `r'ws/chat/(?P<conversation_id>\d+)/$'` a `r'ws/chat/(?P<conversation_id>[^/]+)/$'` para soportar UUIDs generados por el frontend.
- El `ChatConsumer` ahora crea o recupera una conversación automáticamente cuando el ID es un UUID y envía una respuesta simulada del bot con el rol `SYSTEM` después de recibir un mensaje de `USER`.

---

## 🐳 Docker y Despliegue

El proyecto está completamente dockerizado y preparado tanto para desarrollo local como para producción. Utiliza **Docker Compose** para orquestar la aplicación, la base de datos (Supabase remoto), Redis y un Proxy Inverso (Nginx).

### 1. Script de Inicio (`start.sh`)

Para simplificar el arranque de los contenedores y la configuración del entorno, hemos creado el script `start.sh`. Este script actualiza automáticamente tu archivo `.env` y levanta los servicios.

**Para Desarrollo Local:**
```bash
./start.sh dev
```
Esto configurará `MODE=dev` y `DEBUG=True` en tu `.env` y levantará la aplicación de forma local.

**Para Producción:**
En producción, es obligatorio proporcionar tu nombre de dominio para que Nginx y Certbot puedan generar los certificados SSL (HTTPS).
```bash
./start.sh prod midominio.com
```
Esto configurará `MODE=production`, `DEBUG=False`, y `DOMAIN=midominio.com` en tu `.env` antes de levantar los contenedores.

### 2. Base de Datos (Supabase / PostgreSQL)

El proyecto está configurado para conectarse a **Supabase** usando su Connection Pooler (puerto 6543) por compatibilidad con redes IPv4.
Todas las credenciales se manejan en el archivo `.env`. Si necesitas cambiar tu contraseña o base de datos, modifica las variables `DB_HOST`, `DB_PORT`, `DB_USER` y `DB_PASSWORD` allí.
> **Nota:** Ya no necesitas ejecutar `makemigrations` o `migrate` manualmente. El contenedor de Django usa un `entrypoint.sh` que ejecuta las migraciones automáticamente cada vez que arranca.

### 3. Nginx (Proxy Inverso) y SSL

El tráfico HTTP y HTTPS es manejado por el servicio **Nginx**.
- La carpeta `nginx/` contiene las configuraciones base.
- Si inicias en modo `dev`, Nginx servirá tráfico HTTP estándar.
- Si inicias en modo `production` (y configuras la variable `EMAIL` en tu `.env`), **Certbot** se encargará de pedir un certificado SSL a Let's Encrypt para tu `DOMAIN`, y Nginx pasará a usar la configuración HTTPS automáticamente.
- **WebSockets:** Nginx ya está configurado para permitir `Upgrade` headers, lo que garantiza que los WebSockets de Django Channels (Daphne) funcionen sin problemas a través del proxy.

### 4. Ejecutar Comandos de Django en Docker

Para correr comandos interactivos o crear superusuarios dentro del contenedor, usa `docker compose exec`:

- **Crear Superusuario:**
  ```bash
  docker compose exec backend python manage.py createsuperuser
  ```
- **Abrir Shell de Django:**
  ```bash
  docker compose exec backend python manage.py shell
  ```
