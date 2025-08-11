import uvloop
import asyncio
from pyrogram import idle
from bot import Bot
import logging

logger = logging.getLogger(__name__)

uvloop.install()

async def main():
    app = Bot()
    await app.start()

    # Start the scheduler
    try:
        from bot.utils.scheduler import schedule_manager
        await schedule_manager.start()
        logger.info("Scheduler started successfully")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
        import traceback
        traceback.print_exc()

    await idle()
    await app.stop()

if __name__ == "__main__":
    asyncio.run(main())