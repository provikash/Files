import re
import os
from dotenv import load_dotenv

load_dotenv()

id_pattern = re.compile(r'^.\d+$')

class Config(object):
    _PROTECTED_ATTRS = frozenset(['ADMINS', 'OWNER_ID', 'API_ID', 'API_HASH', 'BOT_TOKEN'])

    def __setattr__(self, name, value):
        if name in self._PROTECTED_ATTRS and hasattr(self, name):
            raise AttributeError(f"Cannot modify {name} at runtime for security reasons")
        super().__setattr__(name, value)

    def __delattr__(self, name):
        if name in self._PROTECTED_ATTRS:
            raise AttributeError(f"Cannot delete {name} for security reasons")
        super().__delattr__(name)

    # Bot Configuration - Load from environment
    API_ID = os.environ.get("API_ID")
    API_HASH = os.environ.get("API_HASH")
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    BOT_WORKERS = int(os.environ.get("BOT_WORKERS", "4"))

    # Validate required environment variables
    if not API_ID or not API_HASH or not BOT_TOKEN:
        raise ValueError("Missing required environment variables: API_ID, API_HASH, or BOT_TOKEN")

    # Convert API_ID to int after validation
    API_ID = int(API_ID)

    # Webhook settings
    WEB_MODE = os.environ.get("WEB_MODE", "False").lower() in ("true", "1", "yes")
    PORT = int(os.environ.get("PORT", "5000"))
    HOST = os.environ.get("HOST", "0.0.0.0")

    # Channel Configuration - Load from environment
    CHANNEL_ID = os.environ.get("CHANNEL_ID")
    INDEX_CHANNEL_ID = os.environ.get("INDEX_CHANNEL_ID")
    OWNER_ID = os.environ.get("OWNER_ID")

    # Validate and convert channel/owner IDs
    if not CHANNEL_ID or not INDEX_CHANNEL_ID or not OWNER_ID:
        raise ValueError("Missing required environment variables: CHANNEL_ID, INDEX_CHANNEL_ID, or OWNER_ID")

    CHANNEL_ID = int(CHANNEL_ID)
    INDEX_CHANNEL_ID = int(INDEX_CHANNEL_ID)
    OWNER_ID = int(OWNER_ID)

    # Database - Load from environment
    DATABASE_URL = os.environ.get("DATABASE_URL")
    DATABASE_NAME = os.environ.get("DATABASE_NAME", "Cluster0")

    # Force subscription (normal invite links)
    FORCE_SUB_CHANNEL = list(set(int(ch) for ch in os.environ.get("FORCE_SUB_CHANNEL", "").split() if id_pattern.fullmatch(ch)))

    # Request channels (admin approval required)
    REQUEST_CHANNEL = list(set(int(ch) for ch in os.environ.get("REQUEST_CHANNEL", "").split() if id_pattern.fullmatch(ch)))
    JOIN_REQUEST_ENABLE = os.environ.get("JOIN_REQUEST_ENABLED", "False").lower() in ("true", "1", "yes")

    # Messages - Load from environment
    START_PIC = os.environ.get("START_PIC", "")
    START_MSG = os.environ.get("START_MESSAGE", "👋 Hello {mention},\n\nThis bot helps you store private files in a secure channel and generate special access links for sharing. 🔐📁\n\n Only admins can upload files and generate links. Just send the file here to get started.")
    FORCE_MSG = os.environ.get("FORCE_SUB_MESSAGE", "👋 Hello {mention}, \n\n <b>You need to join our updates channel before using this bot.</b>\n\n 📢 Please join the required channel, then try again.")
    CUSTOM_CAPTION = os.environ.get("CUSTOM_CAPTION", None)

    # ✅ Secure ADMINS - Load from environment as immutable tuple
    admins = os.environ.get("ADMINS", "").split()
    _admin_list = list(set(
        [int(x) for x in admins if x.isdigit()] + [OWNER_ID]
    ))
    ADMINS = tuple(_admin_list)  # Immutable tuple prevents runtime modification

    # Security Configuration - Load from environment
    PROTECT_CONTENT = os.environ.get("PROTECT_CONTENT", "False") == "True"
    DISABLE_CHANNEL_BUTTON = os.environ.get("DISABLE_CHANNEL_BUTTON", "False") == "True"

    # Auto Delete Configuration - Load from environment
    AUTO_DELETE_TIME = int(os.environ.get("AUTO_DELETE_TIME", "600"))
    AUTO_DELETE_MSG = os.environ.get("AUTO_DELETE_MSG", "This file will be automatically deleted in {time}.")
    AUTO_DEL_SUCCESS_MSG = os.environ.get("AUTO_DEL_SUCCESS_MSG", "✅ File deleted successfully.")

    # Token Verification (Shortlink) - Load from environment
    VERIFY_MODE = os.environ.get("VERIFY_MODE", "True").lower() in ("true", "1", "yes")
    SHORTLINK_API = os.environ.get("SHORTLINK_API")
    SHORTLINK_URL = os.environ.get("SHORTLINK_URL", "https://teraboxlinks.com/")
    TUTORIAL = os.environ.get("TUTORIAL","https://t.me/alfhamovies/13")

    # Bot Messages - Load from environment
    BOT_STATS_TEXT = os.environ.get("BOT_STATS_TEXT", "<b>BOT UPTIME</b>\n{uptime}")
    USER_REPLY_TEXT = os.environ.get("USER_REPLY_TEXT", "❌ I'm a bot — please don't DM me!")

    # Premium Settings - Load from environment
    PREMIUM_ENABLED = os.environ.get("PREMIUM_ENABLED", "True").lower() in ("true", "1", "yes")
    PAYMENT_UPI = os.environ.get("PAYMENT_UPI", "your_upi_id@paytm")
    PAYMENT_PHONE = os.environ.get("PAYMENT_PHONE", "+919876543210")
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")