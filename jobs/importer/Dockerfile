FROM docker.io/library/python@sha256:a1165e272e578941b84abc79e4ab38a0305cd12803a5c4247979ac7655f4d641 AS build
WORKDIR /build
COPY tools/locks/image-build.txt /build/build.txt
RUN pip install --no-cache-dir --require-hashes -r build.txt
COPY jobs/catalog-importer/requirements.txt /build/runtime.txt
RUN pip install --no-cache-dir --require-hashes --prefix=/install -r runtime.txt
COPY packages/python /build/common
COPY jobs/importer /build/importer
RUN python -m build --wheel --no-isolation --outdir /wheels common && python -m build --wheel --no-isolation --outdir /wheels importer && pip install --no-deps --no-cache-dir --prefix=/install /wheels/*.whl

FROM docker.io/library/python@sha256:a1165e272e578941b84abc79e4ab38a0305cd12803a5c4247979ac7655f4d641
ARG SOURCE_SHA
LABEL org.opencontainers.image.source="https://github.com/Jyot-Kikani/DevOps_Assignment" org.opencontainers.image.revision=$SOURCE_SHA
ENV SOURCE_SHA=$SOURCE_SHA PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY --from=build /install /usr/local
COPY --from=dataset / /data/
COPY tools/container_bootstrap.py /app/bootstrap.py
COPY tools/container_import.py /app/import.py
RUN groupadd -g 10001 stellar && useradd -u 10001 -g stellar -M -s /usr/sbin/nologin stellar
USER 10001:10001
WORKDIR /app
CMD ["python", "/app/import.py"]
