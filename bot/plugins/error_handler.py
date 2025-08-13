
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import RPCError
import traceback

@Client.on_message(filters.all & filters.private, group=-1)
async def global_error_handler(client: Client, message: Message):
    """Global error handler for all private messages"""
    # This handler runs with lowest priority (group=-1) to catch any unhandled errors
    pass

@Client.on_callback_query(group=-1)
async def global_callback_error_handler(client: Client, query: CallbackQuery):
    """Global error handler for all callback queries"""
    # This handler runs with lowest priority (group=-1) to catch any unhandled errors
    pass

# Exception handler for uncaught errors
async def handle_bot_error(client: Client, update, exception):
    """Handle uncaught bot errors"""
    try:
        error_msg = f"❌ **Bot Error Occurred!**\n\n"
        error_msg += f"🔄 Please send /start command to restart the bot properly."
        
        restart_button = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Restart Bot", url=f"https://t.me/{client.username}?start=")]
        ])
        
        if hasattr(update, 'from_user') and update.from_user:
            user_id = update.from_user.id
            try:
                await client.send_message(
                    user_id,
                    error_msg,
                    reply_markup=restart_button
                )
            except:
                pass
        
        print(f"CRITICAL ERROR: {exception}")
        print(f"Traceback: {traceback.format_exc()}")
        
    except Exception as e:
        print(f"ERROR in error handler: {e}")
