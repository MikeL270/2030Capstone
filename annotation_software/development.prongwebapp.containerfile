# Containerfile for in container development

FROM node:20-alpine

WORKDIR /app

COPY /generator_web_app/package.json ./

RUN npm install

COPY /generator_web_app/. .

EXPOSE 5173

CMD ["npm", "run", "dev"]