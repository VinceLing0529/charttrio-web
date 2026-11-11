FROM node:20-alpine AS build
WORKDIR /web
COPY package*.json ./
RUN npm install --no-audit --no-fund
COPY . .
# 同域部署：API 走相对路径 /api，由 nginx 反代到后端
ARG REACT_APP_API_URL=/
ENV REACT_APP_API_URL=$REACT_APP_API_URL
RUN npm run build

FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /web/build /usr/share/nginx/html
EXPOSE 80
