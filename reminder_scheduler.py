"""
АВТОМАТИЧЕСКИЕ НАПОМИНАНИЯ ДЛЯ НЕАКТИВНЫХ ПОЛЬЗОВАТЕЛЕЙ
Проверяет каждый день и отправляет сообщения в личку
"""

import os
import logging
import asyncio
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError
from dotenv import load_dotenv
from database_with_ai import get_inactive_users, update_user_visit

load_dotenv()
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Импортируем функцию для работы с AI
# При необходимости используем динамический импорт
async def get_ai_response(message_text, prompt_type='rest_reminder'):
    """Получить AI ответ для напоминания"""
    import aiohttp
    
    if not GROQ_API_KEY:
        return None
    
    prompts = {
        'rest_reminder': 'Ты заботливый фитнес-тренер. Напомни пользователю вернуться к тренировкам мотивирующим тоном. Используй "малыш", "сука".',
    }
    
    system_message = prompts.get(prompt_type, prompts['rest_reminder'])
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": message_text}
        ],
        "model": "llama-3.1-8b-instant",
        "temperature": 0.7,
        "max_tokens": 150
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data, timeout=10) as response:
                if response.status == 200:
                    result = await response.json()
                    return result['choices'][0]['message']['content']
    except Exception as e:
        logger.error(f"AI Error: {e}")
    
    return None

async def get_reminder_message(days_inactive):
    """Получить мотивирующее сообщение напоминание"""
    message_text = f"У тебя {days_inactive} дней не было никаких визитов! Пора вернуться и потренироваться!"
    
    ai_response = await get_ai_response(message_text, 'rest_reminder')
    
    if ai_response:
        return f"🔔 {ai_response}\n\n💪 Жди тебя в боте!"
    
    # Fallback если AI не ответил
    fallback_msgs = [
        "🔔 Малыш! 5 дней не было в боте! Пора вернуться и качаться! 💪",
        "🔔 Где ты пропал, сука? Качалка уже скучает! 🏋️",
        "🔔 5 дней без тренировки? Дай себя разминаю! Поехали!",
        "🔔 Отличный повод вернуться к тренировкам, малыш! 💪🔥"
    ]
    
    import random
    return random.choice(fallback_msgs)

async def send_reminders_to_inactive():
    """Отправить напоминания всем неактивным"""
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    
    try:
        # Получаем всех неактивных (5+ дней)
        inactive_users = get_inactive_users(days=5)
        logger.info(f"📊 Найдено {len(inactive_users)} неактивных пользователей")
        
        sent_count = 0
        failed_count = 0
        
        for user_id, username, last_visit, created_at, total_visits, favorite_category in inactive_users:
            try:
                days_inactive = (datetime.now() - datetime.fromisoformat(last_visit)).days
                
                if days_inactive < 5:  # Отправляем только если действительно 5+
                    continue
                
                message = await get_reminder_message(days_inactive)
                
                await bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='Markdown'
                )
                
                logger.info(f"✅ Отправлено @{username} ({days_inactive} дней)")
                sent_count += 1
                
                # Обновляем визит чтобы не спамить
                update_user_visit(user_id, username)
                
                # Задержка между сообщениями  
                await asyncio.sleep(1)
                
            except TelegramError as e:
                logger.error(f"❌ Error sending to {user_id}: {e}")
                failed_count += 1
            except Exception as e:
                logger.error(f"❌ Unexpected error for {user_id}: {e}")
                failed_count += 1
        
        logger.info(f"✅ Отправлено: {sent_count}, Ошибок: {failed_count}")
        
    except Exception as e:
        logger.error(f"❌ Critical error in reminder job: {e}")
    finally:
        await bot.session.close()

async def schedule_reminders():
    """Планировщик напоминаний - работает каждый день"""
    logger.info("⏱️ Планировщик напоминаний запущен")
    logger.info("📅 Напоминания будут отправляться каждый день в 9:00 UTC")
    
    while True:
        try:
            # Получаем текущее время
            now = datetime.now()
            
            # Проверяем если сейчас 9:00 (можно изменить)
            if now.hour == 9 and now.minute == 0:
                logger.info("🚀 Запуск проверки неактивных пользователей...")
                await send_reminders_to_inactive()
                
                # Ждём минуту чтобы не запустить дважды
                await asyncio.sleep(60)
            else:
                # Проверяем каждую минуту
                await asyncio.sleep(60)
                
        except Exception as e:
            logger.error(f"❌ Scheduler error: {e}")
            await asyncio.sleep(60)

async def manual_reminder_check():
    """Ручная проверка (для тестирования)"""
    logger.info("🔍 Ручная проверка неактивных пользователей...")
    await send_reminders_to_inactive()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        logger.info("🧪 ТЕСТОВЫЙ РЕЖИМ - отправляем напоминания сейчас")
        asyncio.run(manual_reminder_check())
    else:
        logger.info("🚀 Запуск планировщика напоминаний...")
        asyncio.run(schedule_reminders())
