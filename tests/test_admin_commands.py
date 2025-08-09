
import pytest
from unittest.mock import AsyncMock, patch
from bot.plugins.admin import (
    add_force_channel, remove_force_channel, list_force_channels,
    add_premium_user_cmd, remove_premium_user_cmd, list_premium_users
)

class TestAdminCommands:
    """Test admin command functionality"""
    
    @pytest.mark.asyncio
    async def test_admin_verification(self, mock_client, mock_message, test_config):
        """Test admin-only command access"""
        # Test non-admin access
        mock_message.from_user.id = 111222333  # Non-admin user
        mock_message.command = ["addforce", "-1001234567890"]
        
        await add_force_channel(mock_client, mock_message)
        mock_message.reply_text.assert_called_with(
            "❌ This command is only available to administrators."
        )

    @pytest.mark.asyncio
    async def test_add_force_channel_success(self, mock_client, mock_message, test_config, clean_database):
        """Test adding force subscription channel"""
        mock_message.from_user.id = 987654321  # Admin user
        mock_message.command = ["addforce", "-1001234567890"]
        
        # Mock channel access
        mock_chat = AsyncMock()
        mock_chat.title = "Test Channel"
        mock_chat.invite_link = "https://t.me/+test"
        mock_client.get_chat.return_value = mock_chat
        
        with patch('bot.plugins.admin.set_key') as mock_set_key:
            await add_force_channel(mock_client, mock_message)
            
            # Verify success message
            mock_message.reply_text.assert_called()
            call_args = mock_message.reply_text.call_args[0][0]
            assert "✅ Added force subscription channel" in call_args

    @pytest.mark.asyncio
    async def test_add_force_channel_invalid_id(self, mock_client, mock_message, test_config):
        """Test adding force channel with invalid ID"""
        mock_message.from_user.id = 987654321
        mock_message.command = ["addforce", "invalid_id"]
        
        await add_force_channel(mock_client, mock_message)
        mock_message.reply_text.assert_called_with(
            "❌ Invalid channel ID. Please provide a valid channel ID."
        )

    @pytest.mark.asyncio
    async def test_premium_user_management(self, mock_client, mock_message, test_config, clean_database):
        """Test premium user addition and removal"""
        mock_message.from_user.id = 987654321  # Admin user
        
        # Test adding premium user
        mock_message.command = ["addpremium", "123456789", "basic"]
        await add_premium_user_cmd(mock_client, mock_message)
        
        # Verify success message
        mock_message.reply_text.assert_called()
        call_args = mock_message.reply_text.call_args[0][0]
        assert "✅ Successfully added premium membership" in call_args
        
        # Test removing premium user
        mock_message.command = ["removepremium", "123456789"]
        await remove_premium_user_cmd(mock_client, mock_message)
        
        # Verify success message
        mock_message.reply_text.assert_called()
        call_args = mock_message.reply_text.call_args[0][0]
        assert "✅ Successfully removed premium membership" in call_args

    @pytest.mark.asyncio
    async def test_invalid_premium_plan(self, mock_client, mock_message, test_config):
        """Test adding premium with invalid plan"""
        mock_message.from_user.id = 987654321
        mock_message.command = ["addpremium", "123456789", "invalid_plan"]
        
        await add_premium_user_cmd(mock_client, mock_message)
        mock_message.reply_text.assert_called_with(
            "❌ Invalid plan. Available plans: basic, standard, premium, unlimited"
        )
