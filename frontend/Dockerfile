# syntax=docker/dockerfile:1

# --------------------------------------------------------- development -------
FROM node:22-alpine AS development
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
EXPOSE 5173
CMD ["sh", "-c", "npm install --no-audit --no-fund && npm run dev"]

# --------------------------------------------------------------- build -------
FROM node:22-alpine AS build
ARG VITE_MAP_TILE_URL=""
ENV VITE_MAP_TILE_URL=$VITE_MAP_TILE_URL
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# ---------------------------------------------------------- production -------
FROM nginx:1.27-alpine AS production
COPY --from=build /app/dist /usr/share/nginx/html
# Rendered to /etc/nginx/conf.d/default.conf by the image's envsubst step at start-up.
COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template
ENV BACKEND_UPSTREAM=backend:8000 \
    STORAGE_UPSTREAM=seaweedfs:8333 \
    S3_BUCKET_PUBLIC=smartkids-public \
    S3_BUCKET_PRIVATE=smartkids-private
EXPOSE 80
