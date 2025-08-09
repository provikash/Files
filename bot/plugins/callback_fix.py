
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
import traceback
from bot.database.premium_db import is_premium_user, get_premium_info
from bot.database.command_usage_db import check_command_limit, use_command
from bot.utils.subscription import handle_force_sub
from info import Config

@Client.on_callback_query(filters.regex("^buy_premium:"))
async def buy_premium_callback_fixed(client, query: CallbackQuery):
    """Handle premium purchase callbacks - Fixed version"""
    try:
        # Check force subscription first
        if await handle_force_sub(client, query.message):
            await query.answer()
            return

        plan_key = query.data.split(":")[1]

        # Premium plan configurations
        PREMIUM_PLANS = {
            "basic": {"name": "Basic Token Pack", "price": "29", "tokens": 50},
            "standard": {"name": "Standard Token Pack", "price": "79", "tokens": 150},
            "premium": {"name": "Premium Token Pack", "price": "149", "tokens": 300},
            "unlimited": {"name": "Unlimited Access", "price": "299", "tokens": -1}
        }

        plan = PREMIUM_PLANS.get(plan_key)
        if not plan:
            return await query.answer("❌ Invalid plan selected!", show_alert=True)

        # Payment instructions
        payment_text = (
            f"💎 **{plan['name']} Membership**\n"
            f"💰 **Price:** ₹{plan['price']}\n"
            f"⏱️ **Tokens:** {plan['tokens'] if plan['tokens'] != -1 else 'Unlimited'}\n\n"
            f"💳 **Payment Instructions:**\n"
            f"1. Pay ₹{plan['price']} to the following:\n"
            f"📱 **UPI ID:** `{getattr(Config, 'PAYMENT_UPI', 'Not Set')}`\n"
            f"🏦 **Phone Pay:** `{getattr(Config, 'PAYMENT_PHONE', 'Not Set')}`\n\n"
            f"2. Send screenshot to @{getattr(Config, 'ADMIN_USERNAME', 'admin')}\n"
            f"3. Include your User ID: `{query.from_user.id}`\n\n"
            f"⚠️ **Note:** Manual verification takes 5-10 minutes"
        )

        buttons = [
            [InlineKeyboardButton("📱 Contact Admin", url=f"https://t.me/{getattr(Config, 'ADMIN_USERNAME', 'admin')}")],
            [InlineKeyboardButton("🔙 Back", callback_data="show_premium_plans")]
        ]

        await query.edit_message_text(
            payment_text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    except Exception as e:
        print(f"ERROR in buy_premium_callback: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        await query.answer("❌ An error occurred. Please try again.", show_alert=True)

@Client.on_callback_query(filters.regex("^show_premium_plans$"))
async def show_premium_plans_fixed(client, query: CallbackQuery):
    """Show premium plans - Fixed version"""
    try:
        # Check force subscription first
        if await handle_force_sub(client, query.message):
            await query.answer()
            return

        user_id = query.from_user.id

        # Check if user is already premium
        if await is_premium_user(user_id):
            return await query.answer("✨ You're already a Premium Member!", show_alert=True)

        # Premium plan configurations
        PREMIUM_PLANS = {
            "basic": {"name": "Basic Token Pack", "price": "29", "tokens": 50},
            "standard": {"name": "Standard Token Pack", "price": "79", "tokens": 150},
            "premium": {"name": "Premium Token Pack", "price": "149", "tokens": 300},
            "unlimited": {"name": "Unlimited Access", "price": "299", "tokens": -1}
        }

        # Premium purchase buttons
        buttons = []
        for plan_key, plan_info in PREMIUM_PLANS.items():
            buttons.append([
                InlineKeyboardButton(
                    f"💎 {plan_info['name']} - ₹{plan_info['price']}",
                    callback_data=f"buy_premium:{plan_key}"
                )
            ])

        buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="close")])

        await query.edit_message_text(
            "💎 **Upgrade to Premium Membership**\n\n"
            "🎯 **Premium Benefits:**\n"
            "• 🚫 **No Ads** - Skip all verification steps\n"
            "• ⚡ **Instant Access** - Direct file downloads\n"
            "• 🔥 **Unlimited Downloads** - No restrictions\n"
            "• 👑 **Premium Support** - Priority assistance\n\n"
            "💰 **Choose Your Plan:**",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    except Exception as e:
        print(f"ERROR in show_premium_plans: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        await query.answer("❌ Error loading premium plans. Please try again.", show_alert=True)
