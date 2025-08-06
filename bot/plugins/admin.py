
from pyrogram import Client, filters
from pyrogram.types import Message
from info import Config
from bot.database import add_premium_user, remove_premium, get_users_count
from bot.database.premium_db import get_all_premium_users

# Admin verification decorator
def admin_only(func):
    async def wrapper(client, message):
        user_id = message.from_user.id
        if user_id not in Config.ADMINS and user_id != Config.OWNER_ID:
            return await message.reply_text("❌ This command is only available to administrators.")
        return await func(client, message)
    return wrapper

@Client.on_message(filters.command("adminhelp") & filters.private)
@admin_only
async def admin_help(client: Client, message: Message):
    """Show admin commands"""
    help_text = """
🔧 **Admin Commands**

**Premium Management:**
• `/addpremium <user_id> <plan>` - Add premium membership
• `/removepremium <user_id>` - Remove premium membership
• `/listpremium` - List all premium users

**Stats:**
• `/stats` - Bot statistics
• `/users` - User count
• `/testadmin` - Test admin access

**Plans:** basic, standard, premium, unlimited

**Example:** `/addpremium 1420372797 basic`
    """
    await message.reply_text(help_text)

@Client.on_message(filters.command("listpremium") & filters.private)
@admin_only
async def list_premium_users(client: Client, message: Message):
    """List all premium users"""
    try:
        premium_users = await get_all_premium_users()
        
        if not premium_users:
            return await message.reply_text("📋 No premium users found.")
        
        text = "👑 **Premium Users List:**\n\n"
        for i, user in enumerate(premium_users[:20], 1):  # Limit to 20 users
            user_id = user.get('_id')
            plan = user.get('plan_type', 'Unknown')
            tokens = user.get('tokens_remaining', 0)
            
            if tokens == -1:
                token_info = "Unlimited"
            else:
                token_info = f"{tokens} tokens"
            
            text += f"{i}. **User:** `{user_id}`\n   **Plan:** {plan}\n   **Tokens:** {token_info}\n\n"
        
        if len(premium_users) > 20:
            text += f"... and {len(premium_users) - 20} more users"
        
        await message.reply_text(text)
    except Exception as e:
        await message.reply_text(f"❌ Error retrieving premium users: {e}")

@Client.on_message(filters.command("users") & filters.private)
@admin_only
async def users_count(client: Client, message: Message):
    """Get total user count"""
    try:
        total_users = await get_users_count()
        await message.reply_text(f"👥 **Total Users:** {total_users}")
    except Exception as e:
        await message.reply_text(f"❌ Error getting user count: {e}")

@Client.on_message(filters.command("stats") & filters.private)
@admin_only
async def bot_stats(client: Client, message: Message):
    """Get bot statistics"""
    try:
        total_users = await get_users_count()
        premium_users = await get_all_premium_users()
        premium_count = len(premium_users) if premium_users else 0
        
        premium_rate = (premium_count/total_users*100) if total_users > 0 else 0
        
        stats_text = f"""
📊 **Bot Statistics**

👥 **Total Users:** {total_users}
👑 **Premium Users:** {premium_count}
📈 **Premium Rate:** {premium_rate:.1f}%

🤖 **System Status:** Online ✅
        """
        await message.reply_text(stats_text)
    except Exception as e:
        await message.reply_text(f"❌ Error getting bot stats: {e}")

@Client.on_message(filters.command("testadmin") & filters.private)
@admin_only
async def test_admin(client: Client, message: Message):
    """Test admin functionality"""
    user_id = message.from_user.id
    await message.reply_text(f"✅ Admin verification successful!\n**Your ID:** {user_id}\n**Admin Status:** Confirmed")
