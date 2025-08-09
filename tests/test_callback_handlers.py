
import pytest
from unittest.mock import AsyncMock, patch
from bot.plugins.callback import (
    show_premium_callback, my_stats_callback, get_token_callback,
    buy_premium_callback, execute_rand_callback
)

class TestCallbackHandlers:
    """Test callback handler functionality"""
    
    @pytest.mark.asyncio
    async def test_premium_callback_already_premium(self, mock_client, mock_callback_query, clean_database):
        """Test premium callback when user is already premium"""
        # Add user as premium
        from bot.database.premium_db import add_premium_user
        await add_premium_user(123456789, "basic", 50)
        
        await show_premium_callback(mock_client, mock_callback_query)
        mock_callback_query.answer.assert_called_with(
            "✨ You're already a Premium Member!", show_alert=True
        )

    @pytest.mark.asyncio
    async def test_premium_callback_show_plans(self, mock_client, mock_callback_query, clean_database):
        """Test premium callback shows plans for non-premium user"""
        with patch('bot.plugins.callback.handle_force_sub', return_value=False):
            await show_premium_callback(mock_client, mock_callback_query)
            mock_callback_query.edit_message_text.assert_called()
            
            # Check if plans are shown
            call_args = mock_callback_query.edit_message_text.call_args[0][0]
            assert "💎 **Upgrade to Premium Membership**" in call_args

    @pytest.mark.asyncio
    async def test_buy_premium_callback(self, mock_client, mock_callback_query, test_config):
        """Test buy premium callback"""
        mock_callback_query.data = "buy_premium:basic"
        
        with patch('bot.plugins.callback.handle_force_sub', return_value=False):
            await buy_premium_callback(mock_client, mock_callback_query)
            mock_callback_query.edit_message_text.assert_called()
            
            call_args = mock_callback_query.edit_message_text.call_args[0][0]
            assert "💎 **Basic Token Pack Membership**" in call_args

    @pytest.mark.asyncio
    async def test_get_token_callback_no_verification_needed(self, mock_client, mock_callback_query, clean_database):
        """Test get token callback when verification not needed"""
        # User has remaining commands
        with patch('bot.plugins.callback.handle_force_sub', return_value=False), \
             patch('bot.utils.command_verification.check_command_limit', return_value=(False, 2)):
            
            await get_token_callback(mock_client, mock_callback_query)
            mock_callback_query.edit_message_text.assert_called()
            
            call_args = mock_callback_query.edit_message_text.call_args[0][0]
            assert "You still have 2 commands remaining" in call_args

    @pytest.mark.asyncio
    async def test_my_stats_callback(self, mock_client, mock_callback_query, clean_database):
        """Test my stats callback"""
        with patch('bot.plugins.callback.handle_force_sub', return_value=False), \
             patch('bot.database.get_command_stats') as mock_stats, \
             patch('bot.utils.command_verification.check_command_limit', return_value=(False, 2)):
            
            mock_stats.return_value = {
                'command_count': 5,
                'last_command_at': None,
                'last_reset': None
            }
            
            await my_stats_callback(mock_client, mock_callback_query)
            mock_callback_query.edit_message_text.assert_called()
            
            call_args = mock_callback_query.edit_message_text.call_args[0][0]
            assert "📊 **Your Command Usage Stats**" in call_args

class TestCommandVerification:
    """Test command verification system"""
    
    @pytest.mark.asyncio
    async def test_execute_rand_verification_required(self, mock_client, mock_callback_query, clean_database):
        """Test random command when verification is required"""
        with patch('bot.plugins.callback.handle_force_sub', return_value=False), \
             patch('bot.utils.command_verification.check_command_limit', return_value=(True, 0)):
            
            await execute_rand_callback(mock_client, mock_callback_query)
            mock_callback_query.edit_message_text.assert_called()
            
            call_args = mock_callback_query.edit_message_text.call_args[0][0]
            assert "🔐 **Verification Required!**" in call_args

    @pytest.mark.asyncio
    async def test_execute_rand_success(self, mock_client, mock_callback_query, clean_database):
        """Test successful random command execution"""
        with patch('bot.plugins.callback.handle_force_sub', return_value=False), \
             patch('bot.utils.command_verification.check_command_limit', return_value=(False, 2)), \
             patch('bot.utils.command_verification.use_command', return_value=True), \
             patch('bot.plugins.search.handle_random_files') as mock_random:
            
            await execute_rand_callback(mock_client, mock_callback_query)
            mock_callback_query.answer.assert_called_with("Getting random files...", show_alert=False)
            mock_random.assert_called_once()
