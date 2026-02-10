"""
Alembic environment for FastAPI Starter Kit.
Uses DATABASE_URL from app.core.database and SQLModel.metadata for autogenerate.
"""
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool

# Import app config and models so SQLModel.metadata has all tables
from app.core.database import DATABASE_URL
from app.models.database import DataProcessingRecord, TaskLog  # noqa: F401
from sqlmodel import SQLModel

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set sqlalchemy.url from our app (env wins over alembic.ini)
config.set_main_option("sqlalchemy.url", DATABASE_URL)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (generate SQL only)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (connect to DB)."""
    from sqlalchemy import create_engine

    connectable = create_engine(
        DATABASE_URL,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
