# syntax=docker/dockerfile:1

# Compile the React application with its locked Node dependencies.
FROM node:24-alpine AS build

WORKDIR /workspace/frontend

COPY package.json package-lock.json ./

RUN npm ci

COPY . .

ARG VITE_API_BASE_URL=/
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

RUN npm run build


# Serve only the compiled application through an unprivileged Nginx process.
FROM nginxinc/nginx-unprivileged:1.30-alpine AS runtime

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /workspace/frontend/dist /usr/share/nginx/html

EXPOSE 8080
