"""Configure Alembic migrations for the Cloud Operations database."""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from app.core.config import get_settings
from app.db.base import Base

# Import all database models so Alembic can discover their tables.
import app.models  # noqa: F401


# Access the Alembic configuration created from alembic.ini.
config = context.config

# Configure Python logging from the Alembic configuration file.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Read the database URL from the private project-level .env file.
# Escaping percent signs prevents ConfigParser interpolation errors.
database_url = get_settings().database_url.replace("%", "%%")
config.set_main_option("sqlalchemy.url", database_url)

# Provide model metadata for migration autogeneration.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations without creating a live database connection."""

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations using a live SQLAlchemy database connection."""

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


# Select the migration mode requested by the Alembic command.
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
