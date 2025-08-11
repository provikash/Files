import uvloop
import asyncio
from pyrogram import idle
from bot import Bot
import logging

logger = logging.getLogger(__name__)

uvloop.install()

async def main():
    # Start the mother bot
    app = Bot()
    await app.start()
    
    # Initialize clone manager
    try:
        from clone_manager import clone_manager
        await clone_manager.start_all_clones()
        print("✅ Clone manager initialized")
    except ImportError:
        print("ℹ️ Clone manager not available")
    except Exception as e:
        print(f"⚠️ Clone manager error: {e}")
    
    await idle()
    await app.stop()

if __name__ == "__main__":
    asyncio.run(main())