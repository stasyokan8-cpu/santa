import json
import random
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = "1667037381:AAFdA7l6LcMidWsgrerdOkpBXfNF2gbNsvo"

# --- Хранилище данных ---
participants = {}   # user_id -> {"name": str, "wish": str}
ADMIN_USERNAME = "BeellyKid"  # только этот пользователь может видеть базу и запускать Санту
DB_FILE = "participants.json"

# --- Работа с файлом ---
def load_participants():
    global participants
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            participants = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        participants = {}

def save_participants():
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(participants, f, ensure_ascii=False, indent=2)

# --- Команды ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"🎄 Привет, {user.first_name}! Добро пожаловать на вечеринку Тайного Санты! 🎁\n"
        "Нажми /menu, чтобы открыть праздничное меню ✨"
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("🎁 Присоединиться к веселью", callback_data="join")],
        [InlineKeyboardButton("🚪 Уйти с вечеринки", callback_data="leave")],
        [InlineKeyboardButton("✨ Моё желание", callback_data="wish")],
    ]
    # список участников и запуск Санты доступны только админу
    if user.username == ADMIN_USERNAME:
        keyboard.append([InlineKeyboardButton("📋 Список участников", callback_data="list")])
        keyboard.append([InlineKeyboardButton("🎅 Запустить Санту!", callback_data="start_santa")])

    menu_text = "🎄 *Новогоднее меню Тайного Санты* 🎄\nВыбирай, что хочешь сделать:"
    await update.message.reply_text(menu_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# --- Обработчик кнопок ---

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    user_id = str(user.id)
    username = user.username
    name = user.first_name
    data = query.data

    if data == "join":
        if user_id in participants:
            await query.message.reply_text(f"🎅 {name}, ты уже участвуешь!")
        else:
            participants[user_id] = {"name": name, "wish": ""}
            save_participants()
            await query.message.reply_text(f"🎉 {name} присоединился к веселью!")

    elif data == "leave":
        if user_id in participants:
            del participants[user_id]
            save_participants()
            await query.message.reply_text(f"❄️ {name} покинул игру...")
        else:
            await query.message.reply_text("Ты ещё не в игре!")

    elif data == "wish":
        if user_id not in participants:
            await query.message.reply_text("🎁 Сначала присоединись к игре!")
            return
        current_wish = participants[user_id]["wish"]
        if current_wish:
            await query.message.reply_text(f"✨ Твоё текущее желание: {current_wish}")
        else:
            await query.message.reply_text("У тебя пока нет желания 🎄✨")
        await query.message.reply_text("Напиши своё желание одним сообщением 🎄✨")
        context.user_data["awaiting_wish"] = True

    elif data == "list":
        if username != ADMIN_USERNAME:
            await query.message.reply_text("❌ Только @BeellyKid может видеть список участников 🎄")
            return
        if participants:
            text = "📋 Участники новогоднего розыгрыша:\n"
            for p in participants.values():
                text += f"- {p['name']} (желание: {p['wish'] or '—'})\n"
        else:
            text = "Пока никто не присоединился... ⛄"
        await query.message.reply_text(text)

    elif data == "start_santa":
        if username != ADMIN_USERNAME:
            await query.message.reply_text("❌ Только @BeellyKid может запустить Санту! 🎅")
            return
        if len(participants) < 2:
            await query.message.reply_text("❌ Нужно хотя бы 2 участника!")
            return

        await query.message.reply_text("✨🎄 Санта готовит подарки... 🎅✨")
        await start_santa(context)

# --- Функция запуска Санты ---

async def start_santa(context: ContextTypes.DEFAULT_TYPE):
    ids = list(participants.keys())
    random.shuffle(ids)
    pairs = {ids[i]: ids[(i + 1) % len(ids)] for i in range(len(ids))}

    for giver, receiver in pairs.items():
        wish = participants[receiver]["wish"] or "🎁 Пока без пожеланий"
        await context.bot.send_message(
            chat_id=giver,
            text=(
                f"🎅 Привет, {participants[giver]['name']}!\n"
                f"Ты даришь подарок 🎁 для {participants[receiver]['name']}!\n"
                f"Его/Её желание: {wish}\n"
                "Пусть твой подарок будет волшебным ✨❄️"
            )
        )
    print("🎄 Санта запущен! Все участники получили свои пары 🎉")

# --- Обработка сообщений для желаний ---

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if context.user_data.get("awaiting_wish"):
        if user_id in participants:
            participants[user_id]["wish"] = update.message.text
            save_participants()
            await update.message.reply_text(
                f"✨ Желание записано!\nТвоё желание: {participants[user_id]['wish']} 🎁"
            )
        else:
            await update.message.reply_text("🎄 Ты не участвуешь в игре!")
        context.user_data["awaiting_wish"] = False

# --- Дополнительная команда для удобства ---

async def mywish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id in participants:
        wish = participants[user_id]["wish"]
        if wish:
            await update.message.reply_text(f"✨ Твоё желание: {wish}")
        else:
            await update.message.reply_text("🎄 У тебя пока нет желания!")
    else:
        await update.message.reply_text("❄️ Ты не участвуешь в игре!")

# --- Основная функция запуска бота ---

def main():
    load_participants()
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("mywish", mywish))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🎄 Бот Тайный Санта запущен! 🎅")
    app.run_polling()

if __name__ == "__main__":
    main()
