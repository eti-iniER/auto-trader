import asyncio

import typer
from pydantic import EmailStr

from .db.crud import get_user_by_email
from .db.enums import UserRole
from .db.session import async_session

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


@app.command(name="make-admin")
def make_admin(
    email: str = typer.Option(
        ..., prompt="User email", help="Email of the user to make admin"
    )
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
    List all users in the system (placeholder command).

    This is a placeholder command to ensure proper subcommand structure.
    """
    typer.echo("This command is not yet implemented.")
    raise typer.Exit(1)


if __name__ == "__main__":
    app()
