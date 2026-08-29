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

from supabase import create_client


# =========================
# SETTINGS
# =========================

TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

PORT = int(os.getenv("PORT", "10000"))

# Tumhara Telegram ID
ADMIN_ID = 6775287183


# =========================
# CHECK SETTINGS
# =========================

if not TOKEN:
    raise ValueError("BOT_TOKEN missing")

if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL missing")

if not SUPABASE_KEY:
    raise ValueError("SUPABASE_KEY missing")


# =========================
# SUPABASE
# =========================

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# =========================
# RENDER HEALTH SERVER
# =========================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header(
            "Content-Type",
            "text/plain"
        )
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


# =========================
# DATABASE
# =========================

def get_content():

    result = (
        supabase
        .table("content")
        .select("*")
        .order("id", desc=False)
        .execute()
    )

    return result.data or []


def save_content(title, content_type, file_id):

    metadata = {
        "type": content_type,
        "file_id": file_id
    }

    return (
        supabase
        .table("content")
        .insert({
            "title": title,
            "description": json.dumps(metadata)
        })
        .execute()
    )


def delete_content_db(content_id):

    return (
        supabase
        .table("content")
        .delete()
        .eq("id", content_id)
        .execute()
    )


def get_metadata(item):

    try:
        return json.loads(
            item.get("description") or "{}"
        )
    except Exception:
        return {}


# =========================
# MAIN MENU
# =========================

def main_menu(user_id):

    buttons = [
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
            )
        ],
        [
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
        ]
    ]

    if user_id == ADMIN_ID:
        buttons.append([
            InlineKeyboardButton(
                "🔐 Admin Panel",
                callback_data="admin"
            )
        ])

    return InlineKeyboardMarkup(buttons)


# =========================
# START
# =========================

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


# =========================
# STUDY MATERIAL
# =========================

async def study_material(update, context):

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
        ]
    ]

    await query.edit_message_text(
        "📚 Study Material\n\n"
        "Category choose karo:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# SHOW CONTENT
# =========================

async def show_content(update, context, content_type):

    query = update.callback_query
    await query.answer()

    try:
        items = get_content()

    except Exception as e:

        print("DATABASE ERROR:", e)

        await query.edit_message_text(
            "❌ Database se content load nahi ho pa raha."
        )

        return

    matching = []

    for item in items:

        metadata = get_metadata(item)

        if metadata.get("type") == content_type:
            matching.append(item)

    titles = {
        "video": "🎥 Videos",
        "photo": "🖼️ Photos",
        "document": "📝 Notes / PDFs"
    }

    heading = titles.get(
        content_type,
        "📚 Content"
    )

    if not matching:

        await query.edit_message_text(
            f"{heading}\n\n"
            "Abhi koi content available nahi hai.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 Main Menu",
                        callback_data="home"
                    )
                ]
            ])
        )

        return

    keyboard = []

    for item in matching:

        keyboard.append([
            InlineKeyboardButton(
                f"📌 {item['title']}",
                callback_data=f"open_{item['id']}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "🔙 Main Menu",
            callback_data="home"
        )
    ])

    await query.edit_message_text(
        heading + "\n\n"
        "Content choose karo:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# OPEN CONTENT
# =========================

async def open_content(update, context):

    query = update.callback_query
    await query.answer()

    try:

        content_id = int(
            query.data.replace(
                "open_",
                ""
            )
        )

        result = (
            supabase
            .table("content")
            .select("*")
            .eq("id", content_id)
            .execute()
        )

        items = result.data or []

        if not items:

            await query.message.reply_text(
                "❌ Content nahi mila."
            )

            return

        item = items[0]

        metadata = get_metadata(item)

        content_type = metadata.get("type")
        file_id = metadata.get("file_id")

        caption = (
            f"🎓 {item['title']}\n\n"
            "📚 EduPoint Learning Bot"
        )

        if content_type == "video":

            await query.message.reply_video(
                video=file_id,
                caption=caption
            )

        elif content_type == "photo":

            await query.message.reply_photo(
                photo=file_id,
                caption=caption
            )

        elif content_type == "document":

            await query.message.reply_document(
                document=file_id,
                caption=caption
            )

    except Exception as e:

        print("OPEN CONTENT ERROR:", e)

        await query.message.reply_text(
            "❌ Content open nahi ho paya."
        )


# =========================
# ADMIN PANEL
# =========================

async def admin_panel(update, context):

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
        ]
    ]

    await query.edit_message_text(
        "🔐 Admin Panel\n\n"
        "Content manage karo:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# ADD VIDEO
# =========================

async def add_video(update, context):

    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    context.user_data.clear()

    context.user_data["action"] = "video"

    await query.edit_message_text(
        "🎥 Add Video\n\n"
        "Ab video bhejo."
    )


# =========================
# ADD PHOTO
# =========================

async def add_photo(update, context):

    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    context.user_data.clear()

    context.user_data["action"] = "photo"

    await query.edit_message_text(
        "🖼️ Add Photo\n\n"
        "Ab photo bhejo."
    )


# =========================
# ADD DOCUMENT
# =========================

async def add_document(update, context):

    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    context.user_data.clear()

    context.user_data["action"] = "document"

    await query.edit_message_text(
        "📄 Add PDF / Note\n\n"
        "Ab PDF ya document bhejo."
    )


# =========================
# RECEIVE FILE
# =========================

async def receive_file(update, context):

    if update.effective_user.id != ADMIN_ID:
        return

    action = context.user_data.get("action")

    if action not in [
        "video",
        "photo",
        "document"
    ]:
        return

    file_id = None
    content_type = None

    if action == "video":

        if not update.message.video:

            await update.message.reply_text(
                "⚠️ Video bhejo."
            )

            return

        file_id = update.message.video.file_id
        content_type = "video"

    elif action == "photo":

        if not update.message.photo:

            await update.message.reply_text(
                "⚠️ Photo bhejo."
            )

            return

        file_id = update.message.photo[-1].file_id
        content_type = "photo"

    elif action == "document":

        if not update.message.document:

            await update.message.reply_text(
                "⚠️ PDF/document bhejo."
            )

            return

        file_id = update.message.document.file_id
        content_type = "document"

    context.user_data["file_id"] = file_id
    context.user_data["content_type"] = content_type
    context.user_data["action"] = "title"

    await update.message.reply_text(
        "✅ File receive ho gayi!\n\n"
        "Ab iska title bhejo."
    )


# =========================
# SAVE CONTENT
# =========================

async def save_title(update, context):

    if update.effective_user.id != ADMIN_ID:
        return

    if context.user_data.get("action") != "title":
        return

    title = update.message.text.strip()

    file_id = context.user_data.get("file_id")
    content_type = context.user_data.get("content_type")

    if not file_id or not content_type:

        context.user_data.clear()

        await update.message.reply_text(
            "❌ File information missing hai."
        )

        return

    try:

        save_content(
            title,
            content_type,
            file_id
        )

        context.user_data.clear()

        await update.message.reply_text(
            "✅ Content successfully save ho gaya! 🎉\n\n"
            f"📌 {title}\n"
            "💾 Supabase database mein save hai.",
            reply_markup=main_menu(
                ADMIN_ID
            )
        )

    except Exception as e:

        print("SAVE ERROR:", e)

        await update.message.reply_text(
            "❌ Database mein save nahi ho paya."
        )


# =========================
# DELETE CONTENT
# =========================

async def delete_menu(update, context):

    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    try:

        items = get_content()

    except Exception as e:

        print("DELETE LIST ERROR:", e)

        await query.edit_message_text(
            "❌ Database error."
        )

        return

    if not items:

        await query.edit_message_text(
            "🗑️ Delete Content\n\n"
            "Abhi koi content nahi hai.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 Admin Panel",
                        callback_data="admin"
                    )
                ]
            ])
        )

        return

    keyboard = []

    for item in items:

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
        "Jise delete karna hai uspar tap karo:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def delete_item(update, context):

    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    try:

        content_id = int(
            query.data.replace(
                "delete_",
                ""
            )
        )

        delete_content_db(
            content_id
        )

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

    except Exception as e:

        print("DELETE ERROR:", e)

        await query.edit_message_text(
            "❌ Delete nahi ho paya."
        )


# =========================
# CONTENT COUNT
# =========================

async def content_count(update, context):

    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    try:

        items = get_content()

        videos = 0
        photos = 0
        documents = 0

        for item in items:

            content_type = get_metadata(
                item
            ).get("type")

            if content_type == "video":
                videos += 1

            elif content_type == "photo":
                photos += 1

            elif content_type == "document":
                documents += 1

        await query.edit_message_text(
            "📊 Content Statistics\n\n"
            f"🎥 Videos: {videos}\n"
            f"🖼️ Photos: {photos}\n"
            f"📄 Notes/PDFs: {documents}\n"
            f"📚 Total: {len(items)}",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔙 Admin Panel",
                        callback_data="admin"
                    )
                ]
            ])
        )

    except Exception as e:

        print("COUNT ERROR:", e)

        await query.edit_message_text(
            "❌ Database error."
        )


# =========================
# AUTOMATIC REPLY
# =========================

async def automatic_reply(update, context):

    if not update.message:
        return

    if (
        update.effective_user.id == ADMIN_ID
        and context.user_data.get("action") == "title"
    ):

        await save_title(
            update,
            context
        )

        return

    if not update.message.text:
        return

    text = update.message.text.lower().strip()

    if text in [
        "hi",
        "hello",
        "hey",
        "hii",
        "namaste"
    ]:

        await update.message.reply_text(
            "👋 Hello!\n\n"
            "🎓 EduPoint Learning Bot mein welcome hai!\n\n"
            "📚 /start dabao."
        )

    elif "video" in text:

        await update.message.reply_text(
            "🎥 Videos dekhne ke liye /start dabao."
        )

    elif "pdf" in text or "note" in text:

        await update.message.reply_text(
            "📝 Notes/PDFs ke liye /start dabao."
        )

    elif "photo" in text or "image" in text:

        await update.message.reply_text(
            "🖼️ Photos ke liye /start dabao."
        )

    elif "help" in text:

        await update.message.reply_text(
            "🆘 Help ke liye /start dabao."
        )


# =========================
# CALLBACK ROUTER
# =========================

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

        await study_material(
            update,
            context
        )

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
            "Quiz feature baad mein add karenge.",
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
            "📚 Educational Videos\n"
            "📝 Notes & PDFs\n"
            "🖼️ Educational Photos",
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

        await admin_panel(
            update,
            context
        )

    elif data == "add_video":

        await add_video(
            update,
            context
        )

    elif data == "add_photo":

        await add_photo(
            update,
            context
        )

    elif data == "add_document":

        await add_document(
            update,
            context
        )

    elif data == "delete_content":

        await delete_menu(
            update,
            context
        )

    elif data == "content_count":

        await content_count(
            update,
            context
        )

    elif data.startswith("open_"):

        await open_content(
            update,
            context
        )

    elif data.startswith("delete_"):

        await delete_item(
            update,
            context
        )


# =========================
# MAIN
# =========================

def main():

    threading.Thread(
        target=start_web_server,
        daemon=True
    ).start()

    app = (
        Application
        .builder()
        .token(TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            callback_router
        )
    )

    app.add_handler(
        MessageHandler(
            filters.VIDEO
            | filters.PHOTO
            | filters.Document.ALL,
            receive_file
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            automatic_reply
        )
    )

    print(
        "🎓 EduPoint Learning Bot started!"
    )

    app.run_polling()


if __name__ == "__main__":
    main()
