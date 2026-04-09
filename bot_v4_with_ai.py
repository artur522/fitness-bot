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
    get_weight_history, get_all_categories, update_user_visit
)
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")

def escape_markdown_v2(text):
    chars = '_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{c}' if c in chars else c for c in str(text))

create_tables()

async def get_ai_response(message_text, prompt_type='greeting'):
    if not GROQ_API_KEY:
        return None
    
    prompts = {
        'greeting': 'Ты крутой фитнес-тренер. Ответь кратко.',
        'motivation': 'Дай мотивирующую фразу!',
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    update_user_visit(user_id, username)
    context.user_data.clear()
    
    buttons = [
        [InlineKeyboardButton("Chest", callback_data='cat_chest'),
         InlineKeyboardButton("Back", callback_data='cat_back')],
        [InlineKeyboardButton("Legs", callback_data='cat_legs')],
        [InlineKeyboardButton("History", callback_data='history'),
         InlineKeyboardButton("AI", callback_data='ai_menu')],
    ]
    
    text = escape_markdown_v2("FITNESS BOT v4.0\n\nHello!\n\nChoose category:")
    reply_markup = InlineKeyboardMarkup(buttons)
    
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='MarkdownV2')
    else:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='MarkdownV2')

async def select_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    cat_map = {
        'cat_chest': 'Грудь и бицепс',
        'cat_back': 'Спина и трицепс',
        'cat_legs': 'Ноги и плечи'
    }
    
    category = cat_map.get(query.data, 'Грудь и бицепс')
    context.user_data['category'] = category
    
    exercises = get_exercises_by_category(category)
    
    buttons = []
    for ex_id, ex_name, weight in exercises:
        buttons.append([InlineKeyboardButton(f"{ex_name} ({weight})", callback_data=f'ex_{ex_id}')])
    
    buttons.append([InlineKeyboardButton("Back", callback_data='back')])
    
    reply_markup = InlineKeyboardMarkup(buttons)
    text = escape_markdown_v2(f"{category}")
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='MarkdownV2')

async def select_exercise(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        [InlineKeyboardButton("Edit", callback_data='edit'),
         InlineKeyboardButton("History", callback_data='hist')],
        [InlineKeyboardButton("Chart", callback_data='chart')],
        [InlineKeyboardButton("Back", callback_data='back')]
    ]
    
    text = escape_markdown_v2(f"{ex[1]}\n{ex[2]}kg")
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode='MarkdownV2')

async def edit_weight_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(escape_markdown_v2("Enter weight:"), parse_mode='MarkdownV2')
    return "WAIT_WEIGHT"

async def edit_weight_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        new_weight = float(update.message.text.strip())
        ex_id = context.user_data['ex_id']
        ex_name = context.user_data['ex_name']
        
        modify_exercise(ex_id, str(new_weight))
        text = escape_markdown_v2(f"Saved! {ex_name} {new_weight}kg")
        buttons = [[InlineKeyboardButton("Back", callback_data='back')]]
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode='MarkdownV2')
        
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text(escape_markdown_v2("Invalid!"), parse_mode='MarkdownV2')
        return "WAIT_WEIGHT"

async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    ex_id = context.user_data.get('ex_id')
    if not ex_id:
        return
    
    ex_name = context.user_data['ex_name']
    history = get_weight_history(ex_id)
    
    if not history:
        text = escape_markdown_v2(f"{ex_name}\nNo history")
    else:
        msg = f"{ex_name}\n"
        for date, weight in history[-5:]:
            msg += f"{date} {weight}kg\n"
        text = escape_markdown_v2(msg)
    
    buttons = [[InlineKeyboardButton("Back", callback_data='back')]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode='MarkdownV2')

async def show_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    ex_id = context.user_data.get('ex_id')
    if not ex_id:
        return
    
    ex_name = context.user_data['ex_name']
    category = context.user_data['category']
    history = get_weight_history(ex_id)
    
    if len(history) < 2:
        await query.answer("Not enough data", show_alert=True)
        return
    
    chart = generate_weight_chart(ex_id, ex_name, category)
    if not chart:
        await query.answer("Error", show_alert=True)
        return
    
    chart.seek(0)
    buttons = [[InlineKeyboardButton("Back", callback_data='back')]]
    await query.message.reply_photo(chart, caption=escape_markdown_v2(f"{ex_name}"), 
                                    reply_markup=InlineKeyboardMarkup(buttons), parse_mode='MarkdownV2')
    try:
        await query.delete_message()
    except:
        pass

async def ai_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    buttons = [
        [InlineKeyboardButton("Motivation", callback_data='ai_mot')],
        [InlineKeyboardButton("Tips", callback_data='ai_tips')],
        [InlineKeyboardButton("Back", callback_data='back')],
    ]
    
    text = escape_markdown_v2("AI Coach")
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode='MarkdownV2')

async def ai_motivation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    response = await get_ai_response("Motivate me!", "motivation")
    text = escape_markdown_v2(response or "Lets go!")
    
    buttons = [[InlineKeyboardButton("Back", callback_data='ai_menu')]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode='MarkdownV2')

async def back_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    edit_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_weight_start, pattern='edit')],
        states={"WAIT_WEIGHT": [MessageHandler(filters.TEXT, edit_weight_done)]},
        fallbacks=[],
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(edit_conv)
    app.add_handler(CallbackQueryHandler(select_category, pattern='^cat_'))
    app.add_handler(CallbackQueryHandler(select_exercise, pattern='^ex_'))
    app.add_handler(CallbackQueryHandler(show_history, pattern='hist'))
    app.add_handler(CallbackQueryHandler(show_chart, pattern='chart'))
    app.add_handler(CallbackQueryHandler(ai_menu, pattern='ai_menu'))
    app.add_handler(CallbackQueryHandler(ai_motivation, pattern='ai_mot'))
    app.add_handler(CallbackQueryHandler(back_button, pattern='back$'))
    
    logging.info("Bot started!")
    app.run_polling()

if __name__ == '__main__':
    main()
