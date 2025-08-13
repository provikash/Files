import uvloop
import asyncio
from pyrogram import idle
from bot import Bot
import logging
import traceback

logger = logging.getLogger(__name__)

uvloop.install()

async def main():
    try:
        # Start the mother bot
        print("🚀 Starting Mother Bot...")
        app = Bot()
        await app.start()
        print("✅ Mother Bot started successfully!")
        
        # Initialize clone manager
        try:
            from clone_manager import clone_manager
            await clone_manager.start_all_clones()
            print("✅ Clone manager initialized")
        except ImportError:
            print("ℹ️ Clone manager not available")
        except Exception as e:
            print(f"⚠️ Clone manager error: {e}")
        
        print("🎉 All systems operational! Bot is ready to serve users.")
        await idle()
        
    except KeyboardInterrupt:
        print("🛑 Bot shutdown requested by user")
    except Exception as critical_error:
        print(f"💥 CRITICAL ERROR: {critical_error}")
        print(f"Traceback: {traceback.format_exc()}")
        print("❌ Bot failed to start properly. Please check the logs and restart.")
    finally:
        try:
            if 'app' in locals():
                await app.stop()
                print("✅ Bot stopped successfully")
        except Exception as stop_error:
            print(f"⚠️ Error during shutdown: {stop_error}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as startup_error:
        print(f"💥 STARTUP FAILURE: {startup_error}")
        print("🔄 Please restart the bot using /start command in Telegram")