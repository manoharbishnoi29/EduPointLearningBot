import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================
# SETTINGS
# =========================

TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", "10000"))

# Tumhara Telegram User ID
ADMIN_ID = 6775287183


# =========================
# RENDER WEB SERVER
# =========================

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"EduPoint Learning Bot is running!")

    def log_message(self, format, *args):
        pass


def start_web_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    server.serve_forever()


# =========================
# START COMMAND
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton(
                "📚 Study Material",
                callback_data="study"
            ),
            InlineKeyboardButton(
                "🎥 Videos",
                callback_data="videos"
            ),
        ],
        [
            InlineKeyboardButton(
                "📝 Notes",
                callback_data="notes"
            ),
            InlineKeyboardButton(
                "🖼️ Photos",
                callback_data="photos"
            ),
        ],
        [
            InlineKeyboardButton(
                "❓ Quiz",
                callback_data="quiz"
            ),
            InlineKeyboardButton(
                "ℹ️ About",
                callback_data="about"
            ),
        ],
    ]

    # Admin ke liye extra button
    if update.effective_user.id == ADMIN_ID:
        keyboard.append([
            InlineKeyboardButton(
                "🔐 Admin Panel",
                callback_data="admin"
            )
        ])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🎓 Welcome to EduPoint Learning Bot!\n\n"
        "📚 Educational videos, notes, photos aur "
        "study material yahan milega.\n\n"
        "👇 Neeche se option choose karo:",
        reply_markup=reply_markup,
    )


# =========================
# BUTTON HANDLER
# =========================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    data = query.data

    # -------------------------
    # STUDY MATERIAL
    # -------------------------

    if data == "study":

        keyboard = [
            [
                InlineKeyboardButton(
                    "🎥 Videos",
                    callback_data="videos"
                )
            ],
            [
                InlineKeyboardButton(
                    "📝 Notes",
                    callback_data="notes"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 Main Menu",
                    callback_data="home"
                )
            ],
        ]

        await query.edit_message_text(
            "📚 Study Material\n\n"
            "Yahan educational study material milega.\n\n"
            "👇 Category choose karo:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # -------------------------
    # VIDEOS
    # -------------------------

    elif data == "videos":

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔙 Main Menu",
                    callback_data="home"
                )
            ]
        ]

        await query.edit_message_text(
            "🎥 Educational Videos\n\n"
            "Abhi videos add nahi kiye gaye hain.\n\n"
            "Jaldi hi yahan educational videos "
            "available honge. 📚",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # -------------------------
    # NOTES
    # -------------------------

    elif data == "notes":

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔙 Main Menu",
                    callback_data="home"
                )
            ]
        ]

        await query.edit_message_text(
            "📝 Notes\n\n"
            "Abhi notes add nahi kiye gaye hain.\n\n"
            "Jaldi hi study notes available honge. 📖",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # -------------------------
    # PHOTOS
    # -------------------------

    elif data == "photos":

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔙 Main Menu",
                    callback_data="home"
                )
            ]
        ]

        await query.edit_message_text(
            "🖼️ Educational Photos\n\n"
            "Educational images yahan add ki jayengi.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # -------------------------
    # QUIZ
    # -------------------------

    elif data == "quiz":

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔙 Main Menu",
                    callback_data="home"
                )
            ]
        ]

        await query.edit_message_text(
            "❓ Quiz\n\n"
            "Quiz system jaldi add kiya jayega. 🧠",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # -------------------------
    # ABOUT
    # -------------------------

    elif data == "about":

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔙 Main Menu",
                    callback_data="home"
                )
            ]
        ]

        await query.edit_message_text(
            "🎓 EduPoint Learning Bot\n\n"
            "Educational content ke liye banaya gaya hai.\n\n"
            "📚 Study Material\n"
            "🎥 Educational Videos\n"
            "📝 Notes\n"
            "🖼️ Educational Photos\n"
            "❓ Quiz",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # -------------------------
    # ADMIN PANEL
    # -------------------------

    elif data == "admin":

        if query.from_user.id != ADMIN_ID:
            await query.edit_message_text(
                "⛔ Access denied."
            )
            return

        keyboard = [
            [
                InlineKeyboardButton(
                    "🎥 Add Video",
                    callback_data="add_video"
                )
            ],
            [
                InlineKeyboardButton(
                    "🖼️ Add Photo",
                    callback_data="add_photo"
                )
            ],
            [
                InlineKeyboardButton(
                    "📝 Add Note",
                    callback_data="add_note"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 Main Menu",
                    callback_data="home"
                )
            ],
        ]

        await query.edit_message_text(
            "🔐 Admin Panel\n\n"
            "Yahan se tum educational content manage kar sakte ho.\n\n"
            "👇 Option choose karo:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # -------------------------
    # ADD VIDEO
    # -------------------------

    elif data == "add_video":

        if query.from_user.id != ADMIN_ID:
            return

        await query.edit_message_text(
            "🎥 Add Video\n\n"
            "Is feature ko next update mein connect karenge.\n\n"
            "Uske baad tum Telegram se directly "
            "video upload kar sakoge."
        )

    # -------------------------
    # ADD PHOTO
    # -------------------------

    elif data == "add_photo":

        if query.from_user.id != ADMIN_ID:
            return

        await query.edit_message_text(
            "🖼️ Add Photo\n\n"
            "Is feature ko next update mein connect karenge."
        )

    # -------------------------
    # ADD NOTE
    # -------------------------

    elif data == "add_note":

        if query.from_user.id != ADMIN_ID:
            return

        await query.edit_message_text(
            "📝 Add Note\n\n"
            "Is feature ko next update mein connect karenge."
        )

    # -------------------------
    # HOME
    # -------------------------

    elif data == "home":

        keyboard = [
            [
                InlineKeyboardButton(
                    "📚 Study Material",
                    callback_data="study"
                ),
                InlineKeyboardButton(
                    "🎥 Videos",
                    callback_data="videos"
                ),
            ],
            [
                InlineKeyboardButton(
                    "📝 Notes",
                    callback_data="notes"
                ),
                InlineKeyboardButton(
                    "🖼️ Photos",
                    callback_data="photos"
                ),
            ],
            [
                InlineKeyboardButton(
                    "❓ Quiz",
                    callback_data="quiz"
                ),
                InlineKeyboardButton(
                    "ℹ️ About",
                    callback_data="about"
                ),
            ],
        ]

        if query.from_user.id == ADMIN_ID:
            keyboard.append([
                InlineKeyboardButton(
                    "🔐 Admin Panel",
                    callback_data="admin"
                )
            ])

        await query.edit_message_text(
            "🎓 EduPoint Learning Bot\n\n"
            "👇 Option choose karo:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


# =========================
# AUTOMATIC REPLY
# =========================

async def automatic_reply(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message or not update.message.text:
        return

    message = update.message.text.lower().strip()

    if message in ["hi", "hello", "hey", "hii"]:
        await update.message.reply_text(
            "👋 Hello!\n\n"
            "🎓 EduPoint Learning Bot mein welcome hai.\n"
            "Educational content ke liye /start dabao."
        )

    elif "help" in message or "madad" in message:
        await update.message.reply_text(
            "🆘 Help\n\n"
            "Educational content dekhne ke liye /start command use karo."
        )

    elif "video" in message:
        await update.message.reply_text(
            "🎥 Educational Videos ke liye /start dabao "
            "aur Videos option select karo."
        )

    elif "note" in message:
        await update.message.reply_text(
            "📝 Notes ke liye /start dabao "
            "aur Notes option select karo."
        )

    elif "study" in message or "padhai" in message:
        await update.message.reply_text(
            "📚 Study Material ke liye /start dabao."
        )

    else:
        await update.message.reply_text(
            "🤖 Message mil gaya!\n\n"
            "🎓 EduPoint mein educational content "
            "dekhne ke liye /start dabao."
        )


# =========================
# MAIN
# =========================

def main():

    if not TOKEN:
        raise ValueError(
            "BOT_TOKEN environment variable nahi mila!"
        )

    # Render web server
    threading.Thread(
        target=start_web_server,
        daemon=True
    ).start()

    # Telegram bot
    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CallbackQueryHandler(button_handler)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            automatic_reply
        )
    )

    print("🎓 EduPoint Learning Bot started!")

    app.run_polling()


if __name__ == "__main__":
    main()
