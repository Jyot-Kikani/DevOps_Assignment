FROM docker.io/library/node@sha256:a5f4366e834695d5f363b920c104953a535d3a9864d1bdf74566a0ebe01daee5 AS build
WORKDIR /build
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci --ignore-scripts --engine-strict --no-audit --no-fund
COPY apps/web/ ./
ARG SOURCE_SHA
RUN npm run build && node -e 'const fs=require("fs"); const sha=process.argv[1]; if(!/^[a-f0-9]{40}$/.test(sha)) throw Error("SOURCE_SHA required"); fs.writeFileSync("dist/version.json",JSON.stringify({source_sha:sha}));' "$SOURCE_SHA"

FROM ghcr.io/nginx/nginx-unprivileged@sha256:ec0f7ecb1fbd84959ac114e65fb36074ffc97d4d51db0f18ee925162d889dcef
ARG SOURCE_SHA
LABEL org.opencontainers.image.source="https://github.com/Jyot-Kikani/DevOps_Assignment" org.opencontainers.image.revision=$SOURCE_SHA
COPY --from=build /build/dist /usr/share/nginx/html
COPY apps/web/nginx.conf /etc/nginx/conf.d/default.conf
USER 101:101
EXPOSE 8080
HEALTHCHECK --interval=5s --timeout=3s --retries=20 CMD ["curl", "-fsS", "http://127.0.0.1:8080/health/live"]
CMD ["nginx", "-g", "daemon off;"]
