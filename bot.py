import os
import random
from dotenv import load_dotenv
import anthropic
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [["😂 Шутка", "🤯 Факт"], ["🌍 Переводчик"]],
    resize_keyboard=True
)

LANGUAGE_KEYBOARD = ReplyKeyboardMarkup(
    [["🇬🇧 Английский", "🇪🇸 Испанский"], ["🇩🇪 Немецкий", "🇫🇷 Французский"], ["🇨🇳 Китайский", "🇯🇵 Японский"], ["⬅️ Назад"]],
    resize_keyboard=True
)

user_state = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_state[update.effective_user.id] = None
    await update.message.reply_text(
        "Привет! Я многофункциональный бот 😄\n\nВыбери что хочешь:",
        reply_markup=MAIN_KEYBOARD
    )


async def get_joke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Придумываю шутку...", reply_markup=MAIN_KEYBOARD)
    message = anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content": "Расскажи одну смешную короткую шутку на русском языке. Только шутку, без лишних слов."}],
    )
    await update.message.reply_text(message.content[0].text, reply_markup=MAIN_KEYBOARD)


async def get_fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ищу интересный факт...", reply_markup=MAIN_KEYBOARD)
    message = anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content": f"Расскажи один интересный факт на тему: {random.choice(['космос', 'животные', 'история', 'еда', 'технологии', 'человеческое тело', 'океан', 'растения', 'древние цивилизации', 'математика'])}. Только сам факт, без лишних слов."}],
    )
    await update.message.reply_text(message.content[0].text, reply_markup=MAIN_KEYBOARD)


async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    if text == "😂 Шутка":
        user_state[user_id] = None
        await get_joke(update, context)

    elif text == "🤯 Факт":
        user_state[user_id] = None
        await get_fact(update, context)

    elif text == "🌍 Переводчик":
        user_state[user_id] = "choosing_language"
        await update.message.reply_text("Выбери язык перевода:", reply_markup=LANGUAGE_KEYBOARD)

    elif text == "⬅️ Назад":
        user_state[user_id] = None
        await update.message.reply_text("Главное меню:", reply_markup=MAIN_KEYBOARD)

    elif text in ["🇬🇧 Английский", "🇪🇸 Испанский", "🇩🇪 Немецкий", "🇫🇷 Французский", "🇨🇳 Китайский", "🇯🇵 Японский"]:
        languages = {
            "🇬🇧 Английский": "английский",
            "🇪🇸 Испанский": "испанский",
            "🇩🇪 Немецкий": "немецкий",
            "🇫🇷 Французский": "французский",
            "🇨🇳 Китайский": "китайский",
            "🇯🇵 Японский": "японский",
        }
        user_state[user_id] = {"mode": "translating", "language": languages[text]}
        await update.message.reply_text(
            f"Выбран {languages[text]} язык.\n\nНапиши текст для перевода:",
            reply_markup=ReplyKeyboardMarkup([["⬅️ Назад"]], resize_keyboard=True)
        )

    elif isinstance(user_state.get(user_id), dict) and user_state[user_id].get("mode") == "translating":
        language = user_state[user_id]["language"]
        await update.message.reply_text("Перевожу...")
        message = anthropic_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            messages=[{"role": "user", "content": f"Переведи следующий текст на {language} язык. Только перевод, без пояснений:\n\n{text}"}],
        )
        await update.message.reply_text(
            message.content[0].text,
            reply_markup=ReplyKeyboardMarkup([["⬅️ Назад"]], resize_keyboard=True)
        )


app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))

print("Бот запущен!")
app.run_polling()
