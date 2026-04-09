import os
import logging
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, 
    ContextTypes, MessageHandler, filters, ConversationHandler
)
from database_with_ai import (
    create_tables, get_exercises_by_category, add_exercise, delete_exercise, 
    modify_exercise, get_exercise_by_id, generate_weight_chart,
    get_weight_history, get_all_categories, update_user_visit, days_since_last_visit
)
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def escape_markdown_v2(text):
    """Экранирование для MarkdownV2"""
    chars = '_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{c}' if c in chars else c for c in str(text))

create_tables()

# ============ AI ============

async def get_ai_response(message_text, prompt_type='greeting'):
    """AI от Groq"""
    if not GROQ_API_KEY:
        return None
    
    prompts = {
        'greeting': 'Ты крутой фитнес-тренер. Ответь кратко на русском.',
        'motivation': 'Дай мотивирующую фразу на русском!',
        'tips': 'Дай совет по технике упражнений!',
    }
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "messages": [
            {"role": "system", "content": prompts.get(prompt_type, prompts['greeting'])},
            {"role": "user", "content": message_text}
        ],
        "model": "llama-3.1-8b-instant",
        "temperature": 0.7,
        "max_tokens": 200
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data, timeout=10) as response:
                if response.status == 200:
                    result = await response.json()
                    return result['choices'][0]['message']['content']
    except Exception as e:
        logging.error(f"AI Error: {e}")
    return None

# ============ HANDLERS ============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню"""
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    update_user_visit(user_id, username)
    context.user_data.clear()
    
    buttons = [
        [InlineKeyboardButton("💪 Грудь", callback_data='cat_Грудь и бицепс'),
         InlineKeyboardButton("🏋️ Спина", callback_data='cat_Спина и трицепс')],
        [InlineKeyboardButton("🦵 Ноги", callback_data='cat_Ноги и плечи')],
        [InlineKeyboardButton("📊 Графики", callback_data='charts'),
         InlineKeyboardButton("🤖 AI", callback_data='ai_menu')],
    ]
    
    text = (
        escape_markdown_v2("💪 ФИТНЕС-БОТ v4.0\n\n") +
        escape_markdown_v2(f"Привет, {username}!\n\n") +
        escape_markdown_v2("Выбери категорию:")
    )
    
    reply_markup = InlineKeyboardMarkup(buttons)
    
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='MarkdownV2')
    else:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='MarkdownV2')

async def select_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор категории"""
    query = update.callback_query
    await query.answer()
    
    category = query.data.split('_', 1)[1]
    context.user_data['category'] = category
    
    exercises = get_exercises_by_category(category)
    
    buttons = []
    for ex_id, ex_name, weight in exercises:
        buttons.append([InlineKeyboardButton(f"🏋️ {ex_name} ({weight}kg)", callback_data=f'ex_{ex_id}')])
    
    buttons.append([
        InlineKeyboardButton("➕ Добавить", callback_data='add'),
        InlineKeyboardButton("🔙 Назад", callback_data='back')
    ])
    
    reply_markup = InlineKeyboardMarkup(buttons)
    text = escape_markdown_v2(f"📊 {category}\n\nУпражнения ({len(exercises)}):")
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='MarkdownV2')

async def select_exercise(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню упражнения"""
    query = update.callback_query
    await query.answer()
    
    ex_id = int(query.data.split('_')[1])
    ex = get_exercise_by_id(ex_id)
    
    if not ex:
        return
    
    context.user_data['ex_id'] = ex_id
    context.user_data['ex_name'] = ex[1]
    context.user_data['ex_weight'] = ex[2]
    
    buttons = [
        [InlineKeyboardButton("✏️ Изменить", callback_data='edit_weight'),
         InlineKeyboardButton("📈 История", callback_data='history')],
        [InlineKeyboardButton("📊 График", callback_data='chart')],
        [InlineKeyboardButton("❌ Удалить", callback_data='delete'),
         InlineKeyboardButton("🔙 Назад", callback_data='back_cat')]
    ]
    
    text = escape_markdown_v2(f"🏋️ {ex[1]}\n⚖️ Вес: {ex[2]}kg")
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode='MarkdownV2')

async def edit_weight_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало редактирования"""
    query = update.callback_query
    await query.answer()
    
    text = escape_markdown_v2("Введи новый вес (кг):")
    await query.edit_message_text(text, parse_mode='MarkdownV2')
    
    return "WAIT_WEIGHT"

async def edit_weight_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохранение нового веса"""
    try:
        new_weight = float(update.message.text.strip())
        ex_id = context.user_data['ex_id']
        ex_name = context.user_data['ex_name']
        
        modify_exercise(ex_id, str(new_weight))
        
        text = escape_markdown_v2(f"✅ Сохранено!\n\n🏋️ {ex_name}\n⚖️ {new_weight}kg")
        
        buttons = [[InlineKeyboardButton("🔙 Назад", callback_data='back')]]
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode='MarkdownV2')
        
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text(escape_markdown_v2("❌ Введи число!"), parse_mode='MarkdownV2')
        return "WAIT_WEIGHT"

async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """История весов"""
    query = update.callback_query
    await query.answer("⏳", show_alert=False)
    
    ex_id = context.user_data['ex_id']
    ex_name = context.user_data['ex_name']
    history = get_weight_history(ex_id)
    
    if not history:
        text = escape_markdown_v2(f"📊 {ex_name}\n⚠️ История пуста")
    else:
        text = escape_markdown_v2(f"📊 {ex_name}\n\n")
        for date, weight in history:
            text += escape_markdown_v2(f"  {date} → {weight}kg\n")
    
    buttons = [[InlineKeyboardButton("🔙 Назад", callback_data='back_ex')]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode='MarkdownV2')

async def show_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """График"""
    query = update.callback_query
    await query.answer("⏳ Строю...", show_alert=False)
    
    ex_id = context.user_data['ex_id']
    ex_name = context.user_data['ex_name']
    category = context.user_data['category']
    
    history = get_weight_history(ex_id)
    if len(history) < 2:
        await query.answer("❌ Мало данных", show_alert=True)
        return
    
    chart = generate_weight_chart(ex_id, ex_name, category)
    if not chart:
        await query.answer("❌ Ошибка", show_alert=True)
        return
    
    chart.seek(0)
    buttons = [[InlineKeyboardButton("🔙 Назад", callback_data='back_ex')]]
    await query.message.reply_photo(chart, caption=escape_markdown_v2(f"📊 {ex_name}"), 
                                    reply_markup=InlineKeyboardMarkup(buttons), parse_mode='MarkdownV2')
    try:
        await query.delete_message()
    except:
        pass

async def ai_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню AI"""
    query = update.callback_query
    await query.answer()
    
    buttons = [
        [InlineKeyboardButton("💪 Мотивация", callback_data='ai_mot')],
        [InlineKeyboardButton("🎯 Советы", callback_data='ai_tips')],
        [InlineKeyboardButton("❓ Вопрос", callback_data='ai_q')],
        [InlineKeyboardButton("🔙 Назад", callback_data='back')],
    ]
    
    text = escape_markdown_v2("🤖 AI Коуч\n\nЧто нужно?")
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode='MarkdownV2')

async def ai_motivation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """AI мотивация"""
    query = update.callback_query
    await query.answer("⏳", show_alert=False)
    
    response = await get_ai_response("Дай мотивирующую фразу!", "motivation")
    text = escape_markdown_v2(f"💪 {response or 'Давай качаться!'}")
    
    buttons = [[InlineKeyboardButton("🔙 Назад", callback_data='ai_menu')]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode='MarkdownV2')

async def delete_exercise(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удалить упражнение"""
    query = update.callback_query
    ex_id = context.user_data['ex_id']
    ex_name = context.user_data['ex_name']
    
    delete_exercise(ex_id)
    
    text = escape_markdown_v2(f"✅ {ex_name} удалено")
    buttons = [[InlineKeyboardButton("🔙 Назад", callback_data='back')]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode='MarkdownV2')

async def back_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Назад"""
    await start(update, context)

async def back_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Назад к категории"""
    await select_category(update, context)

# ============ MAIN ============

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    edit_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_weight_start, pattern='edit_weight')],
        states={"WAIT_WEIGHT": [MessageHandler(filters.TEXT, edit_weight_done)]},
        fallbacks=[],
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(edit_conv)
    app.add_handler(CallbackQueryHandler(select_category, pattern='^cat_'))
    app.add_handler(CallbackQueryHandler(select_exercise, pattern='^ex_'))
    app.add_handler(CallbackQueryHandler(show_history, pattern='history'))
    app.add_handler(CallbackQueryHandler(show_chart, pattern='chart'))
    app.add_handler(CallbackQueryHandler(ai_menu, pattern='ai_menu'))
    app.add_handler(CallbackQueryHandler(ai_motivation, pattern='ai_mot'))
    app.add_handler(CallbackQueryHandler(delete_exercise, pattern='delete'))
    app.add_handler(CallbackQueryHandler(back_button, pattern='back$'))
    app.add_handler(CallbackQueryHandler(back_category, pattern='back_cat'))
    
    logging.info("🚀 Бот запущен!")
    app.run_polling()

if __name__ == '__main__':
    main()
