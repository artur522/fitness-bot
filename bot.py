import os
import logging
import random
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
from datetime import date, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from database import create_tables, get_exercises_by_category, add_exercise, delete_exercise, modify_exercise, add_workout, get_user_stats, get_workout_logs, get_workouts_by_user, delete_workout
import os
from dotenv import load_dotenv
from database import create_tables, get_exercises_by_category, add_exercise, delete_exercise, modify_exercise, add_workout, get_user_stats, get_workout_logs, get_workouts_by_user, delete_workout, delete_all_workouts

# Загружаем переменные из .env файла
load_dotenv()
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# Мотивационные фразы для группового чата
MOTIVATIONAL_PHRASES = [
    "Уважаемые участники! Напоминаю о важности регулярных тренировок. 💪",
    "Отличная работа тем, кто сегодня посетил тренировку! 🔥",
    "Напоминание: прогресс требует последовательности и дисциплины. 🏋️",
    "Не забывайте о восстановлении после тренировок. 🥛",
    "Я вижу ваш прогресс, продолжайте в том же духе! 🏆",
    "Разминка - обязательная часть тренировочного процесса. 🤸",
    "Сегодня прекрасный день для установления новых личных рекордов! 💥",
    "Регулярность - ключ к достижению спортивных целей. 😊",
    "Каждая тренировка приближает вас к поставленным целям. 💦",
    "Отличные результаты сегодня! Продолжайте работать! 👏",
    "Заминка и растяжка помогут улучшить восстановление. 🧘",
    "Ваше упорство впечатляет! Так держать! 🔥",
    "Тренировка ног - фундамент сильного тела. 🦵",
    "Дисциплина и регулярность приводят к результатам. 💪",
    "Сбалансированное питание - важная составляющая успеха. 🍗",
    "Качественный сон необходим для мышечного восстановления. 😴",
    "Новый день - новые возможности для совершенствования! 🌟",
    "Не сдавайтесь! Упорство всегда вознаграждается. ❤️",
    "Гидратация особенно важна во время тренировок. 💧",
    "Правильная техника выполнения важнее рабочего веса. 📊"
]

# Фразы для ответов на сообщения
RESPONSE_PHRASES = [
    "Согласен с вашим мнением! 👍",
    "Отличная мотивация! 🔥", 
    "Полностью разделяю ваш подход! 💪",
    "Верное направление мыслей! 👏",
    "Профессиональный подход! 😎",
    "Рациональное предложение! 💭",
    "Опыт чувствуется в ваших словах! 🏆",
    "Поддерживаю эту точку зрения! ✅",
    "Энтузиазм заразителен! Продолжайте! 🔥",
    "Конструктивное предложение! 🧠"
]

# Ключевые слова для реакций
TRIGGER_WORDS = {
    'качалка': "Тренировочный процесс требует системного подхода! 💪",
    'тренировка': "Регулярные тренировки - основа прогресса! 🏋️", 
    'спортзал': "Спортивный зал ждет своих посетителей! 🔥",
    'жим': "Жимовые упражнения развивают силу верхней части тела! 💥",
    'присед': "Приседания - базовое упражнение для развития ног! 👑",
    'становая': "Становая тяга требует особого внимания к технике! ⚡",
    'протеин': "Белковое питание поддерживает мышечный рост! 🥛",
    'качаться': "Системные тренировки приводят к результатам! ❤️",
    'мышцы': "Мышечная система отвечает на регулярные нагрузки! 💪",
    'рельеф': "Мышечный рельеф достигается комплексным подходом! 🏔️",
    'сила': "Силовые показатели растут при последовательных тренировках! 🔥",
    'памп': "Кровенаполнение мышц свидетельствует об эффективной работе! 💉",
    'прогресс': "Отслеживание прогресса мотивирует к дальнейшим занятиям! 📈",
    'диета': "Сбалансированное питание - важный компонент тренировок! 🥗",
    'разминка': "Предтренировочная разминка предотвращает травмы! 🤸"
}

def escape_markdown_v2(text):
    characters = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    return ''.join(f'\\{char}' if char in characters else char for char in str(text))

create_tables()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("💪 Грудь и бицепс", callback_data='chest_biceps')],
        [InlineKeyboardButton("🏋️‍♂️ Спина и трицепс", callback_data='back_triceps')],
        [InlineKeyboardButton("🦵 Ноги и плечи", callback_data='legs_shoulders')],
        [InlineKeyboardButton("📊 Статистика", callback_data='statistics')],
        [InlineKeyboardButton("⚙️ Настройки", callback_data='settings')]
    ])
    main_menu = ReplyKeyboardMarkup([["/start", "📊 Статистика"]], resize_keyboard=True)
    text = escape_markdown_v2("❚█══█❚ Фитнес-бот запущен! ❚█══█❚") + "\n" + escape_markdown_v2("Выберите категорию упражнений или раздел:")
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='MarkdownV2')
    else:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='MarkdownV2')

async def settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    default_reps = context.user_data.get('default_reps', 8)
    
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🔄 Повторений за подход: {default_reps}", callback_data='change_reps')],
        [InlineKeyboardButton("🔙 Назад", callback_data='back')]
    ])
    
    await query.edit_message_text(
        escape_markdown_v2("⚙️ Настройки тренировки:"),
        reply_markup=reply_markup,
        parse_mode='MarkdownV2'
    )

async def change_reps_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    context.user_data['action'] = 'change_reps'
    await query.edit_message_text(
        escape_markdown_v2("Введите количество повторений за подход (например, 8, 10, 12):"),
        parse_mode='MarkdownV2'
    )

async def category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    mapping = {
        'chest_biceps': "Грудь и бицепс",
        'back_triceps': "Спина и трицепс",
        'legs_shoulders': "Ноги и плечи"
    }
    category = mapping.get(query.data, "Грудь и бицепс")
    context.user_data['category'] = category
    context.user_data['page'] = 0
    await display_exercises(query, category, context)

async def display_exercises(query, category, context, page=0):
    exercises = get_exercises_by_category(category)
    
    text = f"{get_emoji(category)} *{escape_markdown_v2(category)}*\n\n"
    if not exercises:
        text += escape_markdown_v2("📝 Упражнения отсутствуют.")
    else:
        for ex in exercises:
            text += f"▫ *{escape_markdown_v2(ex[1])}*\n   ⚖ {escape_markdown_v2(ex[2])}\n{'─' * 20}\n"

    buttons = [
        [InlineKeyboardButton("✅ Выполнить", callback_data='do_workout')],
        [InlineKeyboardButton("✏ Редактировать", callback_data='edit_exercise')],
        [InlineKeyboardButton("🔙 Меню", callback_data='back')]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode='MarkdownV2')

def get_emoji(category):
    return {
        "Грудь и бицепс": "💪",
        "Спина и трицепс": "🏋️‍♂️",
        "Ноги и плечи": "🦵"
    }.get(category, "")

async def edit_exercise_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Добавить", callback_data='add_exercise')],
        [InlineKeyboardButton("🗑 Удалить", callback_data='delete_exercise')],
        [InlineKeyboardButton("✏ Изменить", callback_data='modify_exercise')],
        [InlineKeyboardButton("🔙 Меню", callback_data='back')]
    ])
    await query.edit_message_text(escape_markdown_v2("Выберите действие:"), reply_markup=reply_markup, parse_mode='MarkdownV2')

async def add_exercise_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['action'] = 'add'
    text = escape_markdown_v2("Введите: Название, веса (через запятую)\nПример: Жим лежа, 70, 75, 75")
    await query.edit_message_text(text, parse_mode='MarkdownV2')

async def delete_exercise_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category = context.user_data.get('category')
    exercises = get_exercises_by_category(category)
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"• {escape_markdown_v2(ex[1])}", callback_data=f'delete_{ex[0]}')] for ex in exercises
    ] + [[InlineKeyboardButton("🔙 Меню", callback_data='back')]])
    await query.edit_message_text(escape_markdown_v2("Выберите упражнение для удаления:"), reply_markup=reply_markup, parse_mode='MarkdownV2')

async def confirm_delete_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    exercise_id = int(query.data.split('_')[1])
    delete_exercise(exercise_id)
    await query.edit_message_text(
        escape_markdown_v2("✅ Упражнение удалено!"),
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✔ ОК", callback_data='back_to_cat')]]),
        parse_mode='MarkdownV2'
    )

async def modify_exercise_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category = context.user_data.get('category')
    exercises = get_exercises_by_category(category)
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"• {escape_markdown_v2(ex[1])}", callback_data=f'modify_{ex[0]}')] for ex in exercises
    ] + [[InlineKeyboardButton("🔙 Меню", callback_data='back')]])
    await query.edit_message_text(escape_markdown_v2("Выберите упражнение для изменения:"), reply_markup=reply_markup, parse_mode='MarkdownV2')

async def confirm_modify_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    exercise_id = int(query.data.split('_')[1])
    context.user_data['exercise_id'] = exercise_id
    context.user_data['action'] = 'modify'
    category = context.user_data.get('category')
    exercises = get_exercises_by_category(category)
    exercise = next((ex for ex in exercises if ex[0] == exercise_id), None)
    text = escape_markdown_v2(f"Введите новые веса для '{exercise[1]}' (через запятую):\nПример: 70, 75, 75")
    await query.edit_message_text(text, parse_mode='MarkdownV2')

async def workout_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category = context.user_data.get('category')
    exercises = get_exercises_by_category(category)
    if not exercises:
        await query.edit_message_text(escape_markdown_v2("📝 Упражнения отсутствуют."), parse_mode='MarkdownV2')
        return
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{escape_markdown_v2(ex[1])}", callback_data=f'workout_{ex[0]}')] for ex in exercises
    ] + [[InlineKeyboardButton("🔙 Назад", callback_data='back_to_cat')]])
    await query.edit_message_text(
        escape_markdown_v2(f"Выберите упражнение ({category}):"),
        reply_markup=reply_markup,
        parse_mode='MarkdownV2'
    )

async def select_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    ex_id = int(query.data.split('_')[1])
    category = context.user_data['category']
    exercises = get_exercises_by_category(category)
    exercise = next((ex for ex in exercises if ex[0] == ex_id), None)
    if not exercise:
        await query.edit_message_text("❌ Упражнение не найдено.")
        return
    context.user_data['exercise'] = exercise
    context.user_data['sets'] = []
    
    weights = [w.strip() for w in exercise[2].split(',')]
    buttons = [[InlineKeyboardButton(f"{w} кг", callback_data=f'addset_{w}')] for w in weights]
    buttons.append([InlineKeyboardButton("➕ Свой вес", callback_data='custom_weight')])
    buttons.append([InlineKeyboardButton("✅ Завершить", callback_data='finish_sets')])
    buttons.append([InlineKeyboardButton("🔙 Назад", callback_data='do_workout')])
    
    await query.edit_message_text(
        f"🏋️ Упражнение: {exercise[1]}\n\n"
        f"Отмеченные подходы:\n"
        f"Пока нет подходов\n\n"
        f"Выберите вес — каждый клик = подход 💥\n"
        f"Нажмите «✅ Завершить» для сохранения.",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def add_set(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    weight = float(query.data.split('_')[1])
    sets = context.user_data.get('sets', [])
    sets.append(weight)
    context.user_data['sets'] = sets
    exercise = context.user_data['exercise']
    
    # Формируем список подходов (без Markdown)
    sets_text = ""
    for i, set_weight in enumerate(sets, 1):
        sets_text += f"{i}. {set_weight} кг\n"
    
    buttons = [[InlineKeyboardButton(f"{w} кг", callback_data=f'addset_{w}')]
               for w in exercise[2].split(',')]
    buttons.append([InlineKeyboardButton("➕ Свой вес", callback_data='custom_weight')])
    buttons.append([InlineKeyboardButton("✅ Завершить", callback_data='finish_sets')])
    buttons.append([InlineKeyboardButton("🔙 Назад", callback_data='do_workout')])
    
    await query.edit_message_text(
        f"🏋️ Упражнение: {exercise[1]}\n\n"
        f"Отмеченные подходы:\n"
        f"{sets_text}\n"
        f"Выберите вес для следующего подхода:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def custom_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(escape_markdown_v2("Введите вес (число, например, 75):"), parse_mode='MarkdownV2')
    context.user_data['action'] = 'custom_weight'

async def finish_sets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    exercise = context.user_data.get('exercise')
    sets = context.user_data.get('sets', [])
    if not sets:
        await query.edit_message_text(escape_markdown_v2("⚠️ Подходы не были отмечены."), parse_mode='MarkdownV2')
        return
    
    default_reps = context.user_data.get('default_reps', 8)
    category = context.user_data.get('category')
    
    for weight in sets:
        add_workout(0, exercise[1], default_reps, weight, category)
    
    weights_str = ', '.join(escape_markdown_v2(str(w)) for w in sets)
    
    saved_category = context.user_data.get('category')
    context.user_data.clear()
    context.user_data['category'] = saved_category
    
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='back_to_cat')]])
    await query.edit_message_text(
        f"{escape_markdown_v2('✅')} *{escape_markdown_v2(exercise[1])}*\n\n"
        f"{escape_markdown_v2(f'Количество подходов: {len(sets)}')}\n"
        f"{escape_markdown_v2(f'Повторений в подходе: {default_reps}')}\n"
        f"{escape_markdown_v2(f'Использованные веса:')} {weights_str} {escape_markdown_v2('кг')}",
        reply_markup=reply_markup,
        parse_mode='MarkdownV2'
    )

async def statistics_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if 'stat_messages' in context.user_data:
        for msg_id in context.user_data['stat_messages']:
            try:
                await query.message.chat.delete_message(msg_id)
            except Exception as e:
                logging.warning(f"Failed to delete message {msg_id}: {str(e)}")
        context.user_data['stat_messages'] = []
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Месяц", callback_data='stats_month')],
        [InlineKeyboardButton("📅 Полгода", callback_data='stats_halfyear')],
        [InlineKeyboardButton("📅 Год", callback_data='stats_year')],
        [InlineKeyboardButton("🗑 Удалить запись", callback_data='delete_workout')],
        [InlineKeyboardButton("🔙 Меню", callback_data='back')]
    ])
    await query.edit_message_text(escape_markdown_v2("Выберите период для просмотра статистики:"), reply_markup=reply_markup, parse_mode='MarkdownV2')

async def delete_workout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    start_date = (date.today() - timedelta(days=365)).isoformat()
    end_date = date.today().isoformat()
    workouts = get_workouts_by_user(0, start_date, end_date)
    if not workouts:
        await query.edit_message_text(
            escape_markdown_v2("📊 Записи тренировок отсутствуют."),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='statistics')]]),
            parse_mode='MarkdownV2'
        )
        return
    
    # Добавляем кнопку удаления всех записей
    buttons = []
    for workout in workouts:
        workout_id, exercise_name, weight, reps, workout_date = workout
        button_text = f"{escape_markdown_v2(exercise_name)}: {escape_markdown_v2(weight)} кг, {reps} повт., {escape_markdown_v2(workout_date)}"
        buttons.append([InlineKeyboardButton(button_text, callback_data=f'delete_workout_{workout_id}')])
    
    # Кнопка удаления всех записей
    buttons.append([InlineKeyboardButton("🗑️ УДАЛИТЬ ВСЕ ЗАПИСИ", callback_data='delete_all_workouts')])
    buttons.append([InlineKeyboardButton("🔙 Назад", callback_data='statistics')])
    
    await query.edit_message_text(
        escape_markdown_v2("Выберите запись для удаления:"),
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode='MarkdownV2'
    )
    
async def delete_all_workouts_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Кнопки подтверждения
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ ПОДТВЕРДИТЬ УДАЛЕНИЕ", callback_data='confirm_delete_all')],
        [InlineKeyboardButton("❌ ОТМЕНА", callback_data='delete_workout')]
    ])
    
    await query.edit_message_text(
        escape_markdown_v2("⚠️ ВНИМАНИЕ: Это действие удалит ВСЕ записи тренировок без возможности восстановления!"),
        reply_markup=reply_markup,
        parse_mode='MarkdownV2'
    )
    
async def confirm_delete_all_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Удаляем все записи (для всех пользователей)
    delete_all_workouts()
    
    await query.edit_message_text(
        escape_markdown_v2("✅ Все записи тренировок были удалены!"),
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='statistics')]]),
        parse_mode='MarkdownV2'
    )

async def confirm_delete_workout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    workout_id = int(query.data.split('_')[2])
    delete_workout(workout_id)
    await query.edit_message_text(
        escape_markdown_v2("✅ Запись удалена!"),
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✔ ОК", callback_data='statistics')]]),
        parse_mode='MarkdownV2'
    )

async def display_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    period = query.data.split('_')[1]
    if period == 'month':
        start_date = (date.today() - timedelta(days=30)).isoformat()
        period_text = "за месяц"
    elif period == 'halfyear':
        start_date = (date.today() - timedelta(days=180)).isoformat()
        period_text = "за полгода"
    else:
        start_date = (date.today() - timedelta(days=365)).isoformat()
        period_text = "за год"
    end_date = date.today().isoformat()
    categories = ["Грудь и бицепс", "Спина и трицепс", "Ноги и плечи"]
    stat_messages = []
    for cat in categories:
        text = get_user_stats(0, start_date, end_date, cat)
        exercises = get_exercises_by_category(cat)
        media = []
        for ex in exercises:
            logs = get_workout_logs(0, ex[1], start_date, end_date, cat)
            if logs:
                graph = generate_progress_graph(ex[1], logs, period_text)
                if graph:
                    media.append(InputMediaPhoto(media=graph, caption=escape_markdown_v2(f"График прогресса: {ex[1]} {period_text}"), parse_mode='MarkdownV2'))
        if media:
            media_group = await query.message.reply_media_group(media=media)
            stat_messages.extend([msg.message_id for msg in media_group])
        if text != escape_markdown_v2(f"📊 Данные за указанный период отсутствуют."):
            text_message = await query.message.reply_text(text, parse_mode='MarkdownV2')
            stat_messages.append(text_message.message_id)
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='statistics')]])
    final_message = await query.message.reply_text(
        escape_markdown_v2("📈 Общая статистика по категориям:"),
        reply_markup=reply_markup,
        parse_mode='MarkdownV2'
    )
    stat_messages.append(final_message.message_id)
    context.user_data['stat_messages'] = stat_messages

def generate_progress_graph(exercise_name, logs, period_text):
    if not logs:
        return None
    dates = [log[0] for log in logs]
    weights = [log[1] for log in logs]
    plt.figure(figsize=(8, 4))
    plt.plot(dates, weights, marker='o', linestyle='-', color='#1f77b4')
    plt.title(escape_markdown_v2(f'Прогресс: {exercise_name}'))
    plt.xlabel(escape_markdown_v2('Дата'))
    plt.ylabel(escape_markdown_v2('Вес (кг)'))
    plt.xticks(rotation=45, fontsize=10)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    plt.close()
    return buf

# Новые функции для работы в групповом чате
async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик сообщений в групповом чате"""
    if not update.message or not update.message.text:
        return
    
    message_text = update.message.text.lower()
    
    # Случайные мотивационные фразы (5% вероятность)
    if random.random() < 0.05:
        phrase = random.choice(MOTIVATIONAL_PHRASES)
        await update.message.reply_text(phrase)
        return
    
    # Ответы на упоминания бота
    if '@' in message_text and any(word in message_text for word in ['бот', 'bot', 'качалка']):
        phrase = random.choice(RESPONSE_PHRASES)
        await update.message.reply_text(phrase)
        return
    
    # Реакции на ключевые слова
    for trigger_word, response in TRIGGER_WORDS.items():
        if trigger_word in message_text:
            # 70% вероятность ответа на ключевое слово
            if random.random() < 0.7:
                await update.message.reply_text(response)
                return

async def handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем, является ли сообщение групповым
    if update.message and update.message.chat.type in ['group', 'supergroup']:
        await handle_group_message(update, context)
        return
        
    action = context.user_data.get('action')
    user_id = update.effective_user.id
    category = context.user_data.get('category')
    try:
        if action == 'custom_weight':
            weight = float(update.message.text.strip())
            sets = context.user_data.get('sets', [])
            sets.append(weight)
            context.user_data['sets'] = sets
            context.user_data['action'] = None
            exercise = context.user_data['exercise']
            
            # Формируем список подходов (без Markdown)
            sets_text = ""
            for i, set_weight in enumerate(sets, 1):
                sets_text += f"{i}. {set_weight} кг\n"
            
            buttons = [[InlineKeyboardButton(f"{w} кг", callback_data=f'addset_{w}')]
                       for w in exercise[2].split(',')]
            buttons.append([InlineKeyboardButton("➕ Свой вес", callback_data='custom_weight')])
            buttons.append([InlineKeyboardButton("✅ Завершить", callback_data='finish_sets')])
            buttons.append([InlineKeyboardButton("🔙 Назад", callback_data='do_workout')])
            
            await update.message.reply_text(
                f"🏋️ Упражнение: {exercise[1]}\n\n"
                f"Отмеченные подходы:\n"
                f"{sets_text}\n"
                f"Выберите вес для следующего подхода:",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        elif action == 'add':
            if 'new_exercise' not in context.user_data:
                context.user_data['new_exercise'] = update.message.text.strip()
                await update.message.reply_text(
                    escape_markdown_v2(f"Введите веса для '{context.user_data['new_exercise']}' (через запятую):\nПример: 70, 75, 75"),
                    parse_mode='MarkdownV2'
                )
            else:
                weights = [float(w.strip()) for w in update.message.text.split(',')]
                new_exercise = context.user_data['new_exercise']
                add_exercise(category, new_exercise, ', '.join(map(str, weights)))
                weight_str = ', '.join(map(str, weights))
                await update.message.reply_text(
                    f"{escape_markdown_v2(f'Упражнение {new_exercise} добавлено: {weight_str} кг')} ✅",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✔ ОК", callback_data='back_to_cat')]]),
                    parse_mode='MarkdownV2'
                )
                context.user_data['action'] = None
                context.user_data.pop('new_exercise', None)
        elif action == 'modify':
            weights = [float(w.strip()) for w in update.message.text.split(',')]
            modify_exercise(context.user_data['exercise_id'], ', '.join(map(str, weights)))
            weight_str = ', '.join(map(str, weights))
            await update.message.reply_text(
                f"{escape_markdown_v2(f'Упражнение обновлено: {weight_str} кг')} ✅",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✔ ОК", callback_data='back_to_cat')]]),
                parse_mode='MarkdownV2'
            )
            context.user_data['action'] = None
            context.user_data.pop('exercise_id', None)
    except ValueError:
        await update.message.reply_text(escape_markdown_v2("⚠️ Проверьте правильность введенных данных."), parse_mode='MarkdownV2')

async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await start(update, context)

async def back_to_cat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await display_exercises(query, context.user_data.get('category'), context)

async def back_to_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await statistics_handler(update, context)

def main():
    token = os.environ.get('BOT_TOKEN')
    
    if not token:
        logging.error("❌ BOT_TOKEN not found in environment variables")
        print("❌ BOT_TOKEN not found in environment variables")
        return
    
    app = ApplicationBuilder().token(token).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(settings_handler, pattern='^settings$'))
    app.add_handler(CallbackQueryHandler(change_reps_handler, pattern='^change_reps$'))
    app.add_handler(CallbackQueryHandler(category_handler, pattern='^(chest_biceps|back_triceps|legs_shoulders)$'))
    app.add_handler(CallbackQueryHandler(edit_exercise_handler, pattern='^edit_exercise$'))
    app.add_handler(CallbackQueryHandler(add_exercise_handler, pattern='^add_exercise$'))
    app.add_handler(CallbackQueryHandler(delete_exercise_handler, pattern='^delete_exercise$'))
    app.add_handler(CallbackQueryHandler(confirm_delete_handler, pattern='^delete_\\d+$'))
    app.add_handler(CallbackQueryHandler(modify_exercise_handler, pattern='^modify_exercise$'))
    app.add_handler(CallbackQueryHandler(confirm_modify_handler, pattern='^modify_\\d+$'))
    app.add_handler(CallbackQueryHandler(workout_menu, pattern='^do_workout$'))
    app.add_handler(CallbackQueryHandler(select_weight, pattern='^workout_\\d+$'))
    app.add_handler(CallbackQueryHandler(add_set, pattern='^addset_'))
    app.add_handler(CallbackQueryHandler(custom_weight, pattern='^custom_weight$'))
    app.add_handler(CallbackQueryHandler(finish_sets, pattern='^finish_sets$'))
    app.add_handler(CallbackQueryHandler(statistics_handler, pattern='^statistics$'))
    app.add_handler(CallbackQueryHandler(delete_workout_handler, pattern='^delete_workout$'))
    app.add_handler(CallbackQueryHandler(confirm_delete_workout, pattern='^delete_workout_\\d+$'))
    app.add_handler(CallbackQueryHandler(delete_all_workouts_handler, pattern='^delete_all_workouts$'))
    app.add_handler(CallbackQueryHandler(confirm_delete_all_handler, pattern='^confirm_delete_all$'))
    app.add_handler(CallbackQueryHandler(display_stats, pattern='^stats_(month|halfyear|year)$'))
    app.add_handler(CallbackQueryHandler(back, pattern='^back$'))
    app.add_handler(CallbackQueryHandler(back_to_cat, pattern='^back_to_cat$'))
    app.add_handler(CallbackQueryHandler(back_to_stats, pattern='^back_to_stats$'))
    
    # Обработчик текстовых сообщений (включая групповые чаты)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input))
    
    logging.info("Бот запущен!")
    app.run_polling()

if __name__ == '__main__':
    main()