import sys, asyncio
from datetime import datetime
from pyrogram import Client
from logger import LOGGER
from info import Config
from bot.utils import schedule_manager

ascii_art = """
████████╗██╗░░██╗███████╗  ██████╗░░██████╗  ██████╗░░█████╗░████████╗░██████╗
╚══██╔══╝██║░░██║██╔════╝  ██╔══██╗██╔════╝  ██╔══██╗██╔══██╗╚══██╔══╝██╔════╝
░░░██║░░░███████║█████╗░░  ██████╔╝╚█████╗░  ██████╦╝██║░░██║░░░██║░░░╚█████╗░
░░░██║░░░██╔══██║██╔══╝░░  ██╔═══╝░░╚═══██╗  ██╔══██╗██║░░██║░░░██║░░░░╚═══██╗
░░░██║░░░██║░░██║███████╗  ██║░░░░░██████╔╝  ██████╦╝╚█████╔╝░░░██║░░░██████╔╝
░░░╚═╝░░░╚═╝░░╚═╝╚══════╝  ╚═╝░░░░░╚═════╝░  ╚═════╝░░╚════╝░░░░╚═╝░░░╚═════╝░
"""

class Bot(Client):
    def __init__(self):
        super().__init__(
            name="PS-LinkVault",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,            
            plugins=dict(root="bot/plugins"),
            workers=Config.BOT_WORKERS,
            bot_token=Config.BOT_TOKEN
        )
        
        self.log = LOGGER
        self.username = None

    async def start(self):
        await super().start()
        me = await self.get_me()
        self.username = me.username
        self.mention = me.mention
        self.uptime = datetime.now()             
        self.channel_info = {}
        
        # Load force subscription channel info
        for channel_id in Config.FORCE_SUB_CHANNEL:
            try:
                chat = await self.get_chat(channel_id)
                title = chat.title
                link = chat.invite_link
        
                if not link:
                    link = await self.export_chat_invite_link(channel_id)
                    
                self.channel_info[channel_id] = {"title": title, "invite_link": link}
                print(f"✅ Loaded force channel info: {title} - {link}")
            except Exception as e:
                print(f"❌ Error loading force channel {channel_id}: {e}")

        # Load request channel info
        request_channels = getattr(Config, 'REQUEST_CHANNEL', [])
        for channel_id in request_channels:
            try:
                chat = await self.get_chat(channel_id)
                title = chat.title
                
                self.channel_info[channel_id] = {"title": title, "invite_link": None}
                print(f"✅ Loaded request channel info: {title}")
            except Exception as e:
                print(f"❌ Error loading request channel {channel_id}: {e}")

        if True:  # Placeholder for the rest of the method
            chat = await self.get_chat(channel_id)
                    link = chat.invite_link or link
                
                self.channel_info[channel_id] = {
                    "title": title,
                    "invite_link": link
                }
                print(f"✅ Loaded channel info: {title} - {link}")
                
            except Exception as e:
                print(f"❌ Failed to load channel {channel_id}: {e}")
                # Store minimal info for fallback
                self.channel_info[channel_id] = {
                    "title": f"Channel {channel_id}",
                    "invite_link": f"https://t.me/c/{str(channel_id)[4:]}"
                }
                
            except Exception as e:
                self.log(__name__).warning(f"Could not get info for channel {channel_id}: {e}")
                continue
        
        # Initialize database channel
        try:
            db_channel = await self.get_chat(Config.CHANNEL_ID)
            self.db_channel = db_channel
            test = await self.send_message(chat_id=db_channel.id, text="Test Message")
            await test.delete()
        except Exception as e:
            self.log(__name__).warning(e)
            self.log(__name__).warning(f"Make Sure bot is Admin in DB Channel, and Double check the CHANNEL_ID Value, Current Value {Config.CHANNEL_ID}")
            self.log(__name__).info("\nBot Stopped. Join https://t.me/ps_discuss for support")
            sys.exit()

        print(ascii_art)
        await asyncio.sleep(1.5)
        self.log(__name__).info(f"Bot Running..!\n\nCreated by \nhttps://t.me/ps_updates")
        print("""Welcome to File Sharing Bot""")

        await schedule_manager.start()
        asyncio.create_task(schedule_manager.restore_pending_deletes(self))
        
        if Config.WEB_MODE:
            from web import start_webserver
            asyncio.create_task(start_webserver(self, Config.PORT))
       
    async def stop(self, *args):
        await super().stop()
        self.log(__name__).info("Bot stopped.")
