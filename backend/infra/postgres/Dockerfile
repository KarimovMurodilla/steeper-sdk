FROM postgres:18-bookworm

# Copy custom configuration and initialization scripts into the image
COPY infra/postgres/postgresql.conf /custom-config/postgresql.conf
COPY infra/postgres/setup-config.sh /docker-entrypoint-initdb.d/00-setup-config.sh
COPY infra/postgres/init-extensions.sh /docker-entrypoint-initdb.d/init-extensions.sh

RUN chmod 0644 /custom-config/postgresql.conf \
    && chmod +x /docker-entrypoint-initdb.d/00-setup-config.sh \
    && chmod +x /docker-entrypoint-initdb.d/init-extensions.sh
