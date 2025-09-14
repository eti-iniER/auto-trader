import asyncio
from typing import List

import typer
from pydantic import EmailStr
from sqlalchemy import delete
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select

from .db.crud import get_user_by_email
from .db.enums import UserRole
from .db.models import User, Order, Instrument, Log, Base
from .db.session import async_session, engine

# Create the main CLI app
app = typer.Typer(
    help="Admin commands for the Auto Trader application.",
    no_args_is_help=True,
    invoke_without_command=False,
)


async def _make_admin_async(email: EmailStr) -> bool:
    """
    Async helper function to make a user admin.

    Args:
        email (EmailStr): The email of the user to make admin

    Returns:
        bool: True if successful, False if user not found
    """
    async with async_session() as db:
        try:
            # Get user by email
            user = await get_user_by_email(db, email)

            if not user:
                typer.echo(f"❌ User with email '{email}' not found.", err=True)
                return False

            # Check if user is already admin
            if user.role == UserRole.ADMIN:
                typer.echo(f"ℹ️  User '{email}' is already an admin.")
                return True

            # Update user role to admin
            user.role = UserRole.ADMIN

            # Commit the changes
            await db.commit()
            await db.refresh(user)

            typer.echo(f"✅ Successfully made user '{email}' an admin.")
            return True

        except Exception as e:
            await db.rollback()
            typer.echo(f"❌ Error making user admin: {str(e)}", err=True)
            return False


async def _get_all_users_async() -> List[User]:
    """
    Async helper function to get all users.

    Returns:
        List[User]: List of all users in the system
    """
    async with async_session() as db:
        try:
            stmt = (
                select(User)
                .options(selectinload(User.settings))
                .order_by(User.created_at)
            )
            result = await db.execute(stmt)
            users = result.scalars().all()
            return list(users)
        except Exception as e:
            typer.echo(f"❌ Error fetching users: {str(e)}", err=True)
            return []


async def _delete_all_orders_async() -> bool:
    """
    Async helper function to delete all orders.

    Returns:
        bool: True if successful, False otherwise
    """
    async with async_session() as db:
        try:
            # Get count before deletion
            count_stmt = select(Order)
            count_result = await db.execute(count_stmt)
            orders_count = len(list(count_result.scalars().all()))

            if orders_count == 0:
                typer.echo("ℹ️  No orders found to delete.")
                return True

            # Delete all orders
            delete_stmt = delete(Order)
            await db.execute(delete_stmt)
            await db.commit()

            typer.echo(f"✅ Successfully deleted {orders_count} orders.")
            return True

        except Exception as e:
            await db.rollback()
            typer.echo(f"❌ Error deleting orders: {str(e)}", err=True)
            return False


async def _nuke_database_async() -> bool:
    """
    Async helper function to completely nuke the database.
    WARNING: This will delete ALL data!

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        async with engine.begin() as conn:
            # Drop all tables
            await conn.run_sync(Base.metadata.drop_all)
            # Recreate all tables
            await conn.run_sync(Base.metadata.create_all)

        typer.echo("✅ Successfully nuked and recreated the database.")
        return True

    except Exception as e:
        typer.echo(f"❌ Error nuking database: {str(e)}", err=True)
        return False


async def _get_database_stats_async() -> dict:
    """
    Async helper function to get database statistics.

    Returns:
        dict: Database statistics
    """
    async with async_session() as db:
        try:
            stats = {}

            # Count users
            user_stmt = select(User)
            user_result = await db.execute(user_stmt)
            stats["users"] = len(list(user_result.scalars().all()))

            # Count orders
            order_stmt = select(Order)
            order_result = await db.execute(order_stmt)
            stats["orders"] = len(list(order_result.scalars().all()))

            # Count instruments
            instrument_stmt = select(Instrument)
            instrument_result = await db.execute(instrument_stmt)
            stats["instruments"] = len(list(instrument_result.scalars().all()))

            # Count logs
            log_stmt = select(Log)
            log_result = await db.execute(log_stmt)
            stats["logs"] = len(list(log_result.scalars().all()))

            return stats

        except Exception as e:
            typer.echo(f"❌ Error fetching database stats: {str(e)}", err=True)
            return {}


async def _clear_logs_async() -> bool:
    """
    Async helper function to clear all logs.

    Returns:
        bool: True if successful, False otherwise
    """
    async with async_session() as db:
        try:
            # Get count before deletion
            count_stmt = select(Log)
            count_result = await db.execute(count_stmt)
            logs_count = len(list(count_result.scalars().all()))

            if logs_count == 0:
                typer.echo("ℹ️  No logs found to clear.")
                return True

            # Delete all logs
            delete_stmt = delete(Log)
            await db.execute(delete_stmt)
            await db.commit()

            typer.echo(f"✅ Successfully cleared {logs_count} logs.")
            return True

        except Exception as e:
            await db.rollback()
            typer.echo(f"❌ Error clearing logs: {str(e)}", err=True)
            return False


@app.command(name="make-admin")
def make_admin(
    email: str = typer.Option(
        ..., prompt="User email", help="Email of the user to make admin"
    ),
) -> None:
    """
    Make a user an admin by updating their role.

    This command updates the specified user's role to ADMIN in the database.
    If the user is already an admin, it will inform you without making changes.

    Example:
        python -m app.commands make-admin --email user@example.com
    """

    typer.echo(f"🔄 Making user '{email}' an admin...")

    # Run the async function
    success = asyncio.run(_make_admin_async(email))

    if not success:
        raise typer.Exit(1)


@app.command(name="list-users")
def list_users() -> None:
    """
    List all users in the system with their details.

    Displays a formatted table of all users including their ID, name, email,
    role, and creation date.

    Example:
        python -m app.commands list-users
    """
    typer.echo("🔄 Fetching all users...")

    # Run the async function
    users = asyncio.run(_get_all_users_async())

    if not users:
        typer.echo("ℹ️  No users found in the system.")
        return

    typer.echo(f"\n📊 Found {len(users)} users:\n")

    # Print header
    typer.echo("=" * 120)
    typer.echo(f"{'ID':<36} {'Name':<25} {'Email':<30} {'Role':<10} {'Created':<19}")
    typer.echo("=" * 120)

    # Print user details
    for user in users:
        name = f"{user.first_name} {user.last_name}"
        created_str = user.created_at.strftime("%Y-%m-%d %H:%M:%S")
        typer.echo(
            f"{str(user.id):<36} {name:<25} {user.email:<30} {user.role.value:<10} {created_str:<19}"
        )

    typer.echo("=" * 120)


@app.command(name="delete-orders")
def delete_orders(
    confirm: bool = typer.Option(
        False, "--confirm", help="Confirm deletion of all orders without prompting"
    ),
) -> None:
    """
    Delete all orders from the system.

    WARNING: This will permanently delete ALL orders in the database.
    This action cannot be undone.

    Example:
        python -m app.commands delete-orders --confirm
    """
    if not confirm:
        typer.echo("⚠️  WARNING: This will delete ALL orders in the database!")
        typer.echo("This action cannot be undone.")

        confirmation = typer.confirm("Are you sure you want to continue?")
        if not confirmation:
            typer.echo("❌ Operation cancelled.")
            raise typer.Exit(0)

    typer.echo("🔄 Deleting all orders...")

    # Run the async function
    success = asyncio.run(_delete_all_orders_async())

    if not success:
        raise typer.Exit(1)


@app.command(name="nuke-db")
def nuke_database(
    confirm: bool = typer.Option(
        False, "--confirm", help="Confirm database nuke without prompting"
    ),
) -> None:
    """
    Completely nuke the database and recreate all tables.

    WARNING: This will permanently delete ALL data in the database including:
    - Users
    - Orders
    - Instruments
    - Logs
    - Settings
    - Everything else

    This action cannot be undone and will result in a completely fresh database.

    Example:
        python -m app.commands nuke-db --confirm
    """
    if not confirm:
        typer.echo("🚨 DANGER: This will completely destroy ALL data in the database!")
        typer.echo(
            "This includes users, orders, instruments, logs, settings, and everything else."
        )
        typer.echo("This action CANNOT be undone!")
        typer.echo("")

        confirmation = typer.confirm(
            "Are you absolutely sure you want to nuke the entire database?"
        )
        if not confirmation:
            typer.echo("❌ Operation cancelled.")
            raise typer.Exit(0)

        # Double confirmation for safety
        double_confirm = typer.confirm(
            "Type 'yes' to confirm you understand this will delete EVERYTHING"
        )
        if not double_confirm:
            typer.echo("❌ Operation cancelled.")
            raise typer.Exit(0)

    typer.echo("💥 Nuking database...")

    # Run the async function
    success = asyncio.run(_nuke_database_async())

    if not success:
        raise typer.Exit(1)


@app.command(name="db-stats")
def database_stats() -> None:
    """
    Display database statistics including record counts for all tables.

    Shows the current number of users, orders, instruments, and logs in the database.

    Example:
        python -m app.commands db-stats
    """
    typer.echo("🔄 Fetching database statistics...")

    # Run the async function
    stats = asyncio.run(_get_database_stats_async())

    if not stats:
        typer.echo("❌ Failed to fetch database statistics.")
        raise typer.Exit(1)

    typer.echo("\n📊 Database Statistics:")
    typer.echo("=" * 40)
    typer.echo(f"Users:       {stats.get('users', 0):,}")
    typer.echo(f"Orders:      {stats.get('orders', 0):,}")
    typer.echo(f"Instruments: {stats.get('instruments', 0):,}")
    typer.echo(f"Logs:        {stats.get('logs', 0):,}")
    typer.echo("=" * 40)


@app.command(name="clear-logs")
def clear_logs(
    confirm: bool = typer.Option(
        False, "--confirm", help="Confirm log clearing without prompting"
    ),
) -> None:
    """
    Clear all logs from the system.

    WARNING: This will permanently delete ALL logs in the database.
    This action cannot be undone.

    Example:
        python -m app.commands clear-logs --confirm
    """
    if not confirm:
        typer.echo("⚠️  WARNING: This will delete ALL logs in the database!")
        typer.echo("This action cannot be undone.")

        confirmation = typer.confirm("Are you sure you want to continue?")
        if not confirmation:
            typer.echo("❌ Operation cancelled.")
            raise typer.Exit(0)

    typer.echo("🔄 Clearing all logs...")

    # Run the async function
    success = asyncio.run(_clear_logs_async())

    if not success:
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
