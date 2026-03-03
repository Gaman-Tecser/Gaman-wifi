import logging
from logging.config import fileConfig

from flask import current_app
from alembic import context

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

logger = logging.getLogger("alembic.env")

target_metadata = current_app.extensions["migrate"].db.metadata

GAMAN_TABLES = {
    "gaman_admin", "gaman_wifi_user", "gaman_wifi_group", "gaman_access_point",
    "gaman_allowed_domain", "gaman_portal_user", "gaman_portal_session",
}


def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table":
        return name in GAMAN_TABLES
    if type_ == "index" and hasattr(object, "table"):
        return object.table.name in GAMAN_TABLES
    if type_ == "column" and hasattr(object, "table"):
        return object.table.name in GAMAN_TABLES
    return True


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = current_app.extensions["migrate"].db.engine
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
