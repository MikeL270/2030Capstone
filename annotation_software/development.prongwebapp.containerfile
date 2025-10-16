# Containerfile for in container development

FROM node:20-alpine

USER root

RUN mkdir /app && /app

COPY /generator_web_app/package.json package-lock.json* ./

RUN chown -R pronghorn:pronghorn /app

RUN chmod 644 package.json \
    && [ -f package-lock.json ] && chmod 644 package-lock.json || true


RUN cd /app && npm install

COPY /generator_web_app/. .

RUN chown -R prong:prong /app
RUN chmod -R 755 /app

USER prong

EXPOSE 5173

CMD ["npm", "run", "dev"]