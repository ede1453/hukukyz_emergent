"""Telegram Bot for HukukYZ

Bot Commands:
- /start - Başlangıç mesajı
- /help - Yardım
- /ask <soru> - Hukuki soru sor
- /history - Son sorularım
- /clear - Geçmişi temizle
"""

import logging
from typing import Optional, Dict, List
from datetime import datetime
import asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

from backend.agents.workflow_optimized import execute_workflow
from backend.database.mongodb import mongodb_client

logger = logging.getLogger(__name__)


class HukukYZBot:
    """Telegram Bot for HukukYZ Legal Assistant"""
    
    def __init__(self, token: str):
        self.token = token
        self.app = None
        
        # Bot info
        self.bot_username = "HukukYZ_bot"
        
        # User settings cache (user_id -> settings)
        self.user_settings = {}
        self.welcome_message = """
🏛️ **HukukYZ - Hukuki Asistan Bot**

Merhaba! Ben HukukYZ, Türk hukuku konusunda size yardımcı olacak yapay zeka asistanınızım.

📚 **Kullanabileceğiniz Komutlar:**
/ask - Hukuki soru sorun
/history - Son sorularınızı görün
/clear - Geçmişinizi temizleyin
/deprecated - Eski versiyonları dahil et/hariç tut
/help - Yardım menüsü

💡 **Örnek Sorular:**
• Anonim şirket nasıl kurulur?
• TTK m.11 ne diyor?
• Borçlu ödeme yapmazsa ne olur?

Doğrudan mesaj yazarak da soru sorabilirsiniz!
        """
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        user_id = str(user.id)
        
        logger.info(f"User {user_id} started bot")
        
        # Create inline keyboard
        keyboard = [
            [InlineKeyboardButton("📝 Soru Sor", callback_data="ask")],
            [InlineKeyboardButton("📚 Yardım", callback_data="help")],
            [InlineKeyboardButton("📊 Hakkında", callback_data="about")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            self.welcome_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
📖 **HukukYZ Yardım**

**Komutlar:**
/start - Başlangıç
/ask <soru> - Soru sor
/history - Geçmişi gör
/clear - Geçmişi temizle
/help - Bu mesaj

**Kullanım:**
Doğrudan mesaj yazabilir veya /ask komutuyla soru sorabilirsiniz.

Örnek:
```
/ask Anonim şirket nasıl kurulur?
```

veya doğrudan:
```
Limited şirket nedir?
```

**Desteklenen Alanlar:**
• Ticaret Hukuku (TTK)
• Borçlar Hukuku (TBK)
• İcra İflas Hukuku (İİK)
• Medeni Hukuk (TMK)
• Tüketici Hakları (TKHK)
• Hukuk Muhakemeleri (HMK)
        """
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def ask_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /ask command"""
        user = update.effective_user
        user_id = str(user.id)
        
        # Get question from command
        question = " ".join(context.args)
        
        if not question:
            await update.message.reply_text(
                "❓ Lütfen bir soru yazın.\n\nÖrnek: /ask Anonim şirket nasıl kurulur?"
            )
            return
        
        await self.process_question(update, question, user_id)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages (questions)"""
        user = update.effective_user
        user_id = str(user.id)
        question = update.message.text
        
        if not question or question.startswith('/'):
            return
        
        await self.process_question(update, question, user_id)
    
    async def process_question(self, update: Update, question: str, user_id: str):
        """Process user question"""
        try:
            # Send "typing" action
            await update.message.chat.send_action("typing")
            
            # Send processing message
            processing_msg = await update.message.reply_text(
                "🔍 Sorgunuz işleniyor...\n⏳ Lütfen bekleyin..."
            )
            
            logger.info(f"Processing question from {user_id}: {question[:100]}")
            
            # Get user settings (include_deprecated)
            include_deprecated = await self.get_user_setting(user_id, "include_deprecated", False)
            
            # Execute workflow
            result = await execute_workflow(
                query=question,
                user_id=user_id,
                session_id=f"telegram_{user_id}",
                include_deprecated=include_deprecated
            )
            
            # Get answer
            answer = result.get("final_answer", result.get("answer", "Üzgünüm, cevap oluşturulamadı."))
            confidence = result.get("confidence", 0.0)
            citations = result.get("citations", [])
            
            # Format response
            response = f"📖 **Cevap:**\n\n{answer}\n\n"
            
            # Add confidence
            confidence_emoji = "🟢" if confidence > 0.7 else "🟡" if confidence > 0.4 else "🔴"
            response += f"{confidence_emoji} Güven: {int(confidence * 100)}%\n\n"
            
            # Add citations
            if citations:
                response += "📚 **Kaynaklar:**\n"
                for i, citation in enumerate(citations[:3], 1):
                    source = citation.get("source", "Bilinmiyor")
                    law_name = citation.get("law_name", "")
                    if law_name:
                        response += f"{i}. {source} ({law_name})\n"
                    else:
                        response += f"{i}. {source}\n"
            
            # Delete processing message
            await processing_msg.delete()
            
            # Send answer (split if too long)
            if len(response) > 4096:
                # Telegram message limit
                parts = [response[i:i+4000] for i in range(0, len(response), 4000)]
                for part in parts:
                    await update.message.reply_text(part, parse_mode='Markdown')
            else:
                await update.message.reply_text(response, parse_mode='Markdown')
            
            # Save to history
            await self.save_to_history(user_id, question, answer)
            
            logger.info(f"Question answered for {user_id} (confidence: {confidence:.2f})")
            
        except Exception as e:
            logger.error(f"Error processing question: {e}", exc_info=True)
            await update.message.reply_text(
                "❌ Üzgünüm, sorgunuzu işlerken bir hata oluştu. Lütfen tekrar deneyin."
            )
    
    async def history_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /history command"""
        user = update.effective_user
        user_id = str(user.id)
        
        try:
            # Get history from MongoDB
            db = mongodb_client.get_database()
            history = await db.telegram_history.find(
                {"user_id": user_id}
            ).sort("timestamp", -1).limit(5).to_list(5)
            
            if not history:
                await update.message.reply_text("📭 Henüz soru geçmişiniz yok.")
                return
            
            response = "📜 **Son Sorularınız:**\n\n"
            for i, item in enumerate(history, 1):
                question = item.get("question", "")
                timestamp = item.get("timestamp", "")
                response += f"{i}. {question[:100]}...\n"
                response += f"   🕐 {timestamp}\n\n"
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error getting history: {e}")
            await update.message.reply_text("❌ Geçmiş alınırken hata oluştu.")
    
    async def clear_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clear command"""
        user = update.effective_user
        user_id = str(user.id)
        
        try:
            # Clear history
            db = mongodb_client.db
            result = await db.telegram_history.delete_many({"user_id": user_id})
            
            await update.message.reply_text(
                f"✅ {result.deleted_count} adet soru geçmişiniz temizlendi."
            )
            
        except Exception as e:
            logger.error(f"Error clearing history: {e}")
            await update.message.reply_text("❌ Geçmiş temizlenirken hata oluştu.")
    
    async def deprecated_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /deprecated command"""
        user = update.effective_user
        user_id = str(user.id)
        
        try:
            # Check if user wants to toggle or just see status
            if context.args:
                action = context.args[0].lower()
                
                if action in ['on', 'açık', '1', 'evet', 'yes']:
                    await self.set_user_setting(user_id, "include_deprecated", True)
                    await update.message.reply_text(
                        "✅ **Eski Versiyonlar Aktif**\n\n"
                        "Artık aramalar eski/iptal edilmiş belge versiyonlarını da içerecek.\n\n"
                        "❗ Not: Bu, güncel olmayan bilgiler içerebilir."
                    )
                elif action in ['off', 'kapalı', '0', 'hayır', 'no']:
                    await self.set_user_setting(user_id, "include_deprecated", False)
                    await update.message.reply_text(
                        "✅ **Eski Versiyonlar Kapalı**\n\n"
                        "Aramalar sadece güncel belgeleri içerecek."
                    )
                else:
                    await update.message.reply_text(
                        "❓ Geçersiz parametre.\n\n"
                        "Kullanım:\n"
                        "`/deprecated on` - Eski versiyonları dahil et\n"
                        "`/deprecated off` - Sadece güncel belgeler",
                        parse_mode='Markdown'
                    )
            else:
                # Show current status
                current = await self.get_user_setting(user_id, "include_deprecated", False)
                status = "Açık ✅" if current else "Kapalı ❌"
                
                await update.message.reply_text(
                    f"📋 **Eski Versiyonlar:** {status}\n\n"
                    "Değiştirmek için:\n"
                    "`/deprecated on` veya `/deprecated off`",
                    parse_mode='Markdown'
                )
                
        except Exception as e:
            logger.error(f"Error in deprecated command: {e}")
            await update.message.reply_text("❌ Ayar değiştirilirken hata oluştu.")
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "ask":
            await query.message.reply_text(
                "💬 Hukuki sorunuzu yazın:\n\nÖrnek: Anonim şirket nasıl kurulur?"
            )
        elif query.data == "help":
            await self.help_command(update, context)
        elif query.data == "about":
            about_text = """
ℹ️ **HukukYZ Hakkında**

HukukYZ, yapay zeka destekli bir Türk hukuku asistanıdır.

**Özellikler:**
✅ 8 hukuk dalında uzman
✅ 2000+ hukuki belge
✅ Madde referansları
✅ Yargıtay içtihatları
✅ 7/24 erişilebilir

**Teknoloji:**
🤖 GPT-4 Powered
🔍 Advanced RAG
📊 Citation Tracking
🔄 Version Control

**Uyarı:**
Bu bot genel bilgi amaçlıdır. Kesin hukuki tavsiye için avukata danışın.

🌐 Web: hukukyz.preview.emergentagent.com
            """
            await query.message.reply_text(about_text, parse_mode='Markdown')
    
    async def get_user_setting(self, user_id: str, setting_name: str, default=None):
        """Get user setting from MongoDB"""
        try:
            db = mongodb_client.db
            user_settings = await db.telegram_settings.find_one({"user_id": user_id})
            
            if user_settings and setting_name in user_settings:
                return user_settings[setting_name]
            
            return default
        except Exception as e:
            logger.error(f"Error getting user setting: {e}")
            return default
    
    async def set_user_setting(self, user_id: str, setting_name: str, value):
        """Set user setting in MongoDB"""
        try:
            db = mongodb_client.db
            await db.telegram_settings.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        setting_name: value,
                        "updated_at": datetime.now().isoformat()
                    },
                    "$setOnInsert": {
                        "created_at": datetime.now().isoformat()
                    }
                },
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error setting user setting: {e}")
            raise
    
    async def save_to_history(self, user_id: str, question: str, answer: str):
        """Save interaction to MongoDB"""
        try:
            db = mongodb_client.db
            await db.telegram_history.insert_one({
                "user_id": user_id,
                "question": question,
                "answer": answer,
                "timestamp": datetime.now().isoformat(),
                "platform": "telegram"
            })
        except Exception as e:
            logger.error(f"Error saving history: {e}")
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Update {update} caused error {context.error}", exc_info=context.error)
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ Bir hata oluştu. Lütfen daha sonra tekrar deneyin."
            )
    
    def build_application(self) -> Application:
        """Build the telegram application"""
        # Create application
        app = Application.builder().token(self.token).build()
        
        # Add handlers
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CommandHandler("help", self.help_command))
        app.add_handler(CommandHandler("ask", self.ask_command))
        app.add_handler(CommandHandler("history", self.history_command))
        app.add_handler(CommandHandler("clear", self.clear_command))
        
        # Message handler (for direct questions)
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Button callback handler
        app.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Error handler
        app.add_error_handler(self.error_handler)
        
        logger.info("✅ Telegram bot application built")
        return app
    
    async def start_polling(self):
        """Start the bot with polling"""
        self.app = self.build_application()
        
        logger.info(f"🤖 Starting {self.bot_username}...")
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling(drop_pending_updates=True)
        
        logger.info(f"✅ {self.bot_username} is running!")
        
        # Keep running
        try:
            await asyncio.Event().wait()
        finally:
            await self.app.stop()
    
    async def start_webhook(self, webhook_url: str, port: int = 8080):
        """Start the bot with webhook"""
        self.app = self.build_application()
        
        logger.info(f"🤖 Starting {self.bot_username} with webhook...")
        await self.app.initialize()
        await self.app.start()
        
        # Start webhook
        await self.app.updater.start_webhook(
            listen="0.0.0.0",
            port=port,
            webhook_url=webhook_url,
            drop_pending_updates=True
        )
        
        logger.info(f"✅ {self.bot_username} webhook running on port {port}")
        
        # Keep running
        try:
            await asyncio.Event().wait()
        finally:
            await self.app.stop()


# Global bot instance (will be initialized in main.py)
telegram_bot: Optional[HukukYZBot] = None
