
#!/usr/bin/env python3
"""
Standalone Clone Manager
This script manages multiple bot instances
"""

import asyncio
import json
import os
from pyrogram import Client
from info import Config

class CloneManager:
    def __init__(self):
        self.clones = {}
        self.config_file = "clones.json"
        self.load_clones()

    def load_clones(self):
        """Load clone configurations from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.clones = json.load(f)
                print(f"✅ Loaded {len(self.clones)} clone configurations")
            except Exception as e:
                print(f"❌ Error loading clones: {e}")
                self.clones = {}

    def save_clones(self):
        """Save clone configurations to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.clones, f, indent=2)
            print("✅ Clone configurations saved")
        except Exception as e:
            print(f"❌ Error saving clones: {e}")

    async def add_clone(self, bot_token: str, owner_id: int):
        """Add a new clone"""
        try:
            # Test the token
            test_client = Client(
                name=f"test_{bot_token[:10]}",
                api_id=Config.API_ID,
                api_hash=Config.API_HASH,
                bot_token=bot_token
            )
            
            await test_client.start()
            me = await test_client.get_me()
            
            clone_info = {
                'bot_id': me.id,
                'username': me.username,
                'first_name': me.first_name,
                'token': bot_token,
                'owner_id': owner_id,
                'running': False
            }
            
            await test_client.stop()
            
            # Add to clones
            self.clones[str(me.id)] = clone_info
            self.save_clones()
            
            print(f"✅ Added clone: @{me.username}")
            return True, clone_info
            
        except Exception as e:
            print(f"❌ Error adding clone: {e}")
            return False, str(e)

    async def start_clone(self, bot_id: str):
        """Start a specific clone"""
        if bot_id not in self.clones:
            return False, "Clone not found"
        
        try:
            clone_info = self.clones[bot_id]
            
            if clone_info.get('running', False):
                return False, "Clone is already running"
            
            # Create and start the clone
            clone_client = Client(
                name=f"clone_{bot_id}",
                api_id=Config.API_ID,
                api_hash=Config.API_HASH,
                bot_token=clone_info['token'],
                plugins=dict(root="bot/plugins")
            )
            
            await clone_client.start()
            clone_info['running'] = True
            clone_info['client'] = clone_client
            self.save_clones()
            
            print(f"✅ Started clone: @{clone_info['username']}")
            return True, f"Clone @{clone_info['username']} started successfully"
            
        except Exception as e:
            print(f"❌ Error starting clone {bot_id}: {e}")
            return False, str(e)

    async def stop_clone(self, bot_id: str):
        """Stop a specific clone"""
        if bot_id not in self.clones:
            return False, "Clone not found"
        
        try:
            clone_info = self.clones[bot_id]
            
            if not clone_info.get('running', False):
                return False, "Clone is not running"
            
            # Stop the clone
            if 'client' in clone_info:
                await clone_info['client'].stop()
                del clone_info['client']
            
            clone_info['running'] = False
            self.save_clones()
            
            print(f"✅ Stopped clone: @{clone_info['username']}")
            return True, f"Clone @{clone_info['username']} stopped successfully"
            
        except Exception as e:
            print(f"❌ Error stopping clone {bot_id}: {e}")
            return False, str(e)

    async def start_all_clones(self):
        """Start all configured clones"""
        print("🚀 Starting all clones...")
        
        tasks = []
        for bot_id in self.clones:
            if not self.clones[bot_id].get('running', False):
                tasks.append(self.start_clone(bot_id))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            print(f"✅ Started {len([r for r in results if r[0]])} clones")
        else:
            print("ℹ️ All clones are already running")

    def list_clones(self):
        """List all clones"""
        if not self.clones:
            print("📝 No clones configured")
            return
        
        print("🤖 **Configured Clones:**\n")
        for bot_id, info in self.clones.items():
            status = "🟢 Running" if info.get('running', False) else "🔴 Stopped"
            print(f"@{info['username']} ({bot_id}) - {status}")

# Global clone manager instance
clone_manager = CloneManager()

if __name__ == "__main__":
    # Example usage
    async def main():
        await clone_manager.start_all_clones()
        
        # Keep running
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            print("\n🛑 Shutting down clone manager...")
            for bot_id in list(clone_manager.clones.keys()):
                await clone_manager.stop_clone(bot_id)
    
    asyncio.run(main())
