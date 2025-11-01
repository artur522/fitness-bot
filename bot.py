import os
import logging
import asyncio
import random
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
from datetime import date, timedelta, datetime, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from database import create_tables, get_exercises_by_category, add_exercise, delete_exercise, modify_exercise, add_workout, get_user_stats, get_workout_logs, get_workouts_by_user, delete_workout, delete_all_workouts
from user_profiles import *
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

def escape_markdown_v2(text):
    characters = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    return ''.join(f'\\{char}' if char in characters else char for char in str(text))

create_tables()

# Базовые мотивационные сообщения
BASE_MOTIVATION_MESSAGES = [
    "💪 Не забывай о тренировках! Регулярность - ключ к успеху!",
    "🏋️‍♂️ Помни о своих целях! Каждая тренировка приближает тебя к ним!",
    "🔥 Ты становишься сильнее с каждой тренировкой!",
    "🚀 Прогресс складывается из маленьких шагов! Продолжай в том же духе!",
    "🌟 Сегодня отличный день для тренировки!",
    "💫 Ты можешь больше, чем думаешь! Докажи это себе!",
    "🎯 Дисциплина - это когда ты делаешь то, что нужно, даже когда не хочется!",
    "⚡ Энергия приходит во время движения! Начни и увидишь!",
]

# Персонализированные мотивационные сообщения
PERSONALIZED_MOTIVATION = {
    'beginner': [
        "🎯 {name}, ты делаешь большие успехи! Продолжай в том же духе!",
        "🌟 {name}, первый шаг уже сделан! Теперь главное - не останавливаться!",
        "💫 {name}, помни: даже большие чемпионы начинали с малого!",
        "👶 {name}, не смотри на других - сравнивай себя с собой вчерашним!",
    ],
    'intermediate': [
        "🔥 {name}, твой прогресс впечатляет! Так держать!",
        "🚀 {name}, ты уже видишь результаты своих усилий!",
        "🏆 {name}, твоя дисциплина достойна уважения!",
        "💪 {name}, ты преодолел начальный этап - это многое значит!",
    ],
    'advanced': [
        "💪 {name}, ты пример для других! Покажи, на что способен!",
        "🏋️‍♂️ {name}, твои тренировки вдохновляют!",
        "🎖 {name}, ты уже достиг многого! Стремись к большему!",
        "🏅 {name}, твоя сила воли восхищает!",
    ]
}

# Случайные ответы на сообщения пользователей
RANDOM_RESPONSES = [
    "💪 Отличные слова! Подкрепляй их действиями!",
    "🏋️‍♂️ Слышу тебя! Как насчет тренировки?",
    "🔥 Правильный настрой! Так держать!",
    "🚀 Круто! А теперь добавь немного спорта!",
    "🌟 Мотивируешь! Сам захотел потренироваться!",
    "💫 Сильные слова! Претворяй их в жизнь!",
    "🎯 Верю в тебя! Ты справишься!",
    "⚡ Заряжаешь энергией! Направь её в тренировку!",
]

# Ответы на конкретные фразы
KEYWORD_RESPONSES = {
    'устал': ["Отдых - это важно, но не забывай про тренировки!", "После отдыха возвращайся в зал с новыми силами!", "Усталость пройдет, а результаты останутся!"],
    'не могу': ["Ты сильнее, чем думаешь!", "Верь в себя - ты справишься!", "Не могу - это всего лишь слово!"],
    'лень': ["Лень проходит после первой тренировки!", "Победи лень - стань сильнее!", "Сделай первый шаг - остальное придет!"],
    'тренировка': ["Отличная тема! Когда следующая тренировка?", "Тренировки - это путь к лучшей версии себя!", "Тренировка - лучший антидепрессант!"],
    'зал': ["Зал ждет тебя!", "Лучшее время для зала - сейчас!", "Зал - твой второй дом!"],
    'качаться': ["Качаться - это круто!", "Железо никогда не подводит!", "Мышцы растут во время отдыха, но создаются в зале!"],
    'спорт': ["Спорт - это жизнь!", "Ты на правильном пути!", "Спорт меняет не только тело, но и мышление!"],
    'диета': ["Питание - 70% успеха!", "Не забывай про белок!", "Правильное питание + тренировки = суперрезультат!"],
    'прогресс': ["Прогресс есть! Главное не останавливаться!", "Маленькие шаги ведут к большим целям!", "Ты растешь - это главное!"],
}

async def track_user_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отслеживает активность пользователя и сохраняет в профиль"""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    create_or_update_user_profile(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        chat_id=chat_id
    )

def get_personalized_motivation(user_id):
    """Возвращает персонализированное мотивационное сообщение"""
    profile = get_user_profile(user_id)
    
    if not profile:
        return random.choice(BASE_MOTIVATION_MESSAGES)
    
    name = profile['first_name'] or "друг"
    fitness_level = profile['fitness_level']
    
    # Персонализированные сообщения для уровня подготовки
    if fitness_level in PERSONALIZED_MOTIVATION:
        message = random.choice(PERSONALIZED_MOTIVATION[fitness_level])
        return message.format(name=name)
    else:
        return random.choice(BASE_MOTIVATION_MESSAGES)

async def send_personalized_motivation(context: ContextTypes.DEFAULT_TYPE, chat_id, user_id=None):
    """Отправляет персонализированное мотивационное сообщение"""
    if user_id:
        message = get_personalized_motivation(user_id)
        await context.bot.send_message(chat_id=chat_id, text=message)
    else:
        message = random.choice(BASE_MOTIVATION_MESSAGES)
        await context.bot.send_message(chat_id=chat_id, text=message)

async def smart_motivation_scheduler(context: ContextTypes.DEFAULT_TYPE):
    """Умный планировщик мотивационных сообщений - РЕЖЕ"""
    try:
        users = get_all_users()
        sent_count = 0
        
        # Только 30% шанс отправить сообщение (реже)
        if random.random() < 0.3:
            for user in users:
                # Отправляем только 1-2 пользователям за раз
                if sent_count < 2 and random.random() < 0.4:
                    await send_personalized_motivation(context, user['chat_id'], user['user_id'])
                    sent_count += 1
                    await asyncio.sleep(1)
        
        if sent_count > 0:
            print(f"✅ Sent personalized motivation to {sent_count} users")
        
    except Exception as e:
        print(f"❌ Error in motivation scheduler: {e}")

async def workout_reminder_scheduler(context: ContextTypes.DEFAULT_TYPE):
    """Планировщик напоминаний о тренировках"""
    try:
        upcoming_workouts = get_upcoming_workouts()
        now = datetime.now()
        
        for workout in upcoming_workouts:
            workout_date = datetime.strptime(workout['next_workout_date'], '%Y-%m-%d %H:%M')
            reminder_time = workout_date - timedelta(hours=workout['reminder_hours_before'])
            
            # Если время напоминания наступило
            if now >= reminder_time and now < workout_date:
                message = (
                    f"⏰ Напоминание для {workout['first_name']}!\n"
                    f"Твоя тренировка через {workout['reminder_hours_before']} часа!\n"
                    f"Время: {workout_date.strftime('%d.%m в %H:%M')}\n"
                    f"💪 Готовься к работе!"
                )
                await context.bot.send_message(chat_id=workout['chat_id'], text=message)
                print(f"✅ Sent workout reminder to {workout['first_name']}")
        
    except Exception as e:
        print(f"❌ Error in workout reminder scheduler: {e}")

async def random_response_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Случайно отвечает на сообщения пользователей"""
    # 20% шанс ответить на сообщение (реже)
    if random.random() > 0.2:
        return
    
    message_text = update.message.text.lower()
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Отслеживаем активность
    await track_user_activity(update, context)
    
    # Проверяем ключевые слова
    response = None
    for keyword, responses in KEYWORD_RESPONSES.items():
        if keyword in message_text:
            response = random.choice(responses)
            break
    
    # Если не нашли по ключевым словам, берем случайный ответ
    if not response:
        response = random.choice(RANDOM_RESPONSES)
    
    # Добавляем имя пользователя в 40% случаев
    if random.random() < 0.4 and user.first_name:
        response = f"{user.first_name}, {response.lower()}"
    
    await update.message.reply_text(response)

# КОМАНДА MOTIVATE
async def motivate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /motivate - отправляет мотивационное сообщение"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # Отслеживаем активность
    await track_user_activity(update, context)
    
    # Отправляем персонализированное сообщение
    await send_personalized_motivation(context, chat_id, user_id)

# КОМАНДА STATISTICS
async def statistics_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /statistics - показывает меню статистики"""
    user_id = update.effective_user.id
    
    # Отслеживаем активность
    await track_user_activity(update, context)
    
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Месяц", callback_data='stats_month')],
        [InlineKeyboardButton("📅 Полгода", callback_data='stats_halfyear')],
        [InlineKeyboardButton("📅 Год", callback_data='stats_year')],
        [InlineKeyboardButton("🗑 Удалить запись", callback_data='delete_workout')],
        [InlineKeyboardButton("🔙 Меню", callback_data='back')]
    ])
    
    if update.message:
        await update.message.reply_text(
            "📊 Выбери период для просмотра статистики:",
            reply_markup=reply_markup
        )
    else:
        await update.callback_query.edit_message_text(
            "📊 Выбери период для просмотра статистики:",
            reply_markup=reply_markup
        )

# КОМАНДА PROFILE
async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /profile - показывает профиль пользователя"""
    user_id = update.effective_user.id
    profile = get_user_profile(user_id)
    
    if not profile:
        await update.message.reply_text("❌ Профиль не найден. Используй /setup для создания.")
        return
    
    level_names = {
        'beginner': '👶 Начинающий',
        'intermediate': '💪 Продвинутый',
        'advanced': '🏆 Профи'
    }
    
    level = level_names.get(profile['fitness_level'], 'Не установлен')
    
    # Информация о следующей тренировке
    workout_info = ""
    if profile['next_workout_date']:
        workout_date = datetime.strptime(profile['next_workout_date'], '%Y-%m-%d %H:%M')
        time_left = workout_date - datetime.now()
        if time_left.total_seconds() > 0:
            hours_left = int(time_left.total_seconds() // 3600)
            minutes_left = int((time_left.total_seconds() % 3600) // 60)
            workout_info = f"\n🎯 Следующая тренировка: {workout_date.strftime('%d.%m в %H:%M')}\n⏰ Осталось: {hours_left}ч {minutes_left}м"
        else:
            workout_info = "\n🎯 Последняя тренировка была запланирована на: " + workout_date.strftime('%d.%m в %H:%M')
    
    text = (
        f"👤 Твой профиль:\n"
        f"Имя: {profile['first_name']}\n"
        f"Уровень: {level}\n"
        f"В системе с: {profile['created_at'][:10]}\n"
        f"Последняя активность: {profile['last_active'][:10]}"
        f"{workout_info}"
    )
    
    await update.message.reply_text(text)

# НОВЫЕ КОМАНДЫ ДЛЯ ТРЕНИРОВОК
async def set_workout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Установить следующую тренировку"""
    user_id = update.effective_user.id
    
    # Отслеживаем активность
    await track_user_activity(update, context)
    
    if not context.args:
        # Показываем клавиатуру с датами
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🕐 Сегодня 19:00", callback_data='workout_today')],
            [InlineKeyboardButton("🕑 Завтра 19:00", callback_data='workout_tomorrow')],
            [InlineKeyboardButton("🕒 Послезавтра 19:00", callback_data='workout_dayafter')],
            [InlineKeyboardButton("📅 Выбрать дату", callback_data='workout_custom')],
            [InlineKeyboardButton("❌ Отменить", callback_data='workout_cancel')]
        ])
        
        await update.message.reply_text(
            "🎯 Когда планируешь следующую тренировку?",
            reply_markup=reply_markup
        )
        return
    
    # Обработка текстовой команды
    try:
        date_str = ' '.join(context.args)
        workout_date = parse_workout_date(date_str)
        
        if workout_date:
            set_next_workout_date(user_id, workout_date.strftime('%Y-%m-%d %H:%M'))
            await update.message.reply_text(
                f"✅ Запланирована тренировка на {workout_date.strftime('%d.%m.%Y в %H:%M')}\n"
                f"Я напомню тебе за 2 часа до начала! ⏰"
            )
        else:
            await update.message.reply_text(
                "❌ Не могу распознать дату. Используй:\n"
                "• /workout сегодня 19:00\n"
                "• /workout завтра 18:00\n"
                "• /workout 15.12 20:00\n"
                "• /workout 2024-12-25 20:00"
            )
            
    except Exception as e:
        await update.message.reply_text("❌ Ошибка при установке даты. Попробуй еще раз.")

async def workout_date_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик выбора даты тренировки"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    action = query.data
    
    if action == 'workout_today':
        # Устанавливаем тренировку на сегодня вечером
        workout_date = datetime.now().replace(hour=19, minute=0, second=0, microsecond=0)
        set_next_workout_date(user_id, workout_date.strftime('%Y-%m-%d %H:%M'))
        await query.edit_message_text(
            f"✅ Отлично! Запланирована тренировка на сегодня в 19:00!\n"
            f"Я напомню тебе в 17:00 ⏰"
        )
        
    elif action == 'workout_tomorrow':
        # Устанавливаем тренировку на завтра вечером
        workout_date = (datetime.now() + timedelta(days=1)).replace(hour=19, minute=0, second=0, microsecond=0)
        set_next_workout_date(user_id, workout_date.strftime('%Y-%m-%d %H:%M'))
        await query.edit_message_text(
            f"✅ Отлично! Запланирована тренировка на завтра в 19:00!\n"
            f"Я напомню тебе за 2 часа до начала ⏰"
        )
        
    elif action == 'workout_dayafter':
        # Устанавливаем тренировку на послезавтра
        workout_date = (datetime.now() + timedelta(days=2)).replace(hour=19, minute=0, second=0, microsecond=0)
        set_next_workout_date(user_id, workout_date.strftime('%Y-%m-%d %H:%M'))
        await query.edit_message_text(
            f"✅ Отлично! Запланирована тренировка на послезавтра в 19:00!\n"
            f"Я напомню тебе за 2 часа до начала ⏰"
        )
        
    elif action == 'workout_custom':
        await query.edit_message_text(
            "📅 Введи дату и время тренировки:\n\n"
            "Примеры:\n"
            "• сегодня 20:00\n"
            "• завтра 18:30\n"
            "• 25.12 19:00\n"
            "• 2024-12-25 20:00"
        )
        context.user_data['waiting_for_workout_date'] = True
        
    elif action == 'workout_cancel':
        await query.edit_message_text("❌ Отменено")

async def my_workouts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать мои запланированные тренировки"""
    user_id = update.effective_user.id
    
    # Отслеживаем активность
    await track_user_activity(update, context)
    
    profile = get_user_profile(user_id)
    
    if not profile or not profile['next_workout_date']:
        await update.message.reply_text(
            "📅 У тебя нет запланированных тренировок.\n\n"
            "Используй /workout чтобы запланировать тренировку! 💪"
        )
        return
    
    workout_date = datetime.strptime(profile['next_workout_date'], '%Y-%m-%d %H:%M')
    time_left = workout_date - datetime.now()
    
    if time_left.total_seconds() > 0:
        hours_left = int(time_left.total_seconds() // 3600)
        minutes_left = int((time_left.total_seconds() % 3600) // 60)
        time_info = f"⏰ Осталось: {hours_left}ч {minutes_left}м"
    else:
        time_info = "⏰ Время тренировки уже прошло"
    
    await update.message.reply_text(
        f"🎯 Твоя следующая тренировка:\n"
        f"📅 {workout_date.strftime('%d.%m.%Y в %H:%M')}\n"
        f"{time_info}\n"
        f"🔔 Напоминание за {profile['reminder_hours_before']} часа\n\n"
        f"Используй /workout чтобы изменить дату"
    )

def parse_workout_date(date_str):
    """Парсит строку с датой тренировки"""
    try:
        now = datetime.now()
        date_str = date_str.lower().strip()
        
        if date_str.startswith('сегодня'):
            time_part = date_str.replace('сегодня', '').strip()
            if not time_part:
                time_part = '19:00'
            time_obj = datetime.strptime(time_part, '%H:%M').time()
            return datetime.combine(now.date(), time_obj)
            
        elif date_str.startswith('завтра'):
            time_part = date_str.replace('завтра', '').strip()
            if not time_part:
                time_part = '19:00'
            time_obj = datetime.strptime(time_part, '%H:%M').time()
            return datetime.combine(now.date() + timedelta(days=1), time_obj)
            
        elif '.' in date_str:  # Формат DD.MM
            parts = date_str.split()
            date_part = parts[0]
            time_part = parts[1] if len(parts) > 1 else '19:00'
            
            date_obj = datetime.strptime(date_part, '%d.%m').date()
            date_obj = date_obj.replace(year=now.year)
            time_obj = datetime.strptime(time_part, '%H:%M').time()
            return datetime.combine(date_obj, time_obj)
            
        elif '-' in date_str:  # Формат YYYY-MM-DD
            parts = date_str.split()
            date_part = parts[0]
            time_part = parts[1] if len(parts) > 1 else '19:00'
            
            date_obj = datetime.strptime(date_part, '%Y-%m-%d').date()
            time_obj = datetime.strptime(time_part, '%H:%M').time()
            return datetime.combine(date_obj, time_obj)
            
    except Exception:
        return None
    
    return None

# СУЩЕСТВУЮЩИЕ КОМАНДЫ
async def setup_user_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Настройка профиля пользователя"""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    create_or_update_user_profile(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        chat_id=chat_id
    )
    
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("👶 Начинающий", callback_data='level_beginner')],
        [InlineKeyboardButton("💪 Продвинутый", callback_data='level_intermediate')],
        [InlineKeyboardButton("🏆 Профи", callback_data='level_advanced')]
    ])
    
    await update.message.reply_text(
        "🎯 Давай настроим твой профиль! Выбери свой уровень подготовки:",
        reply_markup=reply_markup
    )

async def handle_level_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор уровня подготовки"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    level = query.data.split('_')[1]
    
    update_user_fitness_level(user_id, level)
    
    level_names = {
        'beginner': 'начинающий',
        'intermediate': 'продвинутый', 
        'advanced': 'профи'
    }
    
    await query.edit_message_text(
        f"✅ Отлично! Установлен уровень: {level_names[level]}\n"
        f"Теперь мотивационные сообщения будут персонализированы для тебя!"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    context.user_data.clear()
    
    # Создаем/обновляем профиль пользователя
    user = update.effective_user
    chat_id = update.effective_chat.id
    create_or_update_user_profile(user.id, user.username, user.first_name, chat_id)
    
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("💪 Грудь и бицепс", callback_data='chest_biceps')],
        [InlineKeyboardButton("🏋️‍♂️ Спина и трицепс", callback_data='back_triceps')],
        [InlineKeyboardButton("🦵 Ноги и плечи", callback_data='legs_shoulders')],
        [InlineKeyboardButton("📊 Статистика", callback_data='statistics')],
        [InlineKeyboardButton("🎯 Мои тренировки", callback_data='my_workouts_menu')],
        [InlineKeyboardButton("⚙️ Настройки", callback_data='settings')]
    ])
    
    text = (
        "❚█══█❚ Фитнес-мотиватор! ❚█══█❚\n\n"
        "Я помогу тебе:\n"
        "• 🎯 Запланировать тренировки\n"
        "• ⏰ Напоминать о занятиях\n"
        "• 💪 Мотивировать и поддерживать\n"
        "• 📊 Следить за прогрессом\n\n"
        "Выбери раздел:"
    )
    
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

# Обработчик для кнопки "Мои тренировки" в меню
async def my_workouts_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки Мои тренировки в меню"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    profile = get_user_profile(user_id)
    
    if not profile or not profile['next_workout_date']:
        await query.edit_message_text(
            "📅 У тебя нет запланированных тренировок.\n\n"
            "Используй /workout чтобы запланировать тренировку! 💪",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎯 Запланировать тренировку", callback_data='do_workout')],
                [InlineKeyboardButton("🔙 Назад", callback_data='back')]
            ])
        )
        return
    
    workout_date = datetime.strptime(profile['next_workout_date'], '%Y-%m-%d %H:%M')
    time_left = workout_date - datetime.now()
    
    if time_left.total_seconds() > 0:
        hours_left = int(time_left.total_seconds() // 3600)
        minutes_left = int((time_left.total_seconds() % 3600) // 60)
        time_info = f"⏰ Осталось: {hours_left}ч {minutes_left}м"
    else:
        time_info = "⏰ Время тренировки уже прошло"
    
    await query.edit_message_text(
        f"🎯 Твоя следующая тренировка:\n"
        f"📅 {workout_date.strftime('%d.%m.%Y в %H:%M')}\n"
        f"{time_info}\n"
        f"🔔 Напоминание за {profile['reminder_hours_before']} часа\n\n"
        f"Используй /workout чтобы изменить дату",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✏️ Изменить тренировку", callback_data='workout_custom')],
            [InlineKeyboardButton("🔙 Назад", callback_data='back')]
        ])
    )

# ... остальные существующие обработчики (category_handler, display_exercises и т.д.)

def main():
    token = os.environ.get('BOT_TOKEN')
    
    if not token:
        logging.error("❌ BOT_TOKEN not found in environment variables")
        return
    
    app = ApplicationBuilder().token(token).build()
    
    # Основные команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setup", setup_user_profile))
    app.add_handler(CommandHandler("profile", profile_command))
    app.add_handler(CommandHandler("motivate", motivate_command))
    #app.add_handler(CommandHandler("statistics", statistics_command)) - статистика
    app.add_handler(CommandHandler("workout", set_workout))
    app.add_handler(CommandHandler("my_workouts", my_workouts_command))
    
    # Обработчики callback
    app.add_handler(CallbackQueryHandler(handle_level_selection, pattern='^level_'))
    app.add_handler(CallbackQueryHandler(workout_date_handler, pattern='^workout_'))
    app.add_handler(CallbackQueryHandler(my_workouts_menu_handler, pattern='^my_workouts_menu$'))
    app.add_handler(CallbackQueryHandler(statistics_command, pattern='^statistics$'))
    
    # Обработчик случайных ответов на сообщения в группах
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
        random_response_handler
    ))
    
    # Умный планировщик мотивации - РЕЖЕ (каждые 8 часов)
    app.job_queue.run_repeating(
        smart_motivation_scheduler,
        interval=28800,  # 8 часов
        first=30
    )
    
    # Планировщик напоминаний о тренировках (проверяет каждые 30 минут)
    app.job_queue.run_repeating(
        workout_reminder_scheduler,
        interval=1800,  # 30 минут
        first=10
    )
    
    logging.info("🤖 Smart workout bot started!")
    app.run_polling()

if __name__ == "__main__":
    main()