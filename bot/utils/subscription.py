
# Cleaned & Refactored by @Mak0912 (TG)

from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatMemberStatus
from info import Config


async def handle_force_sub(client, message: Message):
    user = message.from_user
    not_joined_force = []
    not_joined_request = []
    joined = []
    buttons = []

    # Check if any subscription channels are configured
    force_channels = getattr(Config, 'FORCE_SUB_CHANNEL', [])
    request_channels = getattr(Config, 'REQUEST_CHANNEL', [])
    all_channels = force_channels + request_channels
    
    if not all_channels:
        return False

    # Check force subscription channels (normal invite links)
    for ch in force_channels:
        try:
            member = await client.get_chat_member(ch, user.id)
            if member.status in (
                ChatMemberStatus.OWNER,
                ChatMemberStatus.ADMINISTRATOR,
                ChatMemberStatus.MEMBER,
            ):
                joined.append(ch)
            else:
                not_joined_force.append(ch)
        except Exception:
            not_joined_force.append(ch)

    # Check request channels (admin approval required)
    for ch in request_channels:
        try:
            member = await client.get_chat_member(ch, user.id)
            if member.status in (
                ChatMemberStatus.OWNER,
                ChatMemberStatus.ADMINISTRATOR,
                ChatMemberStatus.MEMBER,
            ):
                joined.append(ch)
            elif member.status == ChatMemberStatus.RESTRICTED:
                # User has pending join request
                joined.append(ch)
            else:
                not_joined_request.append(ch)
        except Exception:
            not_joined_request.append(ch)

    # If all channels are joined, return False (no force sub needed)
    if not not_joined_force and not not_joined_request:
        return False

    # Create buttons for force subscription channels (normal invite)
    for ch in force_channels:
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
                else:
                    buttons.append([InlineKeyboardButton(f"📢 Join {title}", url=url)])
        except Exception as e:
            print(f"Error creating button for force channel {ch}: {e}")
            # Create a fallback button
            buttons.append([InlineKeyboardButton(f"📢 Join Channel", url=f"https://t.me/c/{str(ch)[4:]}")])

    # Create buttons for request channels (admin approval required)
    for ch in request_channels:
        try:
            # Get channel info
            try:
                chat = await client.get_chat(ch)
                title = chat.title or f"Channel {ch}"
            except:
                title = f"Channel {ch}"
            
            if ch in joined:
                buttons.append([InlineKeyboardButton(f"✅ {title}", url=f"https://t.me/c/{str(ch)[4:]}")])
            elif Config.JOIN_REQUEST_ENABLE:
                try:
                    # Create an invite link that requires admin approval
                    invite_link = await client.create_chat_invite_link(
                        ch,
                        creates_join_request=True,
                        name=f"Join Request for {user.first_name or user.id}"
                    )
                    url = invite_link.invite_link
                    print(f"DEBUG: Created join request link for channel {ch}: {url}")
                    buttons.append([InlineKeyboardButton(f"🔔 Request to Join {title}", url=url)])
                except Exception as e:
                    print(f"DEBUG: Failed to create join request link for {ch}: {e}")
                    # Fallback to regular link
                    try:
                        url = await client.export_chat_invite_link(ch)
                        buttons.append([InlineKeyboardButton(f"📢 Join {title}", url=url)])
                    except:
                        buttons.append([InlineKeyboardButton(f"📢 Join {title}", url=f"https://t.me/c/{str(ch)[4:]}")])
            else:
                # Regular invite link for request channels when JOIN_REQUEST_ENABLE is false
                try:
                    url = await client.export_chat_invite_link(ch)
                    buttons.append([InlineKeyboardButton(f"📢 Join {title}", url=url)])
                except:
                    buttons.append([InlineKeyboardButton(f"📢 Join {title}", url=f"https://t.me/c/{str(ch)[4:]}")])
        except Exception as e:
            print(f"Error creating button for request channel {ch}: {e}")

    # Add retry button if start payload is present
    if hasattr(message, 'command') and len(message.command) > 1:
        payload = message.command[1]
        if client.username:
            buttons.append([
                InlineKeyboardButton("🔁 Try Again", url=f"https://t.me/{client.username}?start={payload}")
            ])

    # Build channel join status text
    joined_txt = ""
    
    # Show force subscription channels
    for ch in force_channels:
        try:
            if hasattr(client, 'channel_info') and client.channel_info.get(ch):
                title = client.channel_info.get(ch).get("title", f"Channel {ch}")
            else:
                chat = await client.get_chat(ch)
                title = chat.title
        except:
            title = f"Channel {ch}"
            
        if ch in joined:
            joined_txt += f"✅ <b>{title}</b> (Force Sub)\n"
        else:
            joined_txt += f"❌ <b>{title}</b> (Force Sub)\n"
    
    # Show request channels
    for ch in request_channels:
        try:
            chat = await client.get_chat(ch)
            title = chat.title or f"Channel {ch}"
        except:
            title = f"Channel {ch}"
            
        if ch in joined:
            joined_txt += f"✅ <b>{title}</b> (Request)\n"
        else:
            joined_txt += f"🔔 <b>{title}</b> (Request)\n"

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
    
    if not_joined_force or not_joined_request:
        final_message += f"\n🔽 <b>Instructions:</b>\n"
        if not_joined_force:
            final_message += f"📢 <b>Force Sub:</b> Click to join directly\n"
        if not_joined_request and Config.JOIN_REQUEST_ENABLE:
            final_message += f"🔔 <b>Request:</b> Click to send join request (admin approval required)\n"
            final_message += f"<i>⏳ Your request will be sent to admins for approval.</i>\n"
    else:
        final_message += f"\n✅ <b>All channels joined! You can now use the bot.</b>"
    
    # Ensure we have buttons before creating markup
    if buttons:
        reply_markup = InlineKeyboardMarkup(buttons)
        print(f"DEBUG: Created {len(buttons)} buttons for subscription")
    else:
        reply_markup = None
        print("DEBUG: No buttons created for subscription")
    
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
