import os
import random
import asyncio
import logging
from dotenv import load_dotenv
import httpx
import anthropic
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

anthropic_client = anthropic.Anthropic(
    api_key=ANTHROPIC_API_KEY,
    http_client=httpx.Client(proxy="socks5://127.0.0.1:9050"),
)

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [["😂 Шутка", "🤯 Факт"], ["🌍 Переводчик"]],
    resize_keyboard=True
)

LANGUAGE_KEYBOARD = ReplyKeyboardMarkup(
    [["🇬🇧 Английский", "🇪🇸 Испанский"], ["🇩🇪 Немецкий", "🇫🇷 Французский"], ["🇨🇳 Китайский", "🇯🇵 Японский"], ["⬅️ Назад"]],
    resize_keyboard=True
)

user_state = {}


async def call_anthropic(**kwargs):
    return await asyncio.to_thread(anthropic_client.messages.create, **kwargs)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_state[update.effective_user.id] = None
    await update.message.reply_text(
        "Привет! Я многофункциональный бот 😄\n\nВыбери что хочешь:",
        reply_markup=MAIN_KEYBOARD
    )


JOKE_TOPICS = [
    'животные', 'работа', 'еда', 'школа', 'технологии', 'спорт',
    'семья', 'путешествия', 'деньги', 'погода', 'врачи', 'политика',
    'программисты', 'студенты', 'дети', 'пенсионеры', 'автомобили', 'рыбалка'
]

FACT_TOPICS = [
    'космос', 'животные', 'история', 'еда', 'технологии', 'человеческое тело',
    'океан', 'растения', 'древние цивилизации', 'математика', 'музыка',
    'спорт', 'архитектура', 'насекомые', 'химия', 'география', 'кино', 'язык'
]


async def get_joke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    topic = random.choice(JOKE_TOPICS)
    await update.message.reply_text("Придумываю шутку...", reply_markup=MAIN_KEYBOARD)
    try:
        message = await call_anthropic(
            model="claude-sonnet-4-6",
            max_tokens=300,
            temperature=1,
            messages=[{"role": "user", "content": f"Расскажи одну смешную короткую шутку на русском языке на тему '{topic}'. Только шутку, без лишних слов."}],
        )
        await update.message.reply_text(message.content[0].text, reply_markup=MAIN_KEYBOARD)
    except Exception as e:
        logger.error("Ошибка при запросе шутки: %s", e)
        await update.message.reply_text("Что-то пошло не так, попробуй ещё раз.", reply_markup=MAIN_KEYBOARD)


async def get_fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    topic = random.choice(FACT_TOPICS)
    await update.message.reply_text("Ищу интересный факт...", reply_markup=MAIN_KEYBOARD)
    try:
        message = await call_anthropic(
            model="claude-sonnet-4-6",
            max_tokens=300,
            temperature=1,
            messages=[{"role": "user", "content": f"Расскажи один удивительный факт на тему '{topic}'. Только сам факт, без лишних слов."}],
        )
        await update.message.reply_text(message.content[0].text, reply_markup=MAIN_KEYBOARD)
    except Exception as e:
        logger.error("Ошибка при запросе факта: %s", e)
        await update.message.reply_text("Что-то пошло не так, попробуй ещё раз.", reply_markup=MAIN_KEYBOARD)


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
        try:
            message = await call_anthropic(
                model="claude-sonnet-4-6",
                max_tokens=500,
                messages=[{"role": "user", "content": f"Переведи следующий текст на {language} язык. Только перевод, без пояснений:\n\n{text}"}],
            )
            await update.message.reply_text(
                message.content[0].text,
                reply_markup=ReplyKeyboardMarkup([["⬅️ Назад"]], resize_keyboard=True)
            )
        except Exception as e:
            logger.error("Ошибка при переводе: %s", e)
            await update.message.reply_text("Что-то пошло не так, попробуй ещё раз.", reply_markup=ReplyKeyboardMarkup([["⬅️ Назад"]], resize_keyboard=True))


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Необработанная ошибка: %s", context.error, exc_info=context.error)


app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))
app.add_error_handler(error_handler)

print("Бот запущен!")
app.run_polling()
