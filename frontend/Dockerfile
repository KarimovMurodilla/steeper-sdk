FROM node:20-alpine AS build

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .

# Vite bakes VITE_* vars at build time. Defaults are empty, which makes the SPA
# call the API/WS on its own origin (same-origin behind one reverse proxy).
# Override at build to bake a specific backend, e.g.:
#   docker build --build-arg VITE_API_BASE_URL=https://api.example.com ...
ARG VITE_API_BASE_URL=""
ARG VITE_WS_HOST=""
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL \
    VITE_WS_HOST=$VITE_WS_HOST
RUN npm run build

FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
