# Stage 1: Build the React App
FROM node:20-alpine AS build

WORKDIR /app

# Copy package dependencies and install
COPY package*.json ./
RUN npm ci

# Copy source code and build production package
COPY . .
RUN npm run build

# Stage 2: Serve using Nginx
FROM nginx:stable-alpine

# Copy static assets from build stage to Nginx html path
COPY --from=build /app/dist /usr/share/nginx/html

# Overwrite default Nginx configuration with our custom config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 5173

# Run Nginx in foreground
CMD ["nginx", "-g", "daemon off;"]
