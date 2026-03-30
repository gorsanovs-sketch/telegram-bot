import os
from pathlib import Path
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

BASE_DIR = Path(__file__).resolve().parent

FOLDERS = {
    "Instrukcijas": BASE_DIR / "Instrukcijas",
    "Tehniku autoparks": BASE_DIR / "Tehniku_autoparks",
    "Veidlapas": BASE_DIR / "Veidlapas",
}

BACK_BUTTON = "⬅️ Atpakaļ"
MAIN_MENU_BUTTON = "🏠 Galvenā izvēlne"


def build_main_menu() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton("Instrukcijas"), KeyboardButton("Tehniku autoparks")],
        [KeyboardButton("Veidlapas")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def build_folder_menu(folder_name: str, files: list[str]) -> ReplyKeyboardMarkup:
    keyboard = []

    for file_name in files:
        keyboard.append([KeyboardButton(f"📄 {file_name}")])

    keyboard.append([KeyboardButton(BACK_BUTTON), KeyboardButton(MAIN_MENU_BUTTON)])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_files_from_folder(folder_path: Path) -> list[str]:
    if not folder_path.exists() or not folder_path.is_dir():
        return []

    files = [f.name for f in folder_path.iterdir() if f.is_file()]
    files.sort()
    return files


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["current_folder"] = None
    await update.message.reply_text(
        "Sveicināti! Izvēlieties sadaļu:",
        reply_markup=build_main_menu(),
    )


async def show_folder(update: Update, context: ContextTypes.DEFAULT_TYPE, folder_name: str):
    folder_path = FOLDERS[folder_name]
    files = get_files_from_folder(folder_path)

    context.user_data["current_folder"] = folder_name

    if not files:
        await update.message.reply_text(
            f"Sadaļā '{folder_name}' faili nav atrasti.",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton(BACK_BUTTON), KeyboardButton(MAIN_MENU_BUTTON)]],
                resize_keyboard=True,
            ),
        )
        return

    await update.message.reply_text(
        f"Izvēlieties failu no sadaļas '{folder_name}':",
        reply_markup=build_folder_menu(folder_name, files),
    )


async def send_selected_file(update: Update, context: ContextTypes.DEFAULT_TYPE, file_name: str):
    current_folder = context.user_data.get("current_folder")

    if not current_folder or current_folder not in FOLDERS:
        await update.message.reply_text(
            "Vispirms izvēlieties sadaļu.",
            reply_markup=build_main_menu(),
        )
        return

    folder_path = FOLDERS[current_folder]
    file_path = folder_path / file_name

    if not file_path.exists() or not file_path.is_file():
        await update.message.reply_text(
            "Fails nav atrasts.",
            reply_markup=build_main_menu(),
        )
        return

    with open(file_path, "rb") as file_to_send:
        await update.message.reply_document(document=file_to_send)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()

    if text == "Instrukcijas":
        await show_folder(update, context, "Instrukcijas")
        return

    if text == "Tehniku autoparks":
        await show_folder(update, context, "Tehniku autoparks")
        return

    if text == "Veidlapas":
        await show_folder(update, context, "Veidlapas")
        return

    if text == BACK_BUTTON or text == MAIN_MENU_BUTTON:
        context.user_data["current_folder"] = None
        await update.message.reply_text(
            "Galvenā izvēlne:",
            reply_markup=build_main_menu(),
        )
        return

    if text.startswith("📄 "):
        file_name = text.replace("📄 ", "", 1).strip()
        await send_selected_file(update, context, file_name)
        return

    await update.message.reply_text(
        "Nesapratu komandu. Izvēlieties sadaļu no izvēlnes.",
        reply_markup=build_main_menu(),
    )


def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN nav atrasts Railway variables.")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()


if __name__ == "__main__":
    main()
