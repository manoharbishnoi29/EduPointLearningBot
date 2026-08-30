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


# =========================================================
# CONTENT DATABASE
# =========================================================

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


# =========================================================
# QUIZ DATABASE
# =========================================================

def get_quiz_names():

    result = (
        supabase
        .table("quizzes")
        .select("quiz_name")
        .order("quiz_name")
        .execute()
    )

    names = []

    for item in result.data or []:

        name = item.get("quiz_name")

        if name and name not in names:
            names.append(name)

    return names


def get_quiz_questions(quiz_name):

    result = (
        supabase
        .table("quizzes")
        .select("*")
        .eq("quiz_name", quiz_name)
        .order("question_number", desc=False)
        .execute()
    )

    return result.data or []


def save_quiz_question(
    quiz_name,
    question,
    option_a,
    option_b,
    option_c,
    option_d,
    correct_answer,
    question_number
):

    return (
        supabase
        .table("quizzes")
        .insert({
            "quiz_name": quiz_name,
            "question": question,
            "option_a": option_a,
            "option_b": option_b,
            "option_c": option_c,
            "option_d": option_d,
            "correct_answer": correct_answer,
            "question_number": question_number
        })
        .execute()
    )


def delete_quiz_question(question_id):

    return (
        supabase
        .table("quizzes")
        .delete()
        .eq("id", question_id)
        .execute()
    )


# =========================================================
# MAIN MENU
# =========================================================

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


# =========================================================
# SHOW CONTENT
# =========================================================

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


# =========================================================
# OPEN CONTENT
# =========================================================

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


# =========================================================
# ADMIN PANEL
# =========================================================

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
                "❓ Add Quiz",
                callback_data="add_quiz"
            )
        ],
        [
            InlineKeyboardButton(
                "🗑️ Delete Quiz",
                callback_data="delete_quiz"
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


# =========================================================
# ADD VIDEO
# =========================================================

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


# =========================================================
# ADD PHOTO
# =========================================================

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


# =========================================================
# ADD DOCUMENT
# =========================================================

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


# =========================================================
# RECEIVE FILE
# =========================================================

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


# =========================================================
# SAVE CONTENT
# =========================================================

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


# =========================================================
# QUIZ USER MENU
# =========================================================

async def quiz_menu(update, context):

    query = update.callback_query
    await query.answer()

    try:

        names = get_quiz_names()

    except Exception as e:

        print("QUIZ DATABASE ERROR:", e)

        await query.edit_message_text(
            "❌ Quiz database load nahi ho pa raha."
        )

        return

    if not names:

        await query.edit_message_text(
            "❓ Quiz\n\n"
            "Abhi koi quiz available nahi hai.",
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

    for index, name in enumerate(names):

        keyboard.append([
            InlineKeyboardButton(
                f"🧬 {name}",
                callback_data=f"qselect_{index}"
            )
        ])

    context.user_data["quiz_names"] = names

    keyboard.append([
        InlineKeyboardButton(
            "🔙 Main Menu",
            callback_data="home"
        )
    ])

    await query.edit_message_text(
        "❓ Quiz\n\n"
        "Kiski quiz deni hai? 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# START QUIZ
# =========================================================

async def start_quiz(update, context):

    query = update.callback_query
    await query.answer()

    try:

        index = int(
            query.data.replace(
                "qselect_",
                ""
            )
        )

        names = context.user_data.get(
            "quiz_names",
            []
        )

        if index >= len(names):

            await query.edit_message_text(
                "❌ Quiz nahi mili."
            )

            return

        quiz_name = names[index]

        questions = get_quiz_questions(
            quiz_name
        )

        if not questions:

            await query.edit_message_text(
                "❌ Is quiz mein questions nahi hain."
            )

            return

        context.user_data["quiz_name"] = quiz_name
        context.user_data["quiz_questions"] = questions
        context.user_data["quiz_index"] = 0
        context.user_data["quiz_score"] = 0

        await send_quiz_question(
            query.message,
            context
        )

    except Exception as e:

        print("START QUIZ ERROR:", e)

        await query.edit_message_text(
            "❌ Quiz start nahi ho paayi."
        )


# =========================================================
# SEND QUESTION
# =========================================================

async def send_quiz_question(message, context):

    questions = context.user_data.get(
        "quiz_questions",
        []
    )

    index = context.user_data.get(
        "quiz_index",
        0
    )

    if index >= len(questions):

        score = context.user_data.get(
            "quiz_score",
            0
        )

        total = len(questions)

        quiz_name = context.user_data.get(
            "quiz_name",
            "Quiz"
        )

        await message.reply_text(
            "🎉 Quiz Complete!\n\n"
            f"🧬 {quiz_name}\n"
            f"🏆 Score: {score}/{total}\n\n"
            "Great job! 👏",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🔄 Quiz Menu",
                        callback_data="quiz"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🏠 Main Menu",
                        callback_data="home"
                    )
                ]
            ])
        )

        return

    question = questions[index]

    keyboard = [
        [
            InlineKeyboardButton(
                f"A. {question['option_a']}",
                callback_data="answer_A"
            )
        ],
        [
            InlineKeyboardButton(
                f"B. {question['option_b']}",
                callback_data="answer_B"
            )
        ],
        [
            InlineKeyboardButton(
                f"C. {question['option_c']}",
                callback_data="answer_C"
            )
        ],
        [
            InlineKeyboardButton(
                f"D. {question['option_d']}",
                callback_data="answer_D"
            )
        ]
    ]

    await message.reply_text(
        f"❓ Question {index + 1}/{len(questions)}\n\n"
        f"{question['question']}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# CHECK QUIZ ANSWER
# =========================================================

async def check_quiz_answer(update, context):

    query = update.callback_query
    await query.answer()

    questions = context.user_data.get(
        "quiz_questions",
        []
    )

    index = context.user_data.get(
        "quiz_index",
        0
    )

    if not questions or index >= len(questions):

        await query.message.reply_text(
            "❌ Quiz session khatam ho gayi."
        )

        return

    selected = query.data.replace(
        "answer_",
        ""
    ).upper()

    question = questions[index]

    correct = str(
        question["correct_answer"]
    ).strip().upper()

    if selected == correct:

        context.user_data["quiz_score"] = (
            context.user_data.get(
                "quiz_score",
                0
            ) + 1
        )

        result_text = "✅ Correct answer! 🎉"

    else:

        result_text = (
            "❌ Wrong answer.\n"
            f"Correct answer: {correct}"
        )

    await query.edit_message_text(
        result_text
    )

    context.user_data["quiz_index"] = index + 1

    await send_quiz_question(
        query.message,
        context
    )


# =========================================================
# ADMIN ADD QUIZ
# =========================================================

async def add_quiz(update, context):

    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    context.user_data.clear()

    context.user_data["action"] = "quiz_name"

    await query.edit_message_text(
        "❓ Add Quiz\n\n"
        "Pehle quiz ka naam bhejo.\n\n"
        "Example:\n"
        "Biology 1"
    )


# =========================================================
# ADMIN QUIZ TEXT FLOW
# =========================================================

async def handle_quiz_text(update, context):

    if update.effective_user.id != ADMIN_ID:
        return False

    action = context.user_data.get(
        "action"
    )

    if action not in [
        "quiz_name",
        "quiz_question",
        "quiz_option_a",
        "quiz_option_b",
        "quiz_option_c",
        "quiz_option_d",
        "quiz_correct"
    ]:
        return False

    text = update.message.text.strip()

    if action == "quiz_name":

        context.user_data["quiz_name"] = text
        context.user_data["action"] = "quiz_question"

        await update.message.reply_text(
            "✅ Quiz name save ho gaya.\n\n"
            "Ab Question 1 bhejo."
        )

        return True

    if action == "quiz_question":

        context.user_data["quiz_question"] = text
        context.user_data["action"] = "quiz_option_a"

        await update.message.reply_text(
            "Ab option A bhejo."
        )

        return True

    if action == "quiz_option_a":

        context.user_data["quiz_option_a"] = text
        context.user_data["action"] = "quiz_option_b"

        await update.message.reply_text(
            "Ab option B bhejo."
        )

        return True

    if action == "quiz_option_b":

        context.user_data["quiz_option_b"] = text
        context.user_data["action"] = "quiz_option_c"

        await update.message.reply_text(
            "Ab option C bhejo."
        )

        return True

    if action == "quiz_option_c":

        context.user_data["quiz_option_c"] = text
        context.user_data["action"] = "quiz_option_d"

        await update.message.reply_text(
            "Ab option D bhejo."
        )

        return True

    if action == "quiz_option_d":

        context.user_data["quiz_option_d"] = text
        context.user_data["action"] = "quiz_correct"

        await update.message.reply_text(
            "Ab correct answer bhejo.\n\n"
            "Sirf A, B, C ya D likho."
        )

        return True

    if action == "quiz_correct":

        correct = text.upper()

        if correct not in [
            "A",
            "B",
            "C",
            "D"
        ]:

            await update.message.reply_text(
                "⚠️ Sirf A, B, C ya D likho."
            )

            return True

        quiz_name = context.user_data["quiz_name"]

        existing = get_quiz_questions(
            quiz_name
        )

        question_number = len(existing) + 1

        try:

            save_quiz_question(
                quiz_name,
                context.user_data["quiz_question"],
                context.user_data["quiz_option_a"],
                context.user_data["quiz_option_b"],
                context.user_data["quiz_option_c"],
                context.user_data["quiz_option_d"],
                correct,
                question_number
            )

            context.user_data.clear()

            keyboard = [
                [
                    InlineKeyboardButton(
                        "➕ Add Another Question",
                        callback_data="add_quiz"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔐 Admin Panel",
                        callback_data="admin"
                    )
                ]
            ]

            await update.message.reply_text(
                "✅ Question successfully save ho gaya! 🎉\n\n"
                f"🧬 Quiz: {quiz_name}\n"
                f"📝 Question: {question_number}\n"
                f"✅ Correct answer: {correct}",
                reply_markup=InlineKeyboardMarkup(
                    keyboard
                )
            )

        except Exception as e:

            print("QUIZ SAVE ERROR:", e)

            await update.message.reply_text(
                "❌ Quiz database mein save nahi ho payi."
            )

        return True

    return False


# =========================================================
# DELETE QUIZ MENU
# =========================================================

async def delete_quiz_menu(update, context):

    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    try:

        result = (
            supabase
            .table("quizzes")
            .select("*")
            .order("quiz_name")
            .order("question_number")
            .execute()
        )

        questions = result.data or []

    except Exception as e:

        print("DELETE QUIZ ERROR:", e)

        await query.edit_message_text(
            "❌ Quiz database error."
        )

        return

    if not questions:

        await query.edit_message_text(
            "🗑️ Quiz Delete\n\n"
            "Abhi koi quiz nahi hai.",
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

    for question in questions:

        label = (
            f"🗑️ {question['quiz_name']} - "
            f"Q{question['question_number']}"
        )

        keyboard.append([
            InlineKeyboardButton(
                label,
                callback_data=f"qdelete_{question['id']}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "🔙 Admin Panel",
            callback_data="admin"
        )
    ])

    await query.edit_message_text(
        "🗑️ Quiz Delete\n\n"
        "Jis question ko delete karna hai tap karo:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def delete_quiz_item(update, context):

    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    try:

        question_id = int(
            query.data.replace(
                "qdelete_",
                ""
            )
        )

        delete_quiz_question(
            question_id
        )

        await query.edit_message_text(
            "✅ Quiz question delete ho gaya.",
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

        print("DELETE QUIZ ITEM ERROR:", e)

        await query.edit_message_text(
            "❌ Quiz question delete nahi ho paya."
        )


# =========================================================
# DELETE CONTENT
# =========================================================

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


# =========================================================
# CONTENT COUNT
# =========================================================

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

        quiz_result = (
            supabase
            .table("quizzes")
            .select("id", count="exact")
            .execute()
        )

        quiz_count = quiz_result.count or 0

        await query.edit_message_text(
            "📊 Content Statistics\n\n"
            f"🎥 Videos: {videos}\n"
            f"🖼️ Photos: {photos}\n"
            f"📄 Notes/PDFs: {documents}\n"
            f"❓ Quiz Questions: {quiz_count}\n"
            f"📚 Total Content: {len(items)}",
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


# =========================================================
# AUTOMATIC REPLY
# =========================================================

async def automatic_reply(update, context):

    if not update.message:
        return

    if update.effective_user.id == ADMIN_ID:

        handled = await handle_quiz_text(
            update,
            context
        )

        if handled:
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

        await quiz_menu(
            update,
            context
        )

    elif data.startswith("qselect_"):

        await start_quiz(
            update,
            context
        )

    elif data.startswith("answer_"):

        await check_quiz_answer(
            update,
            context
        )

    elif data == "about":

        await query.answer()

        await query.edit_message_text(
            "🎓 EduPoint Learning Bot\n\n"
            "📚 Educational Videos\n"
            "📝 Notes & PDFs\n"
            "🖼️ Educational Photos\n"
            "❓ Interactive Quiz",
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

    elif data == "add_quiz":

        await add_quiz(
            update,
            context
        )

    elif data == "delete_quiz":

        await delete_quiz_menu(
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

    elif data.startswith("qdelete_"):

        await delete_quiz_item(
            update,
            context
        )

    elif data.startswith("delete_"):

        await delete_item(
            update,
            context
        )


# =========================================================
# MAIN
# =========================================================

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
