
import pytest
from datetime import datetime, timedelta
from bot.database.users import add_user, present_user, get_users_count
from bot.database.premium_db import add_premium_user, is_premium_user, get_premium_info, use_premium_token
from bot.database.verify_db import create_verification_token, verify_token
from bot.database.command_usage_db import get_user_command_count, increment_command_count, reset_command_count

class TestUserOperations:
    """Test user database operations"""
    
    @pytest.mark.asyncio
    async def test_add_user(self, clean_database):
        """Test adding a user"""
        user_id = 123456789
        
        # Test adding new user
        result = await add_user(user_id)
        assert result is True
        
        # Test user exists
        exists = await present_user(user_id)
        assert exists is True
        
        # Test adding existing user
        result = await add_user(user_id)
        assert result is False

    @pytest.mark.asyncio
    async def test_user_count(self, clean_database):
        """Test user count functionality"""
        initial_count = await get_users_count()
        
        # Add test users
        await add_user(123456789)
        await add_user(987654321)
        
        new_count = await get_users_count()
        assert new_count == initial_count + 2

class TestPremiumOperations:
    """Test premium user operations"""
    
    @pytest.mark.asyncio
    async def test_add_premium_user(self, clean_database):
        """Test adding premium user"""
        user_id = 123456789
        
        # Add premium user
        await add_premium_user(user_id, "basic", 50)
        
        # Check if user is premium
        is_premium = await is_premium_user(user_id)
        assert is_premium is True
        
        # Get premium info
        info = await get_premium_info(user_id)
        assert info is not None
        assert info['plan_type'] == "basic"
        assert info['tokens_remaining'] == 50

    @pytest.mark.asyncio
    async def test_unlimited_premium(self, clean_database):
        """Test unlimited premium user"""
        user_id = 123456789
        
        # Add unlimited premium
        await add_premium_user(user_id, "unlimited", -1)
        
        is_premium = await is_premium_user(user_id)
        assert is_premium is True
        
        # Use token shouldn't decrease count
        result = await use_premium_token(user_id)
        assert result is True
        
        info = await get_premium_info(user_id)
        assert info['tokens_remaining'] == -1

    @pytest.mark.asyncio
    async def test_token_based_premium(self, clean_database):
        """Test token-based premium functionality"""
        user_id = 123456789
        
        # Add premium with 3 tokens
        await add_premium_user(user_id, "basic", 3)
        
        # Use 3 tokens
        for i in range(3):
            result = await use_premium_token(user_id)
            assert result is True
        
        # Should fail on 4th attempt
        result = await use_premium_token(user_id)
        assert result is False
        
        # User should no longer be premium
        is_premium = await is_premium_user(user_id)
        assert is_premium is False

class TestCommandUsage:
    """Test command usage tracking"""
    
    @pytest.mark.asyncio
    async def test_command_counting(self, clean_database):
        """Test command count functionality"""
        user_id = 123456789
        
        # Initial count should be 0
        count = await get_user_command_count(user_id)
        assert count == 0
        
        # Increment 3 times
        for i in range(3):
            await increment_command_count(user_id)
            count = await get_user_command_count(user_id)
            assert count == i + 1
        
        # Reset count
        await reset_command_count(user_id)
        count = await get_user_command_count(user_id)
        assert count == 0

class TestVerificationSystem:
    """Test verification token system"""
    
    @pytest.mark.asyncio
    async def test_token_creation_and_verification(self, clean_database):
        """Test token creation and verification"""
        user_id = 123456789
        
        # Create token
        token = await create_verification_token(user_id)
        assert token is not None
        assert len(token) > 10
        
        # Verify valid token
        is_valid = await verify_token(user_id, token)
        assert is_valid is True
        
        # Verify invalid token
        is_valid = await verify_token(user_id, "invalid_token")
        assert is_valid is False
        
        # Verify with wrong user
        is_valid = await verify_token(987654321, token)
        assert is_valid is False
