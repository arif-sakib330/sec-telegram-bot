from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import json
import os
import hashlib

BOT_TOKEN = "8467552861:AAGpZNcMDAyaGgmcxIu0sPSHd8UFgW9Iwk8"
ALLOWED_GROUP_ID = -1003060280470
ADMIN_ID = 6314175930
FILES_JSON = "files.json"
WEBSITE_LINK = "https://www.example.com"

if os.path.exists(FILES_JSON):
    with open(FILES_JSON, "r") as f:
        FILES = json.load(f)
else:
    FILES = {
        "4th Semester (2-2)": {
            "Solid 2": {},
            "Fluid Mechanics": {},
            "Geology": {},
            "GIS": {},
            "Math": {},
            "Hydrology": {},
            "Quantity Survey": {},
            "Fluid Sessional": {},
        },
        "5th Semester (3-1)": {},
        "6th Semester (3-2)": {},
        "7th Semester (4-1)": {},
        "8th Semester (4-2)": {},
    }

user_paths = {}
user_parents = {}
admin_actions = {}
callback_map = {}
file_type_map = {}


def make_callback_data(prefix, name):
    """Generate short safe callback_data using hash"""
    h = hashlib.md5(name.encode()).hexdigest()[:10]
    callback_map[h] = name
    return f"{prefix}|{h}"


def get_name_from_hash(h):
    return callback_map.get(h)


def get_file_type(file_name):
    ext = file_name.lower()
    if ext.endswith((".jpg", ".jpeg", ".png", ".gif")):
        return "photo"
    elif ext.endswith((".mp4", ".mov", ".mkv")):
        return "video"
    else:
        return "document"


async def is_member(user_id, context):
    try:
        member = await context.bot.get_chat_member(ALLOWED_GROUP_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if not await is_member(user_id, context):
        await update.message.reply_text("❌ তুমি গ্রুপের মেম্বার নও। আগে গ্রুপে জয়েন করো।")
        return

    user_paths[chat_id] = FILES
    user_parents[chat_id] = []

    await update.message.reply_text(f"🎉 SEC CE – 09 Bot-এ স্বাগতম! 🎉")
    await list_items(update, context, FILES, chat_id, is_root=True)


async def upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    chat_id = update.effective_chat.id

    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ শুধুমাত্র এডমিন ফাইল আপলোড করতে পারবে।")
        return

    current_folder = user_paths.get(chat_id)
    if current_folder is None:
        await update.message.reply_text(
            "❌ প্রথমে /start দিয়ে কোনো সেমিস্টারে প্রবেশ করো।"
        )
        return

    await update.message.reply_text(
        "📤 ফাইল আপলোড করো এখানে। বট স্বয়ংক্রিয়ভাবে সেভ করবে।"
    )


async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    chat_id = update.effective_chat.id

    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ শুধুমাত্র এডমিন ফাইল আপলোড করতে পারবে।")
        return

    current_folder = user_paths.get(chat_id)
    if current_folder is None:
        await update.message.reply_text(
            "❌ প্রথমে /start দিয়ে কোনো সেমিস্টারে প্রবেশ করো।"
        )
        return

    file_id = None
    file_name = None
    file_type = "document"

    if update.message.document:
        file_name = update.message.document.file_name
        file_id = update.message.document.file_id
        file_type = "document"
    elif update.message.photo:
        photo = update.message.photo[-1]
        file_name = f"photo_{photo.file_id}.jpg"
        file_id = photo.file_id
        file_type = "photo"
    elif update.message.video:
        video = update.message.video
        file_name = video.file_name if video.file_name else f"video_{video.file_id}.mp4"
        file_id = video.file_id
        file_type = "video"

    if file_id and file_name:
        current_folder[file_name] = file_id
        file_type_map[file_name] = file_type
        with open(FILES_JSON, "w") as f:
            json.dump(FILES, f, indent=4)
        await update.message.reply_text(f"✅ {file_name} আপলোড হয়েছে।")
    else:
        await update.message.reply_text("❌ এই ফাইল টাইপ সাপোর্টেড নয়।")


async def create_or_rename_folder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text
    action = admin_actions.get(chat_id, None)
    if not action:
        return
    current_folder = user_paths.get(chat_id, FILES)
    if action["type"] == "create":
        if text in current_folder:
            await update.message.reply_text("❌ ফোল্ডার আগে থেকেই আছে।")
        else:
            current_folder[text] = {}
            with open(FILES_JSON, "w") as f:
                json.dump(FILES, f, indent=4)
            await update.message.reply_text(f"✅ {text} ফোল্ডার তৈরি হয়েছে।")
    elif action["type"] == "rename":
        old_name = action["old_name"]
        if text in current_folder:
            await update.message.reply_text("❌ এই নাম আগে থেকেই আছে।")
        else:
            current_folder[text] = current_folder.pop(old_name)
            if old_name in file_type_map:
                file_type_map[text] = file_type_map.pop(old_name)
            with open(FILES_JSON, "w") as f:
                json.dump(FILES, f, indent=4)
            await update.message.reply_text(f"✅ {old_name} রিনেইম হয়ে {text} হয়েছে।")
    admin_actions.pop(chat_id, None)


async def list_items(update, context, current_dict, chat_id, is_root=False):
    keyboard = []
    user_id = update.effective_user.id
    is_admin = user_id == ADMIN_ID

    if user_parents[chat_id]:
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="BACK")])
    else:
        keyboard.append([InlineKeyboardButton("🏠 Main", callback_data="MAIN")])

    for key, value in current_dict.items():
        row = []
        if isinstance(value, dict):
            row.append(
                InlineKeyboardButton(
                    f"📂 {key}", callback_data=make_callback_data("FOLDER", key)
                )
            )
            if is_admin:
                row.append(
                    InlineKeyboardButton(
                        "⚙", callback_data=make_callback_data("OPTIONS", key)
                    )
                )
        else:
            row.append(
                InlineKeyboardButton(
                    f"📄 {key}", callback_data=make_callback_data("FILE", key)
                )
            )
        keyboard.append(row)

    if is_admin:
        keyboard.append([InlineKeyboardButton("➕ New Folder", callback_data="CREATE")])

    await (
        update.message.reply_text
        if update.message
        else update.callback_query.edit_message_text
    )("📚 Select a folder or file:", reply_markup=InlineKeyboardMarkup(keyboard))


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    chat_id = query.message.chat.id
    if not await is_member(user_id, context):
        await query.answer("❌ তুমি গ্রুপের মেম্বার নও!")
        return
    await query.answer()

    current_dict = user_paths.get(chat_id, FILES)
    parent_stack = user_parents.get(chat_id, [])
    is_admin = user_id == ADMIN_ID
    data = query.data

    if data == "MAIN":
        user_paths[chat_id] = FILES
        user_parents[chat_id] = []
        await list_items(update, context, FILES, chat_id, is_root=True)
    elif data == "BACK":
        if parent_stack:
            previous = parent_stack.pop()
            user_paths[chat_id] = previous
            await list_items(
                update, context, previous, chat_id, is_root=(previous == FILES)
            )
        else:
            user_paths[chat_id] = FILES
            await list_items(update, context, FILES, chat_id, is_root=True)
    elif data.startswith("FOLDER"):
        _, h = data.split("|", 1)
        folder_name = get_name_from_hash(h)
        if folder_name in current_dict and isinstance(current_dict[folder_name], dict):
            user_parents[chat_id].append(current_dict)
            user_paths[chat_id] = current_dict[folder_name]
            await list_items(update, context, current_dict[folder_name], chat_id)
    elif data.startswith("FILE"):
        _, h = data.split("|", 1)
        file_name = get_name_from_hash(h)
        file_id = current_dict.get(file_name)
        if file_id:
            ftype = file_type_map.get(file_name, "document")
            if ftype == "photo":
                await query.message.reply_photo(file_id)
            elif ftype == "video":
                await query.message.reply_video(file_id)
            elif ftype == "audio":
                await query.message.reply_audio(file_id)
            else:
                await query.message.reply_document(file_id)
    elif data == "CREATE" and is_admin:
        admin_actions[chat_id] = {"type": "create"}
        await query.message.reply_text("📝 নতুন ফোল্ডারের নাম লিখো:")
    elif data.startswith("OPTIONS") and is_admin:
        _, h = data.split("|", 1)
        folder_name = get_name_from_hash(h)
        keyboard = [
            [InlineKeyboardButton("🗑️ Delete", callback_data=f"DELETE|{folder_name}")],
            [InlineKeyboardButton("✏️ Rename", callback_data=f"RENAME|{folder_name}")],
            [InlineKeyboardButton("⬆️ Move Up", callback_data=f"MOVE_UP|{folder_name}")],
            [
                InlineKeyboardButton(
                    "⬇️ Move Down", callback_data=f"MOVE_DOWN|{folder_name}"
                )
            ],
        ]
        await query.message.reply_text(
            f"⚙️ {folder_name} Options:", reply_markup=InlineKeyboardMarkup(keyboard)
        )
    elif data.startswith("DELETE") and is_admin:
        _, folder_name = data.split("|", 1)
        if folder_name in current_dict:
            current_dict.pop(folder_name)
            with open(FILES_JSON, "w") as f:
                json.dump(FILES, f, indent=4)
            await query.message.reply_text(f"✅ {folder_name} ডিলিট হয়েছে।")
        await list_items(update, context, current_dict, chat_id)
    elif data.startswith("RENAME") and is_admin:
        _, folder_name = data.split("|", 1)
        admin_actions[chat_id] = {"type": "rename", "old_name": folder_name}
        await query.message.reply_text(f"✏️ {folder_name} নতুন নাম লিখো:")
    elif data.startswith("MOVE_UP") and is_admin:
        _, folder_name = data.split("|", 1)
        keys = list(current_dict.keys())
        idx = keys.index(folder_name)
        if idx > 0:
            keys[idx], keys[idx - 1] = keys[idx - 1], keys[idx]
            new_dict = {k: current_dict[k] for k in keys}
            current_dict.clear()
            current_dict.update(new_dict)
            with open(FILES_JSON, "w") as f:
                json.dump(FILES, f, indent=4)
        await list_items(update, context, current_dict, chat_id)
    elif data.startswith("MOVE_DOWN") and is_admin:
        _, folder_name = data.split("|", 1)
        keys = list(current_dict.keys())
        idx = keys.index(folder_name)
        if idx < len(keys) - 1:
            keys[idx], keys[idx + 1] = keys[idx + 1], keys[idx]
            new_dict = {k: current_dict[k] for k in keys}
            current_dict.clear()
            current_dict.update(new_dict)
            with open(FILES_JSON, "w") as f:
                json.dump(FILES, f, indent=4)
        await list_items(update, context, current_dict, chat_id)


app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("upload", upload))
app.add_handler(
    MessageHandler(
        filters.Document.ALL | filters.PHOTO | filters.VIDEO | filters.AUDIO,
        handle_file,
    )
)
app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, create_or_rename_folder)
)
app.add_handler(CallbackQueryHandler(button_handler))

print("Bot is running...")
app.run_polling()
