# Cleaned & Refactored by @Mak0912 (TG)

import asyncio
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from pyrogram.errors import FloodWait

from info import Config
from bot.utils import handle_force_sub, decode, get_messages, get_readable_time, schedule_manager
from bot.database import add_user, present_user, is_verified, validate_token_and_verify, is_premium_user, increment_access_count

# ──────────────────────────────────────────────────────────────

@Client.on_message(filters.command('start') & filters.private)
async def start_handler(client: Client, message: Message):
    user = message.from_user
    user_id = user.id

    if not await present_user(user_id):
        await add_user(user_id)

    if await handle_force_sub(client, message):
        return

    command = message.command

    # Handle verification tokens
    if len(command) > 1 and command[1].startswith('verify-'):
        try:
            parts = command[1].split('-')
            if len(parts) >= 3:
                user_id_from_link = int(parts[1])
                token = '-'.join(parts[2:])  # Join remaining parts in case token contains hyphens

                print(f"DEBUG: Verification attempt - User ID: {user_id_from_link}, Token: {token[:8]}...")

                if user_id_from_link == message.from_user.id:
                    from bot.database.verify_db import validate_token_and_verify
                    if await validate_token_and_verify(user_id_from_link, token):
                        await message.reply_text("✅ Verification successful! You now have 3 fresh commands.")
                        return
                    else:
                        print(f"DEBUG: Token validation failed for user {user_id_from_link}")
                        await message.reply_text("❌ Invalid or expired token. Please use /token to generate a new one.")
                        return
                else:
                    await message.reply_text("❌ This token is not for your account.")
                    return
        except (ValueError, IndexError) as e:
            print(f"DEBUG: Token parsing error: {e}")
            await message.reply_text("❌ Invalid token format.")
            return

    # Handle deep links if parameters exist
    if len(command) > 1 and not command[1].startswith('verify-'):
        try:
            decoded = decode(command[1])
            parts = decoded.split("-")
        except Exception:
            # If decode fails, show start message
            parts = None
            
        if parts:
            try:
                if len(parts) == 3:
                    start_id = int(int(parts[1]) / abs(client.db_channel.id))
                    end_id = int(int(parts[2]) / abs(client.db_channel.id))
                    ids = range(start_id, end_id + 1) if start_id <= end_id else list(range(start_id, end_id - 1, -1))
                elif len(parts) == 2:
                    ids = [int(int(parts[1]) / abs(client.db_channel.id))]
                else:
                    parts = None
            except Exception:
                parts = None
    else:
        parts = None

    # Process file links if parts exist
    if parts:
        # ✅ Check verification only if required (skip for premium users)
        if Config.VERIFY_MODE and (user_id not in Config.ADMINS and user_id != Config.OWNER_ID):
            # Skip verification for premium users
            if not await is_premium_user(user_id) and not await is_verified(user_id):
                buttons = [
                    [InlineKeyboardButton("🔐 Get Access Token", url=f"https://t.me/{client.username}?start=")],
                    [InlineKeyboardButton("💎 Remove Ads - Buy Premium", callback_data="show_premium_plans")]
                ]
                return await message.reply_text(
                    f"🔐 You're not verified!\nPlease verify yourself first using /token.\n\n💡 **Or upgrade to Premium** for instant ad-free access!",
                    reply_markup=InlineKeyboardMarkup(buttons),
                    disable_web_page_preview=True
                )

        wait_msg = await message.reply("Processing... Please wait.")

        try:
            messages = await get_messages(client, ids)
        except Exception:
            return await wait_msg.edit("❌ Error while fetching messages!")

        await wait_msg.delete()

        to_delete = []
        for msg in messages:
            caption = ""
            if Config.CUSTOM_CAPTION and msg.document:
                caption = Config.CUSTOM_CAPTION.format(
                    previouscaption=msg.caption.html if msg.caption else "",
                    filename=msg.document.file_name
                )
            else:
                caption = msg.caption.html if msg.caption else ""

            markup = msg.reply_markup if Config.DISABLE_CHANNEL_BUTTON else None

            try:
                sent = await msg.copy(
                    chat_id=user_id,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=markup,
                    protect_content=Config.PROTECT_CONTENT
                )
                if Config.AUTO_DELETE_TIME:
                    to_delete.append(sent)
                await asyncio.sleep(0.5)
            except FloodWait as e:
                await asyncio.sleep(e.value)
            except Exception as e:
                client.log(__name__).info(f"Copy error: {e}")

        if to_delete:
            files_to_delete = [msg.id for msg in to_delete if msg is not None]
            delete_at = Config.AUTO_DELETE_TIME

            warning = await client.send_message(user_id, Config.AUTO_DELETE_MSG.format(time=get_readable_time(Config.AUTO_DELETE_TIME)))
            if warning:
                files_to_delete.append(warning.id)

            await schedule_manager.schedule_delete(
                client=client,
                chat_id=message.chat.id,
                message_ids=files_to_delete,
                delete_n_seconds=delete_at,
                base64_file_link=command[1],
            )
    else:
        # Start Message / No Params
        # Only show buttons if force subscription is not active
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🎲 Get Random Files", callback_data="execute_rand"),
                InlineKeyboardButton("🔥 Popular", callback_data="rand_popular")
            ],
            [
                InlineKeyboardButton("😊 About Me", callback_data="about")
            ],
            [
                InlineKeyboardButton("💎 Premium", callback_data="show_premium_plans"),
                InlineKeyboardButton("🔒 Close", callback_data="close")
            ]
        ])
        # Check remaining commands for non-premium users
        from bot.utils.command_verification import check_command_limit
        needs_verification, remaining = await check_command_limit(user_id)

        command_status = ""
        if remaining == -1:  # Unlimited (premium/admin)
            command_status = "\n\n🔥 **Unlimited Access** - No command limits!"
        elif remaining > 0:
            command_status = f"\n\n🆓 **Free Commands Remaining:** {remaining}/3"
        else:
            command_status = "\n\n⚠️ **Command Limit Reached** - Verify to get 3 more free commands!"

        caption = Config.START_MSG + f"""

✨ **Available Command:**
🎲 `/rand` - Get 5 random media files instantly!{command_status}"""

        caption = caption.format(
            first=message.from_user.first_name,
            last=message.from_user.last_name,
            username="@" + message.from_user.username if message.from_user.username else None,
            mention=message.from_user.mention,
            id=user_id
        )

        if Config.START_PIC:
            await message.reply_photo(photo=Config.START_PIC, caption=caption, reply_markup=buttons, quote=True)
        else:
            await message.reply_text(text=caption, reply_markup=buttons, disable_web_page_preview=True, quote=True)

# ──────────────────────────────────────────────────────────────

@Client.on_message(filters.private & filters.text & ~filters.command(['start', 'token', 'rand', 'recent', 'popular']) & ~filters.regex(r"^(🎲 Random|🆕 Recent Added|🔥 Most Popular|💎 Buy Premium)$"))
async def handle_useless_messages(client: Client, message: Message):
    """Handle any useless/random text messages with synchronized keyboards"""
    user = message.from_user

    # Check force subscription first
    if await handle_force_sub(client, message):
        return

    # Create synchronized custom keyboard that matches inline buttons
    custom_keyboard = ReplyKeyboardMarkup([
        [
            KeyboardButton("🎲 Random"),
            KeyboardButton("🆕 Recent Added")
        ],
        [
            KeyboardButton("🔥 Most Popular"),
            KeyboardButton("💎 Buy Premium")
        ]
    ], resize_keyboard=True, one_time_keyboard=False)

    # Create inline buttons that match the custom keyboard functionality
    inline_buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎲 Random Files", callback_data="execute_rand"),
            InlineKeyboardButton("🆕 Recent Files", callback_data="rand_recent")
        ],
        [
            InlineKeyboardButton("🔥 Popular Files", callback_data="rand_popular"),
            InlineKeyboardButton("💎 Premium Plans", callback_data="show_premium_plans")
        ],
        [
            InlineKeyboardButton("😊 About", callback_data="about"),
            InlineKeyboardButton("🔒 Close", callback_data="close")
        ]
    ])

    await message.reply_text(
        f"👋 Hi {user.first_name}!\n\n"
        f"🤖 **Please use the buttons below to navigate:**\n\n"
        f"🎲 **Random** - Get 5 random media files instantly\n"
        f"🆕 **Recent Added** - Latest uploaded files\n"
        f"🔥 **Most Popular** - Most accessed files\n"
        f"💎 **Buy Premium** - Unlimited access without ads\n\n"
        f"💡 **Use either keyboard or inline buttons!**",
        reply_markup=custom_keyboard
    )

    # Send inline buttons as alternative option
    await message.reply_text(
        "🚀 **Or use these quick buttons:**",
        reply_markup=inline_buttons
    )