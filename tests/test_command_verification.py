
import pytest
from unittest.mock import patch
from bot.utils.command_verification import check_command_limit, use_command

class TestCommandVerification:
    """Test command verification and limiting logic"""
    
    @pytest.mark.asyncio
    async def test_admin_unlimited_access(self, test_config, clean_database):
        """Test that admins have unlimited access"""
        admin_id = 987654321  # From test_config
        
        needs_verification, remaining = await check_command_limit(admin_id)
        assert needs_verification is False
        assert remaining == -1  # Unlimited
        
        # Use command should always succeed for admin
        result = await use_command(admin_id)
        assert result is True

    @pytest.mark.asyncio
    async def test_premium_unlimited_access(self, clean_database):
        """Test premium users with unlimited access"""
        user_id = 123456789
        
        # Add unlimited premium
        from bot.database.premium_db import add_premium_user
        await add_premium_user(user_id, "unlimited", -1)
        
        needs_verification, remaining = await check_command_limit(user_id)
        assert needs_verification is False
        assert remaining == -1
        
        # Use command should always succeed
        result = await use_command(user_id)
        assert result is True

    @pytest.mark.asyncio
    async def test_premium_token_based(self, clean_database):
        """Test premium users with token-based access"""
        user_id = 123456789
        
        # Add premium with 3 tokens
        from bot.database.premium_db import add_premium_user
        await add_premium_user(user_id, "basic", 3)
        
        # Should have 3 tokens remaining
        needs_verification, remaining = await check_command_limit(user_id)
        assert needs_verification is False
        assert remaining == 3
        
        # Use all 3 tokens
        for i in range(3):
            result = await use_command(user_id)
            assert result is True
        
        # Should need verification after tokens exhausted
        needs_verification, remaining = await check_command_limit(user_id)
        assert needs_verification is True
        assert remaining == 0

    @pytest.mark.asyncio
    async def test_free_user_limit(self, clean_database):
        """Test free user command limits"""
        user_id = 123456789
        
        # Free user should have 3 commands
        needs_verification, remaining = await check_command_limit(user_id)
        assert needs_verification is False
        assert remaining == 3
        
        # Use all 3 commands
        for i in range(3):
            result = await use_command(user_id)
            assert result is True
            
            # Check remaining after each use
            needs_verification, remaining = await check_command_limit(user_id)
            if i < 2:  # Not the last command
                assert needs_verification is False
                assert remaining == 2 - i
        
        # Should need verification after 3 commands
        needs_verification, remaining = await check_command_limit(user_id)
        assert needs_verification is True
        assert remaining == 0
        
        # Further use should fail
        result = await use_command(user_id)
        assert result is False

    @pytest.mark.asyncio
    async def test_command_reset_after_verification(self, clean_database):
        """Test command reset after verification"""
        user_id = 123456789
        
        # Use all free commands
        for _ in range(3):
            await use_command(user_id)
        
        # Should need verification
        needs_verification, remaining = await check_command_limit(user_id)
        assert needs_verification is True
        
        # Reset commands (simulates verification)
        from bot.utils.command_verification import reset_user_commands
        await reset_user_commands(user_id)
        
        # Should have 3 commands again
        needs_verification, remaining = await check_command_limit(user_id)
        assert needs_verification is False
        assert remaining == 3
