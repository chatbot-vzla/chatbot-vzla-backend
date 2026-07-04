#!/bin/sh

# Paths
NGINX_HTTP_TEMPLATE="/etc/nginx/templates/nginx-http.conf.template"
NGINX_HTTPS_TEMPLATE="/etc/nginx/templates/nginx-https.conf.template"
NGINX_DEV_TEMPLATE="/etc/nginx/templates/nginx-dev.conf.template"
NGINX_CONF="/etc/nginx/nginx.conf"

# Check if SSL certificates exist
if [ "$MODE" = "dev" ]; then
  echo "Using development configuration. Copying template as-is."
  cp ${NGINX_DEV_TEMPLATE} ${NGINX_CONF}
else
  if [ -f "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" ]; then
    echo "SSL certificates found. Using HTTPS configuration."
    envsubst '$DOMAIN' < ${NGINX_HTTPS_TEMPLATE} > ${NGINX_CONF}
  else
    echo "SSL certificates not found. Using HTTP configuration."
    envsubst '$DOMAIN' < ${NGINX_HTTP_TEMPLATE} > ${NGINX_CONF}
  fi
fi


# Start Nginx
nginx -g 'daemon off;'