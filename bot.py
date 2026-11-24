import json
import logging
import telebot
from telebot import apihelper, types

BOT_TOKEN = "1780243761:LKUmLwwjHjHTGmzBiXqK61rfD6zQD4uLXgV"
CUSTOM_API_URL = "https://api.wiftgram.ru"
ADMIN_ID = 123456789
WEBAPP_URL = "git clone https://github.com/artemfilippov36kv"

MIN_DEPOSIT = 500
MIN_WITHDRAW = 1100

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")

apihelper.API_URL = f"{CUSTOM_API_URL}/bot{{0}}/{{1}}"
apihelper.FILE_URL = f"{CUSTOM_API_URL}/file/bot{{0}}/{{1}}"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")


def main_reply_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton(text="🎮 Играть", web_app=types.WebAppInfo(url=WEBAPP_URL)))
    kb.row(
        types.KeyboardButton(text=f"⭐ Пополнить (от {MIN_DEPOSIT} ⭐)"),
        types.KeyboardButton(text=f"🎁 Вывод (от {MIN_WITHDRAW} ⭐)"),
    )
    return kb


def main_inline_kb():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="🎮 Открыть игру", web_app=types.WebAppInfo(url=WEBAPP_URL)))
    kb.add(types.InlineKeyboardButton(text=f"⭐ Пополнить от {MIN_DEPOSIT} ⭐", callback_data="dep_start"))
    return kb


def quick_deposit_kb():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("500 ⭐", callback_data="dep_500"),
        types.InlineKeyboardButton("1000 ⭐", callback_data="dep_1000"),
        types.InlineKeyboardButton("1500 ⭐", callback_data="dep_1500"),
        types.InlineKeyboardButton("2500 ⭐", callback_data="dep_2500"),
    )
    kb.add(types.InlineKeyboardButton("❌ Отмена", callback_data="dep_cancel"))
    return kb


@bot.message_handler(commands=["start"])
def cmd_start(message):
    user = message.from_user
    logging.info(f">>> КОМАНДА /start ОТ: {user.first_name} | ID: {user.id} <<<")

    text = (
        f"👋 <b>Добро пожаловать в Nebula!</b>\n\n"
        f"🆔 Твой ID: <code>{user.id}</code>\n\n"
        f"🎮 Нажми <b>«Открыть игру»</b>, чтобы запустить Мины, Лесенку, Апгрейд и NFT-подарки.\n"
        f"⭐ Пополнение баланса — от <b>{MIN_DEPOSIT} ⭐</b>\n"
        f"🎁 Вывод звёзд и подарков — от <b>{MIN_WITHDRAW} ⭐</b>"
    )
    bot.send_message(message.chat.id, text, reply_markup=main_reply_kb())
    bot.send_message(message.chat.id, "Быстрый запуск:", reply_markup=main_inline_kb())


@bot.callback_query_handler(func=lambda call: call.data == "dep_start")
def cb_dep_start(call):
    bot.answer_callback_query(call.id)
    ask_deposit(call.message)


@bot.message_handler(func=lambda m: m.text and "Пополнить" in m.text)
def msg_dep_start(message):
    ask_deposit(message)


def ask_deposit(message):
    msg = bot.send_message(
        message.chat.id,
        f"⭐ <b>Пополнение баланса</b>\n\n"
        f"Введите сумму в звёздах (минимум <b>{MIN_DEPOSIT} ⭐</b>) или выберите кнопку ниже:",
        reply_markup=quick_deposit_kb(),
    )
    bot.register_next_step_handler(msg, process_text_deposit)


@bot.callback_query_handler(func=lambda call: call.data == "dep_cancel")
def cb_dep_cancel(call):
    bot.answer_callback_query(call.id, "Отменено")
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    try:
        bot.edit_message_text("❌ Пополнение отменено.", call.message.chat.id, call.message.message_id)
    except Exception:
        pass


@bot.callback_query_handler(func=lambda call: call.data.startswith("dep_"))
def cb_dep_quick(call):
    parts = call.data.split("_")
    if len(parts) < 2 or not parts[1].isdigit():
        return
    amount = int(parts[1])
    bot.answer_callback_query(call.id)
    bot.clear_step_handler_by_chat_id(call.message.chat.id)
    create_deposit_request(call.from_user, call.message.chat.id, amount)


def process_text_deposit(message):
    if not message.text:
        return
    digits = "".join(ch for ch in message.text if ch.isdigit())
    amount = int(digits) if digits else 0

    if amount < MIN_DEPOSIT:
        msg = bot.send_message(
            message.chat.id,
            f"❌ Минимальная сумма пополнения — <b>{MIN_DEPOSIT} ⭐</b>.\nВведите корректное число:",
            reply_markup=quick_deposit_kb(),
        )
        bot.register_next_step_handler(msg, process_text_deposit)
        return

    create_deposit_request(message.from_user, message.chat.id, amount)


def create_deposit_request(user, chat_id, amount):
    username = f"@{user.username}" if user.username else f"ID {user.id}"
    bot.send_message(
        chat_id,
        f"✅ <b>Заявка на пополнение {amount} ⭐ создана!</b>\n\n"
        f"Администратор получил уведомление. Переведите <b>{amount} ⭐</b> (подарками или звёздами) "
        f"администратору в ЛС, и он сразу выдаст вам одноразовый код активации для игры!",
    )

    if ADMIN_ID and ADMIN_ID != 123456789:
        try:
            bot.send_message(
                ADMIN_ID,
                f"💰 <b>Заявка на пополнение!</b>\n\n"
                f"👤 Игрок: {user.first_name} ({username})\n"
                f"🆔 ID: <code>{user.id}</code>\n"
                f"⭐ Сумма: <b>{amount} ⭐</b>\n\n"
                f"<i>Сгенерируй для него код на {amount} ⭐ в калькуляторе админа.</i>",
            )
        except Exception as e:
            logging.error(f"Ошибка отправки админу: {e}")


@bot.message_handler(func=lambda m: m.text and "Вывод" in m.text)
def msg_withdraw_info(message):
    bot.send_message(
        message.chat.id,
        f"🎁 <b>Вывод звёзд и подарков (от {MIN_WITHDRAW} ⭐)</b>\n\n"
        f"1. Откройте игру и нажмите <b>«− Вывести»</b> в шапке (или в Инвентаре на подарке от {MIN_WITHDRAW} ⭐).\n"
        f"2. Скопируйте сформированный <b>Чек на вывод</b>.\n"
        f"3. Просто отправьте этот текст чека сюда в чат боту — я мгновенно передам его администратору!",
    )


@bot.message_handler(content_types=["web_app_data"])
def handle_webapp_data(message):
    raw = message.web_app_data.data
    user = message.from_user
    username = f"@{user.username}" if user.username else f"ID {user.id}"

    try:
        data = json.loads(raw)
        gift_name = data.get("gift", "Подарок")
        price = int(data.get("price", 0))
    except Exception:
        gift_name = raw
        price = MIN_WITHDRAW

    if price < MIN_WITHDRAW:
        bot.send_message(message.chat.id, f"❌ Минимальный вывод — {MIN_WITHDRAW} ⭐.")
        return

    bot.send_message(message.chat.id, "✅ <b>Заявка на вывод из игры принята и отправлена администратору!</b>")
    if ADMIN_ID and ADMIN_ID != 123456789:
        bot.send_message(
            ADMIN_ID,
            f"🎁 <b>Вывод из Mini App!</b>\n\n"
            f"👤 Игрок: {user.first_name} ({username})\n"
            f"🆔 ID: <code>{user.id}</code>\n"
            f"🎀 Приз: <b>{gift_name}</b> ({price} ⭐)",
        )


@bot.message_handler(func=lambda m: m.text and "Чек на вывод" in m.text)
def handle_text_check(message):
    user = message.from_user
    username = f"@{user.username}" if user.username else f"ID {user.id}"

    bot.send_message(
        message.chat.id,
        "✅ <b>Чек получен и передан администратору на проверку!</b>\nОжидайте выдачи в ЛС.",
    )
    if ADMIN_ID and ADMIN_ID != 123456789:
        try:
            bot.send_message(
                ADMIN_ID,
                f"🧾 <b>Пришел чек на вывод!</b>\n\n"
                f"👤 От: {user.first_name} ({username})\n"
                f"🆔 ID: <code>{user.id}</code>\n\n"
                f"<code>{message.text}</code>\n\n"
                f"<i>Проверь подпись этого чека в админке!</i>",
            )
        except Exception as e:
            logging.error(f"Ошибка пересылки чека: {e}")


@bot.message_handler(func=lambda m: True)
def fallback(message):
    bot.send_message(message.chat.id, "👇 Используй кнопки меню ниже или нажми /start:", reply_markup=main_reply_kb())


if __name__ == "__main__":
    logging.info("Бот запущен на сервере Wiftgram!")
    try:
        bot.set_chat_menu_button(
            menu_button=types.MenuButtonWebApp(text="🎮 Играть", web_app=types.WebAppInfo(url=WEBAPP_URL))
        )
    except Exception as e:
        logging.warning(f"Menu button: {e}")

    bot.infinity_polling(skip_pending=True)
