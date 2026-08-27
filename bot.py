import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TOKEN = os.getenv("BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("📚 Study Material", callback_data="study"),
            InlineKeyboardButton("🎥 Videos", callback_data="videos"),
        ],
        [
            InlineKeyboardButton("📝 Notes", callback_data="notes"),
            InlineKeyboardButton("ℹ️ About", callback_data="about"),
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🎓 Welcome to EduPoint Learning Bot!\n\n"
        "यहाँ आपको educational videos, notes और study material मिलेगा।\n\n"
        "नीचे से एक option चुनें 👇",
        reply_markup=reply_markup,
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "study":
        text = "📚 Study Material\n\nअभी study material जल्द जोड़ा जाएगा।"

    elif query.data == "videos":
        text = "🎥 Educational Videos\n\nअभी videos जल्द जोड़े जाएंगे।"

    elif query.data == "notes":
        text = "📝 Notes\n\nअभी notes जल्द जोड़े जाएंगे।"

    elif query.data == "about":
        text = (
            "🎓 EduPoint Learning Bot\n\n"
            "Educational content के लिए बनाया गया है।"
        )

    else:
        text = "कुछ गड़बड़ हो गई।"

    await query.edit_message_text(text)


def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN environment variable नहीं मिला!")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("EduPoint Learning Bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()
