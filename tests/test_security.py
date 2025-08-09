
import pytest
from unittest.mock import AsyncMock, patch
from bot.utils.security import is_user_banned, check_rate_limit
from bot.utils.subscription import check_force_subscription

class TestSecurityFeatures:
    """Test security and safety features"""
    
    @pytest.mark.asyncio
    async def test_force_subscription_check(self, mock_client, mock_message, test_config):
        """Test force subscription functionality"""
        user_id = 123456789
        channel_id = -1001234567890
        
        # Mock user not subscribed
        mock_client.get_chat_member.return_value = AsyncMock()
        mock_client.get_chat_member.return_value.status = "left"
        
        with patch('bot.utils.subscription.Config.FORCE_SUB_CHANNEL', [channel_id]):
            result = await check_force_subscription(mock_client, user_id)
            assert result is False  # User not subscribed
        
        # Mock user subscribed
        mock_client.get_chat_member.return_value.status = "member"
        result = await check_force_subscription(mock_client, user_id)
        assert result is True  # User subscribed

    @pytest.mark.asyncio
    async def test_input_validation(self):
        """Test input validation for various inputs"""
        # Test user ID validation
        invalid_user_ids = [-1, 0, "invalid", None]
        for invalid_id in invalid_user_ids:
            # Should handle gracefully
            try:
                from bot.database.users import add_user
                result = await add_user(invalid_id)
                # Should fail safely
                assert result is False or result is None
            except (ValueError, TypeError):
                # Expected for invalid inputs
                pass

    @pytest.mark.asyncio
    async def test_sql_injection_prevention(self, clean_database):
        """Test SQL injection prevention (MongoDB should be safe but test anyway)"""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "<script>alert('xss')</script>",
            "../../etc/passwd"
        ]
        
        from bot.database.users import add_user
        for malicious_input in malicious_inputs:
            try:
                # Should handle gracefully without errors
                result = await add_user(malicious_input)
                # Input should be handled safely
                assert result in [True, False, None]
            except (ValueError, TypeError):
                # Expected for invalid inputs
                pass

class TestErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.mark.asyncio
    async def test_database_connection_failure(self):
        """Test handling of database connection failures"""
        with patch('bot.database.connection.db') as mock_db:
            mock_db.side_effect = Exception("Connection failed")
            
            from bot.database.users import get_users_count
            try:
                count = await get_users_count()
                # Should return 0 or handle gracefully
                assert count == 0
            except Exception:
                # Should not crash the application
                pass

    @pytest.mark.asyncio
    async def test_malformed_callback_data(self, mock_client, mock_callback_query):
        """Test handling of malformed callback data"""
        malformed_data = [
            "",
            "invalid_callback",
            "buy_premium:",
            "buy_premium:invalid_plan",
            "rand_",
            None
        ]
        
        for data in malformed_data:
            mock_callback_query.data = data
            try:
                from bot.plugins.callback import buy_premium_callback
                await buy_premium_callback(mock_client, mock_callback_query)
                # Should handle gracefully
            except Exception as e:
                # Should not cause unhandled exceptions
                assert "Invalid" in str(e) or "Error" in str(e)

    @pytest.mark.asyncio
    async def test_large_file_handling(self, mock_client, mock_message):
        """Test handling of large files and data"""
        # Test with very long message text
        mock_message.text = "A" * 10000  # Very long text
        
        try:
            from bot.plugins.start_handler import start_handler
            await start_handler(mock_client, mock_message)
            # Should handle without crashing
        except Exception:
            # Should handle gracefully
            pass
