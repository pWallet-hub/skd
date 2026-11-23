# Edge proxy. Templates are rendered with envsubst at start-up by the official image.
FROM nginx:1.27-alpine
COPY templates /etc/nginx/templates
# Where the web app is served from: Vite dev server (development) or static nginx (production).
ENV FRONTEND_UPSTREAM=frontend:5173
