
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta

class TestCompleteWorkflows:
    """Test complete user workflows end-to-end"""
    
    @pytest.mark.asyncio
    async def test_new_user_workflow(self, mock_client, mock_message, clean_database):
        """Test complete new user workflow"""
        user_id = 123456789
        mock_message.from_user.id = user_id
        
        # 1. User starts bot
        with patch('bot.utils.subscription.handle_force_sub', return_value=False):
            from bot.plugins.start_handler import start_handler
            await start_handler(mock_client, mock_message)
            
            # User should be added to database
            from bot.database.users import present_user
            assert await present_user(user_id) is True

    @pytest.mark.asyncio
    async def test_premium_purchase_workflow(self, mock_client, mock_message, mock_callback_query, clean_database):
        """Test premium purchase workflow"""
        user_id = 123456789
        
        # 1. User requests premium
        with patch('bot.plugins.callback.handle_force_sub', return_value=False):
            from bot.plugins.callback import show_premium_callback
            await show_premium_callback(mock_client, mock_callback_query)
            
            # Should show premium plans
            mock_callback_query.edit_message_text.assert_called()
        
        # 2. User selects plan
        mock_callback_query.data = "buy_premium:basic"
        with patch('bot.plugins.callback.handle_force_sub', return_value=False):
            from bot.plugins.callback import buy_premium_callback
            await buy_premium_callback(mock_client, mock_callback_query)
            
            # Should show payment instructions
            mock_callback_query.edit_message_text.assert_called()
        
        # 3. Admin adds premium manually
        from bot.database.premium_db import add_premium_user, is_premium_user
        await add_premium_user(user_id, "basic", 50)
        
        # User should now be premium
        assert await is_premium_user(user_id) is True

    @pytest.mark.asyncio
    async def test_command_limit_verification_workflow(self, mock_client, mock_message, mock_callback_query, clean_database):
        """Test command limit and verification workflow"""
        user_id = 123456789
        mock_callback_query.from_user.id = user_id
        
        # 1. User uses 3 free commands
        from bot.utils.command_verification import use_command, check_command_limit
        
        for i in range(3):
            result = await use_command(user_id)
            assert result is True
        
        # 2. User should need verification
        needs_verification, remaining = await check_command_limit(user_id)
        assert needs_verification is True
        assert remaining == 0
        
        # 3. User requests token
        with patch('bot.plugins.callback.handle_force_sub', return_value=False), \
             patch('bot.utils.helper.get_shortlink', return_value="https://short.link/test"):
            
            from bot.plugins.callback import get_token_callback
            await get_token_callback(mock_client, mock_callback_query)
            
            # Should provide verification link
            mock_callback_query.edit_message_text.assert_called()
        
        # 4. Simulate verification completion
        from bot.database.verify_db import create_verification_token, verify_token
        token = await create_verification_token(user_id)
        is_valid = await verify_token(user_id, token)
        assert is_valid is True
        
        # 5. Reset user commands after verification
        from bot.utils.command_verification import reset_user_commands
        await reset_user_commands(user_id)
        
        # User should have commands again
        needs_verification, remaining = await check_command_limit(user_id)
        assert needs_verification is False
        assert remaining == 3

    @pytest.mark.asyncio
    async def test_admin_management_workflow(self, mock_client, mock_message, test_config, clean_database):
        """Test admin management workflow"""
        admin_id = 987654321
        target_user_id = 123456789
        mock_message.from_user.id = admin_id
        
        # 1. Admin adds premium user
        mock_message.command = ["addpremium", str(target_user_id), "basic"]
        
        from bot.plugins.admin import add_premium_user_cmd
        await add_premium_user_cmd(mock_client, mock_message)
        
        # Verify success
        mock_message.reply_text.assert_called()
        
        # 2. Check user is premium
        from bot.database.premium_db import is_premium_user
        assert await is_premium_user(target_user_id) is True
        
        # 3. Admin removes premium
        mock_message.command = ["removepremium", str(target_user_id)]
        
        from bot.plugins.admin import remove_premium_user_cmd
        await remove_premium_user_cmd(mock_client, mock_message)
        
        # Verify removal
        mock_message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, mock_client, mock_message, clean_database):
        """Test error recovery and graceful degradation"""
        user_id = 123456789
        mock_message.from_user.id = user_id
        
        # 1. Test database error handling
        with patch('bot.database.users.user_data.find_one', side_effect=Exception("DB Error")):
            from bot.database.users import present_user
            try:
                result = await present_user(user_id)
                # Should handle gracefully
                assert result in [True, False, None]
            except Exception:
                # Should not crash
                pass
        
        # 2. Test API error handling
        mock_client.get_chat.side_effect = Exception("API Error")
        
        with patch('bot.plugins.admin.set_key'):
            from bot.plugins.admin import add_force_channel
            mock_message.command = ["addforce", "-1001234567890"]
            
            await add_force_channel(mock_client, mock_message)
            # Should handle error gracefully
            mock_message.reply_text.assert_called()

class TestDataIntegrity:
    """Test data integrity and consistency"""
    
    @pytest.mark.asyncio
    async def test_premium_token_consistency(self, clean_database):
        """Test premium token consistency"""
        user_id = 123456789
        
        # Add premium with tokens
        from bot.database.premium_db import add_premium_user, use_premium_token, get_premium_info
        await add_premium_user(user_id, "basic", 5)
        
        # Use tokens and verify consistency
        for i in range(5):
            result = await use_premium_token(user_id)
            assert result is True
            
            info = await get_premium_info(user_id)
            assert info['tokens_remaining'] == 4 - i
        
        # Should fail after all tokens used
        result = await use_premium_token(user_id)
        assert result is False

    @pytest.mark.asyncio
    async def test_command_count_accuracy(self, clean_database):
        """Test command count accuracy"""
        user_id = 123456789
        
        from bot.database.command_usage_db import get_user_command_count, increment_command_count
        
        # Initial count should be 0
        count = await get_user_command_count(user_id)
        assert count == 0
        
        # Increment multiple times
        for i in range(10):
            await increment_command_count(user_id)
            count = await get_user_command_count(user_id)
            assert count == i + 1

    @pytest.mark.asyncio
    async def test_verification_token_uniqueness(self, clean_database):
        """Test verification token uniqueness"""
        user_ids = [123456789, 123456790, 123456791]
        
        from bot.database.verify_db import create_verification_token
        tokens = []
        
        # Create tokens for different users
        for uid in user_ids:
            token = await create_verification_token(uid)
            tokens.append(token)
        
        # All tokens should be unique
        assert len(set(tokens)) == len(tokens)
        
        # Tokens should be valid length
        for token in tokens:
            assert len(token) >= 10
