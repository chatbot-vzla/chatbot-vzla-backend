# 🚀 Plan de Despliegue Automatizado (CI/CD) para VPS

Este documento sirve como guía y plan para configurar el despliegue automático del backend de Chatbot Venezuela cada vez que se haga un *merge* o *push* a la rama `main` en GitHub.

---

## 1. Requisitos Previos en tu VPS

Antes de que GitHub Actions pueda hacer el despliegue, necesitas tener preparado en tu VPS lo siguiente:
- [ ] Tu VPS corriendo Ubuntu/Debian.
- [ ] Haber clonado el repositorio manualmente la primera vez en una ruta específica (por ejemplo, `/home/ubuntu/chatbot-vzla-backend`).
- [ ] Tener instalados `docker` y `docker-compose`.
- [ ] Tener configurado tu archivo `.env` de producción dentro de la carpeta del proyecto en el VPS.

## 2. Configuración de Secretos en GitHub

Debes registrar las credenciales de tu VPS de forma segura en GitHub:
1. Ve a tu repositorio en GitHub.
2. Navega a **Settings** > **Secrets and variables** > **Actions**.
3. Haz clic en **New repository secret** y añade las siguientes 3 variables:

| Nombre del Secreto | Descripción | Ejemplo |
| :--- | :--- | :--- |
| `SSH_HOST` | La IP pública (o dominio) de tu VPS. | `142.250.190.46` |
| `SSH_USER` | El usuario SSH de tu servidor. | `root` o `ubuntu` |
| `SSH_PRIVATE_KEY` | El contenido completo de tu llave privada (`.pem` o `id_rsa`). Incluye las líneas `-----BEGIN OPENSSH PRIVATE KEY-----` y `-----END...` | |

---

## 3. Código del GitHub Action (El "Listener")

Cuando estés listo para habilitarlo, crea este archivo en tu proyecto local exactamente en esta ruta: `.github/workflows/deploy.yml`

```yaml
name: Deploy Backend to VPS

on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Conectar al VPS y Desplegar
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.SSH_HOST }}
          username: ${{ secrets.SSH_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          # IMPORTANTE: Cambia esta ruta a donde clonaste el repo en tu VPS
          script: |
            cd /home/ubuntu/chatbot-vzla-backend
            
            # 1. Traer los últimos cambios de GitHub forzando actualización
            git fetch --all
            git reset --hard origin/main
            
            # 2. Dar permisos de ejecución por seguridad
            chmod +x start.sh
            chmod +x backend/entrypoint.sh
            chmod +x nginx/startnginx.sh
            
            # 3. Levantar todo con el script de producción
            # REEMPLAZA midominio.com por tu dominio real
            ./start.sh prod midominio.com
```

## 4. ¿Qué hace esto paso a paso?

1. Tú haces un **`git push`** a `main` desde tu computadora.
2. GitHub detecta el cambio y lee el archivo `deploy.yml`.
3. GitHub crea una máquina virtual temporal de Linux en la nube.
4. Esa máquina temporal utiliza tu `SSH_PRIVATE_KEY` para iniciar sesión en tu VPS a través de SSH (como si fueras tú desde la terminal).
5. Se dirige a la carpeta del proyecto.
6. Sobreescribe el código del servidor con el código exacto que acaba de subir a GitHub (`git fetch` + `git reset --hard`).
7. Ejecuta el archivo `./start.sh prod midominio.com` el cual tumba los contenedores viejos, construye las nuevas imágenes y vuelve a levantar la aplicación.
