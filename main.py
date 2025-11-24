import logging
from telegram import (
    Update, ReplyKeyboardMarkup, KeyboardButton,
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes,
    filters, ConversationHandler,
)
from config import TOKEN, ADMIN_USERNAME
from keep_alive import keep_alive

import database as db
import utils

logging.basicConfig(level=logging.INFO)
db.init_db()

# States
WAITING_GAME_NAME = 1
WAITING_FULLNAME = 2
WAITING_WISHES = 3
WAITING_GAME_CHOICE = 4


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("Участвовать")],
        [KeyboardButton("Мой профиль")],
    ]

    user = update.effective_user

    # admin menu
    if user.username == ADMIN_USERNAME:
        keyboard.append([KeyboardButton("Админ-панель")])

    await update.message.reply_text(
        "Привет! Это бот Тайного Санты 🎁",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )


# ---------- ADMIN PANEL ----------
async def admin_panel(update: Update, context):
    user = update.effective_user
    if user.username != ADMIN_USERNAME:
        return

    await update.message.reply_text(
        "Админ панель:\n"
        "/create_game — создать коробку\n"
        "/list — список участников\n"
        "/export — экспорт в Excel\n"
        "/distribute — распределить\n"
        "/reset — удалить всех участников"
    )


async def create_game(update: Update, context):
    if update.effective_user.username != ADMIN_USERNAME:
        return
    await update.message.reply_text("Введите название новой коробки:")
    return WAITING_GAME_NAME


async def save_game(update: Update, context):
    name = update.message.text
    chat_id = update.message.chat_id

    db.add_game(chat_id, name)
    await update.message.reply_text(f"Коробка «{name}» создана!")
    return ConversationHandler.END


# ---------- USER JOIN ----------
async def join(update: Update, context):
    games = db.get_games()

    if len(games) == 0:
        await update.message.reply_text("Пока нет коробок. Ожидайте админа.")
        return ConversationHandler.END

    buttons = [[KeyboardButton(g[1])] for g in games]
    await update.message.reply_text(
        "Выберите коробку:",
        reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    )

    return WAITING_GAME_CHOICE


async def choose_game(update: Update, context):
    chosen = update.message.text
    games = {g[1]: g[0] for g in db.get_games()}

    if chosen not in games:
        await update.message.reply_text("Такой коробки нет.")
        return ConversationHandler.END

    context.user_data["game_id"] = games[chosen]

    await update.message.reply_text("Введите ваше ФИО:")
    return WAITING_FULLNAME


async def save_fullname(update: Update, context):
    context.user_data["fullname"] = update.message.text
    await update.message.reply_text("Введите ваши пожелания:")
    return WAITING_WISHES


async def save_wishes(update: Update, context):
    user = update.effective_user

    db.add_participant(
        user_id=user.id,
        username=user.username,
        full_name=context.user_data["fullname"],
        wishes=update.message.text,
        game_id=context.user_data["game_id"]
    )

    await update.message.reply_text("Вы успешно зарегистрированы!")
    return ConversationHandler.END


# ---------- EXPORT ----------
async def export(update, context):
    if update.effective_user.username != ADMIN_USERNAME:
        return

    games = db.get_games()
    if not games:
        await update.message.reply_text("Нет коробок.")
        return

    for gid, name in games:
        participants = db.get_participants(gid)
        filename = f"export_{name}.xlsx"
        utils.export_to_excel(participants, filename)
        await update.message.reply_document(open(filename, "rb"))


# ---------- DISTRIBUTION ----------
async def distribute(update, context):
    if update.effective_user.username != ADMIN_USERNAME:
        return

    games = db.get_games()

    for gid, name in games:
       participants = db.get_participants(gid)
        get_participants(gid)

        if len(participants) < 2:
            await update.message.reply_text(f"В коробке «{name}» недостаточно участников.")
            continue

        result = utils.do_distribution(participants)

        for p in participants:
            user_id = p[1]
            receiver_id = result[user_id]
            receiver = next(r for r in participants if r[1] == receiver_id)

            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"Ваш получатель: {receiver[3]}\nПожелания: {receiver[4]}"
                )
            except:
                pass

        await update.message.reply_text(f"Распределение в коробке «{name}» завершено!")


# ---------- RESET ----------
async def reset(update, context):
    if update.effective_user.username != ADMIN_USERNAME:
        return

    games = db.get_games()
    for gid, name in games:
        db.delete_participants(gid)

    await update.message.reply_text("Все участники удалены.")


# ---------- HANDLER ----------
def main():
    keep_alive()

    app = Application.builder().token(TOKEN).build()

    join_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Участвовать$"), join)],
        states={
            WAITING_GAME_CHOICE: [MessageHandler(filters.TEXT, choose_game)],
            WAITING_FULLNAME: [MessageHandler(filters.TEXT, save_fullname)],
            WAITING_WISHES: [MessageHandler(filters.TEXT, save_wishes)],
        },
        fallbacks=[]
    )

    create_conv = ConversationHandler(
        entry_points=[CommandHandler("create_game", create_game)],
        states={WAITING_GAME_NAME: [MessageHandler(filters.TEXT, save_game)]},
        fallbacks=[]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(join_conv)
    app.add_handler(create_conv)

    app.add_handler(CommandHandler("list", admin_panel))
    app.add_handler(CommandHandler("export", export))
    app.add_handler(CommandHandler("distribute", distribute))
    app.add_handler(CommandHandler("reset", reset))

    app.add_handler(MessageHandler(filters.Regex("^Админ-панель$"), admin_panel))

    app.run_polling()


if name == "__main__":
    main()
