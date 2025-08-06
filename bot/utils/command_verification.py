import asyncio
from datetime import datetime, timedelta
from bot.database import get_user_command_count, increment_command_count, is_verified, is_premium_user
from bot.database.premium_db import use_premium_token
from bot.database.command_usage_db import reset_command_count
from info import Config

# User locks to prevent race conditions
_user_locks = {}

async def check_command_limit(user_id: int) -> tuple[bool, int]:
    """
    Check if user has exceeded command limit
    Returns: (needs_verification, remaining_commands)
    """
    # Skip verification for admins, owner, and premium users
    if (user_id in Config.ADMINS or
        user_id == Config.OWNER_ID or
        await is_premium_user(user_id)):
        return False, -1  # -1 means unlimited

    command_count = await get_user_command_count(user_id)

    # Every user gets exactly 3 commands before needing verification
    max_commands = 3

    if command_count >= max_commands:
        return True, 0  # Need verification to get next 3 commands

    remaining = max_commands - command_count
    return False, remaining

async def reset_user_commands(user_id: int) -> bool:
    """Reset user command count - alias for reset_command_count"""
    try:
        await reset_command_count(user_id)
        return True
    except Exception:
        return False

async def use_command(user_id: int) -> bool:
    """
    Use a command for the user. Returns True if successful, False if limit reached.
    Thread-safe implementation to prevent race conditions.
    """
    try:
        # Skip limits for admins, owner, and premium users
        if (user_id in Config.ADMINS or
            user_id == Config.OWNER_ID or
            await is_premium_user(user_id)):
            return True

        # Get or create user-specific lock
        if user_id not in _user_locks:
            _user_locks[user_id] = asyncio.Lock()

        async with _user_locks[user_id]:

            # Get current command count
            current_count = await get_user_command_count(user_id)

            # Check if user has reached the limit (3 free commands)
            if current_count >= 3:
                return False

            # Increment command count atomically
            await increment_command_count(user_id)
            return True

    except Exception as e:
        print(f"Error in use_command: {e}")
        return False

async def reset_user_commands(user_id):
    """Reset user command count"""
    try:
        from bot.database.connection import db
        from info import Config
        collection = db[Config.COMMAND_USAGE_COLLECTION]
        await collection.delete_one({'user_id': user_id})
        return True
    except Exception as e:
        logger.error(f"Error resetting user commands: {e}")
        return False