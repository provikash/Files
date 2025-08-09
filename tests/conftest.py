
import pytest
import asyncio
import os
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from info import Config
from bot.database.connection import db

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_client():
    """Mock Pyrogram Client"""
    client = AsyncMock()
    client.username = "testbot"
    client.get_chat = AsyncMock()
    client.send_message = AsyncMock()
    client.send_media_group = AsyncMock()
    client.get_messages = AsyncMock()
    client.export_chat_invite_link = AsyncMock(return_value="https://t.me/+test")
    return client

@pytest.fixture
def mock_message():
    """Mock Pyrogram Message"""
    message = MagicMock()
    message.from_user.id = 123456789
    message.from_user.first_name = "Test User"
    message.chat.id = 123456789
    message.command = []
    message.text = "/test"
    message.reply_text = AsyncMock()
    message.edit_text = AsyncMock()
    message.delete = AsyncMock()
    return message

@pytest.fixture
def mock_callback_query():
    """Mock Pyrogram CallbackQuery"""
    callback = MagicMock()
    callback.from_user.id = 123456789
    callback.from_user.first_name = "Test User"
    callback.data = "test_callback"
    callback.message = mock_message()
    callback.answer = AsyncMock()
    callback.edit_message_text = AsyncMock()
    return callback

@pytest.fixture
def test_config():
    """Test configuration"""
    original_values = {}
    
    # Store original values
    test_attrs = ['ADMINS', 'OWNER_ID', 'FORCE_SUB_CHANNEL', 'VERIFY_MODE']
    for attr in test_attrs:
        if hasattr(Config, attr):
            original_values[attr] = getattr(Config, attr)
    
    # Set test values
    Config.ADMINS = [987654321]
    Config.OWNER_ID = 987654321
    Config.FORCE_SUB_CHANNEL = [-1001234567890]
    Config.VERIFY_MODE = True
    
    yield Config
    
    # Restore original values
    for attr, value in original_values.items():
        setattr(Config, attr, value)

@pytest.fixture
async def clean_database():
    """Clean test data from database"""
    # Clean up test data before and after tests
    test_user_ids = [123456789, 987654321, 111222333]
    
    try:
        # Clean users
        await db['users'].delete_many({'_id': {'$in': test_user_ids}})
        # Clean premium users
        await db['premium_users'].delete_many({'_id': {'$in': test_user_ids}})
        # Clean command usage
        await db['command_usage'].delete_many({'user_id': {'$in': test_user_ids}})
        # Clean verification tokens
        await db['verification_tokens'].delete_many({'user_id': {'$in': test_user_ids}})
    except Exception as e:
        print(f"Database cleanup error: {e}")
    
    yield
    
    # Cleanup after test
    try:
        await db['users'].delete_many({'_id': {'$in': test_user_ids}})
        await db['premium_users'].delete_many({'_id': {'$in': test_user_ids}})
        await db['command_usage'].delete_many({'user_id': {'$in': test_user_ids}})
        await db['verification_tokens'].delete_many({'user_id': {'$in': test_user_ids}})
    except Exception as e:
        print(f"Database cleanup error: {e}")
