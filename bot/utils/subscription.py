# Cleaned & Refactored by @Mak0912 (TG)

from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatMemberStatus
from info import Config


async def handle_force_sub(client, message: Message):
    user = message.from_user
    not_joined = []
    joined = []
    buttons = []

    # Use preloaded channel info from client.channels_info
    for ch in Config.FORCE_SUB_CHANNEL:
        try:
            member = await client.get_chat_member(ch, user.id)
            if member.status in (
                ChatMemberStatus.OWNER,
                ChatMemberStatus.ADMINISTRATOR,
                ChatMemberStatus.MEMBER,
            ):
                joined.append(ch)
            else:
                not_joined.append(ch)
        except Exception:
            not_joined.append(ch)

    if not not_joined:
        return False

    # Build buttons with proper validation
    for ch in not_joined:
        try:
            # Get channel info with fallback
            info = getattr(client, 'channel_info', {}).get(ch, {})
            
            # Try to get channel info directly if not in cache
            if not info:
                try:
                    chat = await client.get_chat(ch)
                    title = chat.title or "Channel"
                    url = chat.invite_link
                except Exception:
                    title = "Channel"
                    url = None
            else:
                title = info.get("title", "Channel")
                url = info.get("invite_link")
            
            # Only add button if we have a valid URL
            if url and url.startswith(('https://', 'http://')):
                # Ensure title is not empty and properly formatted
                if not title or not title.strip():
                    title = "Channel"
                buttons.append([InlineKeyboardButton(f"📢 {title[:30]}", url=url)])
        except Exception as e:
            print(f"Error processing channel {ch}: {e}")
            continue

    # Retry button if start payload present
    if len(message.command) > 1 and hasattr(client, 'username') and client.username:
        payload = message.command[1]
        try:
            buttons.append([
                InlineKeyboardButton("🔁 Try Again", url=f"https://t.me/{client.username}?start={payload}")
            ])
        except Exception as e:
            print(f"Error adding retry button: {e}")

    # If no valid buttons, create a simple message without buttons
    if not buttons:
        fsub_msg = Config.FORCE_MSG.format(
            first=user.first_name or "",
            last=user.last_name or "",
            username=f"@{user.username}" if user.username else "N/A",
            mention=user.mention,
            id=user.id
        )
        
        await message.reply(
            f"{fsub_msg}\n\n<b>Please join the required channels and try again.</b>",
            disable_web_page_preview=True
        )
        return True

    # Build channel join status text
    joined_txt = ""
    for ch in Config.FORCE_SUB_CHANNEL:
        try:
            info = getattr(client, 'channel_info', {}).get(ch, {})
            title = info.get("title", "Channel") if info else "Channel"
            if ch in joined:
                joined_txt += f"✅ <b>{title}</b>\n"
            else:
                joined_txt += f"❌ <b>{title}</b>\n"
        except Exception:
            joined_txt += f"❌ <b>Channel</b>\n"

    fsub_msg = Config.FORCE_MSG.format(
        first=user.first_name or "",
        last=user.last_name or "",
        username=f"@{user.username}" if user.username else "N/A",
        mention=user.mention,
        id=user.id
    )
    
    try:
        await message.reply(
            f"{fsub_msg}\n\n<b>Channel Join Status:</b>\n{joined_txt}",
            reply_markup=InlineKeyboardMarkup(buttons) if buttons else None,
            disable_web_page_preview=True
        )
    except Exception as e:
        print(f"Error sending force sub message: {e}")
        # Fallback without buttons
        await message.reply(
            f"{fsub_msg}\n\n<b>Please join the required channels and try again.</b>",
            disable_web_page_preview=True
        )
    
    return True
