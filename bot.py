import os
import json
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

# =========================================================
# SETTINGS
# =========================================================

TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", "10000"))

# Tumhara Telegram User ID
ADMIN_ID = 6775287183

DATA_FILE = "content.json"


# =========================================================
# DATA
# =========================================================

def load_content():
    if not os.path.exists(DATA_FILE):
        return []

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_content(content):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=2)


content_list = load_content()


# =========================================================
# RENDER WEB SERVER
# =========================================================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(
            b"EduPoint Learning Bot is running!"
        )

    def log_message(self, format, *args):
        pass


def start_web_server():
    server = HTTPServer(
        ("0.0.0.0", PORT),
        HealthHandler
    )
    server.serve_forever()


# =========================================================
# MAIN MENU
# =========================================================

def main_menu(user_id):

    keyboard = [
        [
            InlineKeyboardButton(
                "📚 Study Material",
                callback_data="study"
            )
        ],
        [
            InlineKeyboardButton(
                "🎥 Videos",
                callback_data="videos"
            ),
            InlineKeyboardButton(
                "📝 Notes",
                callback_data="notes"
            )
        ],
        [
            InlineKeyboardButton(
                "🖼️ Photos",
                callback_data="photos"
            ),
            InlineKeyboardButton(
                "❓ Quiz",
                callback_data="quiz"
            )
        ],
        [
            InlineKeyboardButton(
                "ℹ️ About",
                callback_data="about"
            )
        ],
    ]

    if user_id == ADMIN_ID:
        keyboard.append([
            InlineKeyboardButton(
                "🔐 Admin Panel",
                callback_data="admin"
            )
        ])

    return InlineKeyboardMarkup(keyboard)


# =========================================================
# START
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data.clear()

    await update.message.reply_text(
        "🎓 Welcome to EduPoint Learning Bot!\n\n"
        "📚 Educational videos, notes, photos aur "
        "study material yahan milega.\n\n"
        "👇 Neeche se option choose karo:",
        reply_markup=main_menu(
            update.effective_user.id
        )
    )


# =========================================================
# STUDY MATERIAL
# =========================================================

async def show_study(update, context):

    query = update.callback_query
    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton(
                "🎥 Videos",
                callback_data="videos"
            )
        ],
        [
            InlineKeyboardButton(
                "📝 Notes / PDFs",
                callback_data="notes"
            )
        ],
        [
            InlineKeyboardButton(
                "🖼️ Photos",
                callback_data="photos"
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
        "Apni category choose karo:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# SHOW CONTENT
# =========================================================

async def show_content(update, context, content_type):

    query = update.callback_query
    await query.answer()

    items = [
        item for item in content_list
        if item["type"] == content_type
    ]

    if not items:

        keyboard = [[
            InlineKeyboardButton(
                "🔙 Main Menu",
                callback_data="home"
            )
        ]]

        names = {
            "video": "🎥 Videos",
            "document": "📝 Notes / PDFs",
            "photo": "🖼️ Photos",
        }

        await query.edit_message_text(
            f"{names[content_type]}\n\n"
            "Abhi yahan koi content available nahi hai.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    keyboard = []

    for item in items:
        keyboard.append([
            InlineKeyboardButton(
                item["title"],
                callback_data=f"open_{item['id']}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "🔙 Main Menu",
            callback_data="home"
        )
    ])

    names = {
        "video": "🎥 Videos",
        "document": "📝 Notes / PDFs",
        "photo": "🖼️ Photos",
    }

    await query.edit_message_text(
        f"{names[content_type]}\n\n"
        "Content choose karo:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# OPEN CONTENT
# =========================================================

async def open_content(update, context):

    query = update.callback_query
    await query.answer()

    try:
        item_id = int(
            query.data.replace("open_", "")
        )
    except ValueError:
        return

    item = next(
        (
            x for x in content_list
            if x["id"] == item_id
        ),
        None
    )

    if not item:
        await query.message.reply_text(
            "❌ Content nahi mila."
        )
        return

    caption = (
        f"🎓 {item['title']}\n\n"
        "📚 EduPoint Learning Bot"
    )

    if item["type"] == "video":

        await query.message.reply_video(
            video=item["file_id"],
            caption=caption
        )

    elif item["type"] == "photo":

        await query.message.reply_photo(
            photo=item["file_id"],
            caption=caption
        )

    elif item["type"] == "document":

        await query.message.reply_document(
            document=item["file_id"],
            caption=caption
        )


# =========================================================
# ADMIN PANEL
# =========================================================

async def show_admin(update, context):

    query = update.callback_query
    await query.answer()

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
                "📄 Add PDF / Note",
                callback_data="add_document"
            )
        ],
        [
            InlineKeyboardButton(
                "🗑️ Delete Content",
                callback_data="delete_content"
            )
        ],
        [
            InlineKeyboardButton(
                "📊 Content Count",
                callback_data="content_count"
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
        "Yahan se tum Telegram se directly "
        "educational content add kar sakte ho.\n\n"
        "👇 Option choose karo:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# ADD CONTENT - START
# =========================================================

async def start_add_video(update, context):

    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    context.user_data["admin_action"] = "video"

    await query.edit_message_text(
        "🎥 Add Video\n\n"
        "Ab mujhe ek educational video bhejo.\n\n"
        "Video receive hone ke baad main uska title puchunga."
    )


async def start_add_photo(update, context):

    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    context.user_data["admin_action"] = "photo"

    await query.edit_message_text(
        "🖼️ Add Photo\n\n"
        "Ab mujhe educational photo bhejo."
    )


async def start_add_document(update, context):

    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    context.user_data["admin_action"] = "document"

    await query.edit_message_text(
        "📄 Add PDF / Note\n\n"
        "Ab mujhe PDF ya document bhejo."
    )


# =========================================================
# RECEIVE VIDEO / PHOTO / DOCUMENT
# =========================================================

async def receive_media(update, context):

    if update.effective_user.id != ADMIN_ID:
        return

    action = context.user_data.get("admin_action")

    if not action:
        return

    file_id = None
    media_type = None

    if action == "video" and update.message.video:

        file_id = update.message.video.file_id
        media_type = "video"

    elif action == "photo" and update.message.photo:

        file_id = update.message.photo[-1].file_id
        media_type = "photo"

    elif action == "document" and update.message.document:

        file_id = update.message.document.file_id
        media_type = "document"

    else:
        await update.message.reply_text(
            "⚠️ Please wahi file type bhejo "
            "jo tumne select ki hai."
        )
        return

    context.user_data["pending_file_id"] = file_id
    context.user_data["pending_type"] = media_type
    context.user_data["admin_action"] = "title"

    await update.message.reply_text(
        "✅ File receive ho gayi!\n\n"
        "Ab iska **title** bhejo.\n\n"
        "Example:\n"
        "Biology Chapter 1"
    )


# =========================================================
# SAVE TITLE
# =========================================================

async def receive_title(update, context):

    if update.effective_user.id != ADMIN_ID:
        return

    if context.user_data.get("admin_action") != "title":
        return

    title = update.message.text.strip()

    if not title:
        await update.message.reply_text(
            "❌ Title khali nahi ho sakta."
        )
        return

    file_id = context.user_data.get(
        "pending_file_id"
    )

    media_type = context.user_data.get(
        "pending_type"
    )

    if not file_id or not media_type:
        await update.message.reply_text(
            "❌ File information nahi mili. "
            "Dobara Add Content karo."
        )
        context.user_data.clear()
        return

    new_id = (
        max(
            [x["id"] for x in content_list],
            default=0
        )
        + 1
    )

    item = {
        "id": new_id,
        "type": media_type,
        "title": title,
        "file_id": file_id,
    }

    content_list.append(item)
    save_content(content_list)

    context.user_data.clear()

    await update.message.reply_text(
        "✅ Content successfully save ho gaya! 🎉\n\n"
        f"📌 Title: {title}\n"
        f"📁 Type: {media_type}\n\n"
        "Ab ye students ko menu mein dikhai dega.",
        reply_markup=main_menu(ADMIN_ID)
    )


# =========================================================
# DELETE CONTENT
# =========================================================

async def show_delete_content(update, context):

    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    if not content_list:

        await query.edit_message_text(
            "🗑️ Delete Content\n\n"
            "Abhi koi content available nahi hai."
        )
        return

    keyboard = []

    for item in content_list:

        keyboard.append([
            InlineKeyboardButton(
                f"🗑️ {item['title']}",
                callback_data=f"delete_{item['id']}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "🔙 Admin Panel",
            callback_data="admin"
        )
    ])

    await query.edit_message_text(
        "🗑️ Delete Content\n\n"
        "Jis content ko delete karna hai "
        "uspar tap karo:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def delete_content(update, context):

    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    try:
        item_id = int(
            query.data.replace("delete_", "")
        )
    except ValueError:
        return

    global content_list

    old_length = len(content_list)

    content_list = [
        x for x in content_list
        if x["id"] != item_id
    ]

    if len(content_list) == old_length:

        await query.edit_message_text(
            "❌ Content nahi mila."
        )
        return

    save_content(content_list)

    await query.edit_message_text(
        "✅ Content delete ho gaya.",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🔙 Admin Panel",
                    callback_data="admin"
                )
            ]
        ])
    )


# =========================================================
# CONTENT COUNT
# =========================================================

async def content_count(update, context):

    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    videos = sum(
        1 for x in content_list
        if x["type"] == "video"
    )

    photos = sum(
        1 for x in content_list
        if x["type"] == "photo"
    )

    documents = sum(
        1 for x in content_list
        if x["type"] == "document"
    )

    await query.edit_message_text(
        "📊 EduPoint Content\n\n"
        f"🎥 Videos: {videos}\n"
        f"🖼️ Photos: {photos}\n"
        f"📄 Notes/PDFs: {documents}\n"
        f"📚 Total: {len(content_list)}",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🔙 Admin Panel",
                    callback_data="admin"
                )
            ]
        ])
    )


# =========================================================
# AUTOMATIC REPLY
# =========================================================

async def automatic_reply(update, context):

    if not update.message or not update.message.text:
        return

    # Admin title mode ko pehle handle karo
    if (
        update.effective_user.id == ADMIN_ID
        and context.user_data.get("admin_action")
        == "title"
    ):
        await receive_title(update, context)
        return

    text = update.message.text.lower().strip()

    if text in ["hi", "hello", "hey", "hii", "namaste"]:

        await update.message.reply_text(
            "👋 Hello!\n\n"
            "🎓 EduPoint Learning Bot mein welcome hai!\n\n"
            "📚 Educational content ke liye /start dabao."
        )

    elif "video" in text:

        await update.message.reply_text(
            "🎥 Educational videos dekhne ke liye "
            "/start dabao aur Videos select karo."
        )

    elif "note" in text or "pdf" in text:

        await update.message.reply_text(
            "📝 Notes/PDFs ke liye /start dabao."
        )

    elif "photo" in text or "image" in text:

        await update.message.reply_text(
            "🖼️ Educational photos ke liye "
            "/start dabao."
        )

    elif "study" in text or "padhai" in text:

        await update.message.reply_text(
            "📚 Study Material ke liye /start dabao."
        )

    elif "help" in text or "madad" in text:

        await update.message.reply_text(
            "🆘 Help\n\n"
            "Educational content dekhne ke liye "
            "/start use karo."
        )

    else:

        await update.message.reply_text(
            "🤖 Message mil gaya!\n\n"
            "🎓 EduPoint mein educational content "
            "dekhne ke liye /start dabao."
        )


# =========================================================
# CALLBACK ROUTER
# =========================================================

async def callback_router(update, context):

    query = update.callback_query
    data = query.data

    if data == "home":
        await query.answer()

        context.user_data.clear()

        await query.edit_message_text(
            "🎓 EduPoint Learning Bot\n\n"
            "👇 Option choose karo:",
            reply_markup=main_menu(
                query.from_user.id
            )
        )

    elif data == "study":
        await show_study(update, context)

    elif data == "videos":
        await show_content(
            update,
            context,
            "video"
        )

    elif data == "notes":
        await show_content(
            update,
            context,
            "document"
        )

    elif data == "photos":
        await show_content(
            update,
            context,
            "photo"
        )

    elif data == "quiz":
        await query.answer()

        await query.edit_message_text(
            "❓ Quiz\n\n"
            "Quiz system next update mein add karenge.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 Main Menu",
                        callback_data="home"
                    )
                ]
            ])
        )

    elif data == "about":
        await query.answer()

        await query.edit_message_text(
            "🎓 EduPoint Learning Bot\n\n"
            "📚 Educational videos\n"
            "📝 Notes & PDFs\n"
            "🖼️ Educational photos\n"
            "❓ Quiz\n\n"
            "Learning made easier! 🚀",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 Main Menu",
                        callback_data="home"
                    )
                ]
            ])
        )

    elif data == "admin":
        await show_admin(update, context)

    elif data == "add_video":
        await start_add_video(update, context)

    elif data == "add_photo":
        await start_add_photo(update, context)

    elif data == "add_document":
        await start_add_document(update, context)

    elif data == "delete_content":
        await show_delete_content(update, context)

    elif data == "content_count":
        await content_count(update, context)

    elif data.startswith("open_"):
        await open_content(update, context)

    elif data.startswith("delete_"):
        await delete_content(update, context)


# =========================================================
# MAIN
# =========================================================

def main():

    if not TOKEN:
        raise ValueError(
            "BOT_TOKEN environment variable nahi mila!"
        )

    # Render Web Service ke liye HTTP server
    threading.Thread(
        target=start_web_server,
        daemon=True
    ).start()

    # Telegram application
    app = Application.builder().token(TOKEN).build()

    # Commands
    app.add_handler(
        CommandHandler("start", start)
    )

    # Buttons
    app.add_handler(
        CallbackQueryHandler(callback_router)
    )

    # Videos / Photos / Documents
    app.add_handler(
        MessageHandler(
            (
                filters.VIDEO
                | filters.PHOTO
                | filters.Document.ALL
            ),
            receive_media
        )
    )

    # Normal text messages
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            automatic_reply
        )
    )

    print("🎓 EduPoint Learning Bot started!")

    app.run_polling()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()
