"""Start Telegram Bot

Usage:
    python start_telegram_bot.py [--webhook WEBHOOK_URL] [--port PORT]

Examples:
    # Polling mode (recommended for development)
    python start_telegram_bot.py
    
    # Webhook mode (recommended for production)
    python start_telegram_bot.py --webhook https://yourdomain.com/telegram-webhook --port 8080
"""

import asyncio
import argparse
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.integrations.telegram_bot import HukukYZBot
from backend.database.mongodb import mongodb_client
from backend.core.cache import cache_manager


async def main():
    """Main function to start the bot"""
    parser = argparse.ArgumentParser(description="Start HukukYZ Telegram Bot")
    parser.add_argument("--webhook", type=str, help="Webhook URL for production")
    parser.add_argument("--port", type=int, default=8080, help="Webhook port")
    parser.add_argument("--token", type=str, help="Telegram Bot Token (or use TELEGRAM_BOT_TOKEN env)")
    
    args = parser.parse_args()
    
    # Get token
    token = args.token or os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ Error: Telegram Bot Token not provided!")
        print("Set TELEGRAM_BOT_TOKEN environment variable or use --token argument")
        sys.exit(1)
    
    print("🚀 HukukYZ Telegram Bot Starting...")
    print("=" * 60)
    
    # Initialize services
    try:
        print("📦 Connecting to MongoDB...")
        await mongodb_client.connect()
        print("✅ MongoDB connected")
        
        print("🔄 Connecting to Redis cache...")
        await cache_manager.connect()
        print("✅ Redis connected")
        
    except Exception as e:
        print(f"❌ Service initialization failed: {e}")
        sys.exit(1)
    
    # Create and start bot
    try:
        bot = HukukYZBot(token=token)
        
        if args.webhook:
            print(f"🌐 Starting in WEBHOOK mode")
            print(f"   URL: {args.webhook}")
            print(f"   Port: {args.port}")
            await bot.start_webhook(webhook_url=args.webhook, port=args.port)
        else:
            print(f"🔄 Starting in POLLING mode (development)")
            await bot.start_polling()
            
    except KeyboardInterrupt:
        print("\n⏹️  Bot stopped by user")
    except Exception as e:
        print(f"❌ Bot error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        print("🧹 Cleaning up...")
        await mongodb_client.close()
        await cache_manager.disconnect()
        print("✅ Cleanup complete")


if __name__ == "__main__":
    asyncio.run(main())
