
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from info import Config
from bot.database import add_premium_user, remove_premium, get_users_count
from bot.database.premium_db import get_all_premium_users
import os
from dotenv import set_key, load_dotenv

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
    """Show all admin commands"""
    help_text = """
🔧 **Complete Admin Control Panel**

**🏢 Channel Management:**
• `/addforce <channel_id>` - Add force subscription channel
• `/removeforce <channel_id>` - Remove force subscription channel  
• `/listforce` - List all force subscription channels
• `/addrequest <channel_id>` - Add request approval channel
• `/removerequest <channel_id>` - Remove request approval channel
• `/listrequest` - List all request channels

**🔗 Shortlink Configuration:**
• `/setshortlink <api_key> <url>` - Configure shortlink API
• `/shortlinkinfo` - View current shortlink settings

**👑 Premium Management:**
• `/addpremium <user_id> <plan>` - Add premium membership
• `/removepremium <user_id>` - Remove premium membership
• `/listpremium` - List all premium users

**📊 Statistics & Info:**
• `/stats` - Bot statistics
• `/users` - User count
• `/testadmin` - Test admin access

**📢 Communication:**
• `/broadcast <message>` - Broadcast to all users

**⚙️ Request Management:**
• `/approveuser <user_id> <channel_id>` - Approve join request
• `/pendingrequests` - View pending requests

**Plans:** basic, standard, premium, unlimited

**Examples:** 
`/addforce -1001234567890`
`/setshortlink your_api_key teraboxlinks.com`
`/addpremium 1420372797 basic`
    """
    await message.reply_text(help_text)

# Force Subscription Channel Management
@Client.on_message(filters.command("addforce") & filters.private)
@admin_only
async def add_force_channel(client: Client, message: Message):
    """Add force subscription channel"""
    if len(message.command) < 2:
        return await message.reply_text("❌ Usage: `/addforce <channel_id>`\nExample: `/addforce -1001234567890`")
    
    try:
        channel_id = int(message.command[1])
        
        # Test if bot can access the channel
        try:
            chat = await client.get_chat(channel_id)
            channel_title = chat.title or f"Channel {channel_id}"
        except:
            return await message.reply_text(f"❌ Cannot access channel {channel_id}. Make sure the bot is added to the channel.")
        
        # Update environment and config
        current_channels = set(Config.FORCE_SUB_CHANNEL)
        current_channels.add(channel_id)
        channel_list = " ".join(str(ch) for ch in current_channels)
        
        # Update .env file
        set_key(".env", "FORCE_SUB_CHANNEL", channel_list)
        Config.FORCE_SUB_CHANNEL = list(current_channels)
        
        # Update bot's channel info
        try:
            if not chat.invite_link:
                invite_link = await client.export_chat_invite_link(channel_id)
            else:
                invite_link = chat.invite_link
                
            client.channel_info[channel_id] = {
                'title': channel_title,
                'invite_link': invite_link
            }
        except:
            pass
        
        await message.reply_text(f"✅ Added force subscription channel: **{channel_title}** (`{channel_id}`)")
        
    except ValueError:
        await message.reply_text("❌ Invalid channel ID. Please provide a valid channel ID.")
    except Exception as e:
        await message.reply_text(f"❌ Error adding channel: {str(e)}")

@Client.on_message(filters.command("removeforce") & filters.private)
@admin_only
async def remove_force_channel(client: Client, message: Message):
    """Remove force subscription channel"""
    if len(message.command) < 2:
        return await message.reply_text("❌ Usage: `/removeforce <channel_id>`")
    
    try:
        channel_id = int(message.command[1])
        
        if channel_id not in Config.FORCE_SUB_CHANNEL:
            return await message.reply_text(f"❌ Channel {channel_id} is not in force subscription list.")
        
        # Update config
        current_channels = set(Config.FORCE_SUB_CHANNEL)
        current_channels.discard(channel_id)
        channel_list = " ".join(str(ch) for ch in current_channels)
        
        # Update .env file
        set_key(".env", "FORCE_SUB_CHANNEL", channel_list)
        Config.FORCE_SUB_CHANNEL = list(current_channels)
        
        # Remove from bot's channel info
        if channel_id in client.channel_info:
            del client.channel_info[channel_id]
        
        await message.reply_text(f"✅ Removed force subscription channel: `{channel_id}`")
        
    except ValueError:
        await message.reply_text("❌ Invalid channel ID.")
    except Exception as e:
        await message.reply_text(f"❌ Error removing channel: {str(e)}")

@Client.on_message(filters.command("listforce") & filters.private)
@admin_only
async def list_force_channels(client: Client, message: Message):
    """List all force subscription channels"""
    if not Config.FORCE_SUB_CHANNEL:
        return await message.reply_text("📋 No force subscription channels configured.")
    
    text = "📢 **Force Subscription Channels:**\n\n"
    for i, channel_id in enumerate(Config.FORCE_SUB_CHANNEL, 1):
        try:
            if channel_id in client.channel_info:
                title = client.channel_info[channel_id]['title']
            else:
                chat = await client.get_chat(channel_id)
                title = chat.title or f"Channel {channel_id}"
            
            text += f"{i}. **{title}**\n   ID: `{channel_id}`\n\n"
        except:
            text += f"{i}. **Unknown Channel**\n   ID: `{channel_id}`\n\n"
    
    await message.reply_text(text)

# Request Channel Management
@Client.on_message(filters.command("addrequest") & filters.private)
@admin_only
async def add_request_channel(client: Client, message: Message):
    """Add request approval channel"""
    if len(message.command) < 2:
        return await message.reply_text("❌ Usage: `/addrequest <channel_id>`\nExample: `/addrequest -1001234567890`")
    
    try:
        channel_id = int(message.command[1])
        
        # Test if bot can access the channel
        try:
            chat = await client.get_chat(channel_id)
            channel_title = chat.title or f"Channel {channel_id}"
        except:
            return await message.reply_text(f"❌ Cannot access channel {channel_id}. Make sure the bot is added to the channel.")
        
        # Update environment and config
        current_channels = set(getattr(Config, 'REQUEST_CHANNEL', []))
        current_channels.add(channel_id)
        channel_list = " ".join(str(ch) for ch in current_channels)
        
        # Update .env file
        set_key(".env", "REQUEST_CHANNEL", channel_list)
        Config.REQUEST_CHANNEL = list(current_channels)
        
        await message.reply_text(f"✅ Added request approval channel: **{channel_title}** (`{channel_id}`)")
        
    except ValueError:
        await message.reply_text("❌ Invalid channel ID. Please provide a valid channel ID.")
    except Exception as e:
        await message.reply_text(f"❌ Error adding request channel: {str(e)}")

@Client.on_message(filters.command("removerequest") & filters.private)
@admin_only
async def remove_request_channel(client: Client, message: Message):
    """Remove request approval channel"""
    if len(message.command) < 2:
        return await message.reply_text("❌ Usage: `/removerequest <channel_id>`")
    
    try:
        channel_id = int(message.command[1])
        
        current_channels = set(getattr(Config, 'REQUEST_CHANNEL', []))
        if channel_id not in current_channels:
            return await message.reply_text(f"❌ Channel {channel_id} is not in request approval list.")
        
        # Update config
        current_channels.discard(channel_id)
        channel_list = " ".join(str(ch) for ch in current_channels)
        
        # Update .env file
        set_key(".env", "REQUEST_CHANNEL", channel_list)
        Config.REQUEST_CHANNEL = list(current_channels)
        
        await message.reply_text(f"✅ Removed request approval channel: `{channel_id}`")
        
    except ValueError:
        await message.reply_text("❌ Invalid channel ID.")
    except Exception as e:
        await message.reply_text(f"❌ Error removing request channel: {str(e)}")

@Client.on_message(filters.command("listrequest") & filters.private)
@admin_only
async def list_request_channels(client: Client, message: Message):
    """List all request approval channels"""
    request_channels = getattr(Config, 'REQUEST_CHANNEL', [])
    if not request_channels:
        return await message.reply_text("📋 No request approval channels configured.")
    
    text = "🔔 **Request Approval Channels:**\n\n"
    for i, channel_id in enumerate(request_channels, 1):
        try:
            chat = await client.get_chat(channel_id)
            title = chat.title or f"Channel {channel_id}"
            text += f"{i}. **{title}**\n   ID: `{channel_id}`\n\n"
        except:
            text += f"{i}. **Unknown Channel**\n   ID: `{channel_id}`\n\n"
    
    await message.reply_text(text)

# Shortlink Management
@Client.on_message(filters.command("setshortlink") & filters.private)
@admin_only
async def set_shortlink(client: Client, message: Message):
    """Configure shortlink API and URL"""
    if len(message.command) < 3:
        return await message.reply_text("❌ Usage: `/setshortlink <api_key> <shortlink_url>`\nExample: `/setshortlink your_api_key teraboxlinks.com`")
    
    try:
        api_key = message.command[1]
        shortlink_url = message.command[2]
        
        # Add https:// if not present
        if not shortlink_url.startswith(('http://', 'https://')):
            shortlink_url = f"https://{shortlink_url}/"
        
        # Update .env file
        set_key(".env", "SHORTLINK_API", api_key)
        set_key(".env", "SHORTLINK_URL", shortlink_url)
        
        # Update config
        Config.SHORTLINK_API = api_key
        Config.SHORTLINK_URL = shortlink_url
        
        await message.reply_text(f"✅ Shortlink configuration updated:\n**API Key:** `{api_key}`\n**URL:** `{shortlink_url}`")
        
    except Exception as e:
        await message.reply_text(f"❌ Error updating shortlink configuration: {str(e)}")

@Client.on_message(filters.command("shortlinkinfo") & filters.private)
@admin_only
async def shortlink_info(client: Client, message: Message):
    """View current shortlink settings"""
    api_key = getattr(Config, 'SHORTLINK_API', 'Not set')
    shortlink_url = getattr(Config, 'SHORTLINK_URL', 'Not set')
    
    info_text = f"""
🔗 **Current Shortlink Configuration**

**API Key:** `{api_key}`
**Shortlink URL:** `{shortlink_url}`
**Verify Mode:** `{Config.VERIFY_MODE}`

Use `/setshortlink <api_key> <url>` to update configuration.
    """
    await message.reply_text(info_text)

# Existing premium and stats commands
@Client.on_message(filters.command("listpremium") & filters.private)
@admin_only
async def list_premium_users(client: Client, message: Message):
    """List all premium users"""
    try:
        premium_users = await get_all_premium_users()
        
        if not premium_users:
            return await message.reply_text("📋 No premium users found.")
        
        text = "👑 **Premium Users List:**\n\n"
        for i, user in enumerate(premium_users[:20], 1):
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
📢 **Force Sub Channels:** {len(Config.FORCE_SUB_CHANNEL)}
🔔 **Request Channels:** {len(getattr(Config, 'REQUEST_CHANNEL', []))}

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
