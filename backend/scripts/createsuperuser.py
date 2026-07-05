"""
Interactive CLI: create a user with is_superuser=True and password login.

Run: python -m scripts.createsuperuser
(from project root, with .env configured for your environment.)

For local runs, set POSTGRES_HOST=localhost (or 127.0.0.1) if PostgreSQL is not
reachable as hostname "postgres" (Docker-only). Or use: make createsuperuser
inside the app container.
"""

from __future__ import annotations


def _bootstrap_env() -> None:
    """Load .env from the repository root before any src imports (fixes wrong cwd)."""
    from pathlib import Path

    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    root = Path(__file__).resolve().parent.parent
    env_path = root / ".env"
    if env_path.is_file():
        load_dotenv(env_path, override=False)


_bootstrap_env()

import asyncio  # noqa: E402
import getpass  # noqa: E402
import socket  # noqa: E402
import sys  # noqa: E402

from sqlalchemy import select  # noqa: E402
from sqlalchemy.exc import IntegrityError, OperationalError  # noqa: E402

from src.core.database.session import async_session  # noqa: E402
from src.core.utils.security import hash_password  # noqa: E402
from src.user.models import User  # noqa: E402


def _db_connection_hint() -> str:
    return (
        "Could not connect to PostgreSQL.\n"
        "  • On your host: set POSTGRES_HOST=localhost (or 127.0.0.1) in .env and ensure "
        "the port is exposed (e.g. docker compose maps 5432).\n"
        "  • Or run inside the stack: make createsuperuser (uses the app container)."
    )


def _is_connection_error(exc: BaseException) -> bool:
    """True if exc or its chain looks like a DB connect / DNS failure."""
    err: BaseException | None = exc
    while err is not None:
        if isinstance(err, (OperationalError, socket.gaierror, TimeoutError, OSError)):
            return True
        err = err.__cause__ or err.__context__
    return False


async def _run() -> None:
    login = input("Login: ").strip()
    if not login:
        print("Error: login is required.", file=sys.stderr)
        sys.exit(1)
    if len(login) < 4:
        print("Error: login must be at least 4 characters.", file=sys.stderr)
        sys.exit(1)

    password = getpass.getpass("Password: ")
    password_again = getpass.getpass("Password (again): ")
    if password != password_again:
        print("Error: passwords do not match.", file=sys.stderr)
        sys.exit(1)
    if len(password) < 8:
        print("Error: password must be at least 8 characters.", file=sys.stderr)
        sys.exit(1)

    try:
        async with async_session() as session:
            existing = await session.execute(
                select(User.id).where(
                    User.login == login,
                    User.is_deleted.is_(False),
                )
            )
            if existing.scalar_one_or_none() is not None:
                print(
                    f"Error: user with login {login!r} already exists.",
                    file=sys.stderr,
                )
                sys.exit(1)

            password_hash = hash_password(password)

            user = User(
                login=login,
                password_hash=password_hash,
                is_superuser=True,
                is_active=True,
                first_name=login,
            )
            session.add(user)
            try:
                await session.commit()
                await session.refresh(user)
                print(f"Superuser {login!r} created successfully (id={user.id}).")
            except IntegrityError:
                await session.rollback()
                print(
                    "Error: could not create user (login may already exist).",
                    file=sys.stderr,
                )
                sys.exit(1)
    except Exception as exc:
        if _is_connection_error(exc):
            print(_db_connection_hint(), file=sys.stderr)
            print(f"({type(exc).__name__}: {exc})", file=sys.stderr)
            sys.exit(1)
        raise


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
