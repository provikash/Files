# Cleaned & Refactored by @Mak0912 (TG)

from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatMemberStatus
from info import Config


async def handle_force_sub(client, message: Message):
    user = message.from_user
    not_joined = []
    joined = []
    buttons = []

    # Check if force subscription is enabled
    if not Config.FORCE_SUB_CHANNEL:
        return False

    # Use preloaded channel info from client.channel_info
    for ch in Config.FORCE_SUB_CHANNEL:
        try:
            member = await client.get_chat_member(ch, user.id)
            if member.status in (
                ChatMemberStatus.OWNER,
                ChatMemberStatus.ADMINISTRATOR,
                ChatMemberStatus.MEMBER,
            ):
                joined.append(ch)
            elif member.status == ChatMemberStatus.RESTRICTED:
                # Check if join requests are enabled and user has pending request
                if Config.JOIN_REQUEST_ENABLE:
                    # User is restricted but may have a pending join request
                    not_joined.append(ch)
                else:
                    not_joined.append(ch)
            else:
                not_joined.append(ch)
        except Exception:
            not_joined.append(ch)

    if not not_joined:
        return False

    # Create buttons for ALL force subscription channels
    for ch in Config.FORCE_SUB_CHANNEL:
        try:
            # Get channel info
            if hasattr(client, 'channel_info') and client.channel_info.get(ch):
                info = client.channel_info.get(ch)
            else:
                # Fallback: get channel info directly
                chat = await client.get_chat(ch)
                info = {
                    'title': chat.title,
                    'invite_link': chat.invite_link
                }
                
            url = info.get("invite_link")
            title = info.get("title", f"Channel {ch}")
            
            # Handle join request enabled channels
            if Config.JOIN_REQUEST_ENABLE and ch in not_joined:
                try:
                    # Create an invite link that requires admin approval
                    invite_link = await client.create_chat_invite_link(
                        ch,
                        creates_join_request=True,
                        name=f"Join Request for {user.first_name or user.id}"
                    )
                    url = invite_link.invite_link
                    print(f"DEBUG: Created join request link for channel {ch}: {url}")
                except Exception as e:
                    print(f"DEBUG: Failed to create join request link for {ch}: {e}")
                    # Fallback to regular invite link
                    if not url:
                        try:
                            url = await client.export_chat_invite_link(ch)
                        except:
                            url = f"https://t.me/c/{str(ch)[4:]}"
            else:
                # If no invite link, create one (regular invite)
                if not url:
                    try:
                        url = await client.export_chat_invite_link(ch)
                    except:
                        url = f"https://t.me/c/{str(ch)[4:]}"
                    
            # Ensure URL is valid and create button
            if url and url.strip():
                if ch in joined:
                    buttons.append([InlineKeyboardButton(f"✅ {title}", url=url)])
                elif Config.JOIN_REQUEST_ENABLE and ch in not_joined:
                    buttons.append([InlineKeyboardButton(f"🔔 Request to Join {title}", url=url)])
                else:
                    buttons.append([InlineKeyboardButton(f"📢 Join {title}", url=url)])
        except Exception as e:
            print(f"Error creating button for channel {ch}: {e}")
            # Create a fallback button
            buttons.append([InlineKeyboardButton(f"📢 Join Channel", url=f"https://t.me/c/{str(ch)[4:]}")])

    # Add retry button if start payload is present
    if hasattr(message, 'command') and len(message.command) > 1:
        payload = message.command[1]
        if client.username:
            buttons.append([
                InlineKeyboardButton("🔁 Try Again", url=f"https://t.me/{client.username}?start={payload}")
            ])

    # Build channel join status text
    joined_txt = ""
    for ch in Config.FORCE_SUB_CHANNEL:
        try:
            if hasattr(client, 'channel_info') and client.channel_info.get(ch):
                title = client.channel_info.get(ch).get("title", f"Channel {ch}")
            else:
                chat = await client.get_chat(ch)
                title = chat.title
        except:
            title = f"Channel {ch}"
            
        if ch in joined:
            joined_txt += f"✅ <b>{title}</b>\n"
        else:
            joined_txt += f"❌ <b>{title}</b>\n"

    # Format the force subscription message
    fsub_msg = Config.FORCE_MSG.format(
        first=user.first_name,
        last=user.last_name or "",
        username=f"@{user.username}" if user.username else "N/A",
        mention=user.mention,
        id=user.id
    )
    
    # Enhanced message with clear instructions
    final_message = f"{fsub_msg}\n\n<b>📋 Channel Join Status:</b>\n{joined_txt}\n"
    if not_joined:
        if Config.JOIN_REQUEST_ENABLE:
            final_message += f"\n🔽 <b>Click the buttons below to request to join the required channels:</b>\n"
            final_message += f"<i>⏳ Your request will be sent to admins for approval. You'll be able to use the bot once approved.</i>"
        else:
            final_message += f"\n🔽 <b>Click the buttons below to join the required channels:</b>"
    else:
        final_message += f"\n✅ <b>All channels joined! You can now use the bot.</b>"
    
    # Ensure we have buttons before creating markup
    if buttons:
        reply_markup = InlineKeyboardMarkup(buttons)
        print(f"DEBUG: Created {len(buttons)} buttons for force subscription")
    else:
        reply_markup = None
        print("DEBUG: No buttons created for force subscription")
    
    try:
        await message.reply(
            final_message,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
        return True
    except Exception as e:
        print(f"Error sending force subscription message: {e}")
        # Fallback without buttons
        await message.reply(
            final_message,
            disable_web_page_preview=True
        )
        return True
