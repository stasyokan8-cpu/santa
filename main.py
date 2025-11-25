from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import random

TOKEN = "1667037381:AAFdA7l6LcMidWsgrerdOkpBXfNF2gbNsvo"

# --- Хранилища данных ---
participants = {}   # user_id -> {"name": str, "wish": str}
ADMIN_USERNAME = "BeellyKid"  # только этот пользователь может запускать Санту

# --- Команды ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"🎄 Привет, {user.first_name}! Добро пожаловать на волшебную новогоднюю вечеринку Тайного Санты! 🎁\n"
        "Нажми /menu, чтобы открыть праздничное меню ✨"
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    # Ёлка в меню через эмодзи 🎄
    keyboard = [
        [InlineKeyboardButton("🎁 Присоединиться к веселью", callback_data="join")],
        [InlineKeyboardButton("🚪 Уйти с вечеринки", callback_data="leave")],
        [InlineKeyboardButton("📋 Кто уже в игре?", callback_data="list")],
        [InlineKeyboardButton("✨ Моё желание", callback_data="wish")],
    ]
    if user.username == ADMIN_USERNAME:
        keyboard.append([InlineKeyboardButton("🎅 Запустить Санту!", callback_data="start_santa")])

    menu_text = "🎄 *Новогоднее меню Тайного Санты* 🎄\nВыбирай, что хочешь сделать:"
    await update.message.reply_text(menu_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# --- Обработчик кнопок ---

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    user_id = user.id
    username = user.username
    name = user.first_name
    data = query.data

    if data == "join":
        if user_id in participants:
            await query.message.reply_text(f"🎅 {name}, ты уже на новогодней тусовке! Санта тебя заметил 😎")
        else:
            participants[user_id] = {"name": name, "wish": ""}
            await query.message.reply_text(f"🎉 {name} присоединился к веселью! Пусть падают снежинки ❄️☃️")

    elif data == "leave":
        if user_id in participants:
            del participants[user_id]
            await query.message.reply_text(f"❄️ {name} покинул хоровод... Надеемся, вернёшься! 🎄")
        else:
            await query.message.reply_text("Ты ещё не в игре! 🎁")

    elif data == "list":
        if participants:
            text = "📋 Участники новогоднего розыгрыша:\n" + "\n".join([p["name"] for p in participants.values()])
        else:
            text = "Пока никто не присоединился... Снеговик грустит ⛄"
        await query.message.reply_text(text)

    elif data == "wish":
        if user_id not in participants:
            await query.message.reply_text("🎁 Сначала присоединись к игре, иначе Санта тебя не увидит!")
            return
        await query.message.reply_text("Напиши своё желание одним сообщением 🎄✨")
        context.user_data["awaiting_wish"] = True

    elif data == "start_santa":
        if username != ADMIN_USERNAME:
            await query.message.reply_text("❌ Только волшебник @BeellyKid может запустить Санту! 🎅")
            return
        if len(participants) < 2:
            await query.message.reply_text("❌ Нужно хотя бы 2 участника, чтобы праздник состоялся! 🎄")
            return

        # Праздничная анимация
        await query.message.reply_text("✨🎄 Разворачиваем подарки и шепчем Санте... 🎅✨")
        await start_santa(context)

# --- Функция запуска Санты ---

async def start_santa(context: ContextTypes.DEFAULT_TYPE):
    ids = list(participants.keys())
    random.shuffle(ids)
    pairs = {ids[i]: ids[(i + 1) % len(ids)] for i in range(len(ids))}

    for giver, receiver in pairs.items():
        wish = participants[receiver]["wish"] or "🎁 Пока без пожеланий, но с любовью ❤️"
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
    user_id = update.effective_user.id
    if context.user_data.get("awaiting_wish"):
        if user_id in participants:
            participants[user_id]["wish"] = update.message.text
            await update.message.reply_text("✨ Желание записано! Санта учтёт твою мечту 🎁")
        else:
            await update.message.reply_text("🎄 Ты не участвуешь в игре! Сначала присоединяйся.")
        context.user_data["awaiting_wish"] = False

# --- Основная функция запуска бота ---

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🎄 Бот Тайный Санта запущен! 🎅")
    app.run_polling()

if __name__ == "__main__":
    main()
