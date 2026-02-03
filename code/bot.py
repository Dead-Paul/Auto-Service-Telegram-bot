import os
import re
from datetime import datetime, time
from typing import Any, TypedDict, Callable


from telebot import TeleBot
from telebot.types import Message, User, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, Contact, CallbackQuery
from dotenv import load_dotenv

from modules.Utils import SQLite, JSON
from modules.SQL_Queries import SQL_Queries

load_dotenv(override = True)

bot = TeleBot(os.environ["BOT_TOKEN"])
print(f"Bot @{bot.get_me().username} started!")

os.chdir("./data")
data_db: SQLite = SQLite({"database": "data.db", "isolation_level": "IMMEDIATE", "autocommit": True}, True)
data_json = JSON("data.json")
queries: SQL_Queries = SQL_Queries(data_db)


def register_user(message, callback_function: Callable[[Message], Any]):
    def handle_user_full_name(message: Message, phone_number: str) -> None:
        assert isinstance(message.from_user, User)
        if message.text is not None:
            if bool(re.compile(r"^[А-ЯІЇЄҐ][а-яіїєґʼ']+(?:-[А-ЯІЇЄҐ][а-яіїєґʼ']+)?(?:\s[А-ЯІЇЄҐ][а-яіїєґʼ']+(?:-[А-ЯІЇЄҐ][а-яіїєґʼ']+)?)+$").fullmatch(message.text)):
                if queries.register_new_user(message.from_user.id, phone_number, message.text):
                    bot.reply_to(message, "Реєстрація завершена! ✅")
                    callback_function(message)
                else: 
                    bot.reply_to(message, "Виникла помилка, спробуйте ще раз! ❌")
                return
            else:
                error_text: str = "Надіслане повідомлення не має тексту! 📝 Будь ласка надішліть ваше ПІБ:"
        else:
            error_text: str = "Надіслане повідомлення не має тексту! 📝 Будь ласка надішліть ваше ПІБ:"
        bot.register_next_step_handler(
            bot.send_message(message.chat.id, error_text),
            handle_user_full_name, phone_number
        )

    def handle_contact(message: Message) -> None:
        if message.content_type == "contact":
            assert isinstance(message.contact, Contact)
            bot.send_message(message.chat.id, f"Отриман номер телефону: 📞 {message.contact.phone_number}!", reply_markup=ReplyKeyboardRemove())
            bot.register_next_step_handler(
                bot.send_message(message.chat.id, f"Для завершення реєстрації напишіть ваше ПІБ 📝:"),
                handle_user_full_name, message.contact.phone_number
            )
        else:
            bot.send_message(message.chat.id, f"Це не номер телефону! ❌\nБудь ласка надішліть дійсний контакт (натисніть на кнопку)")
            register_user(message, callback_function)

    markup = ReplyKeyboardMarkup()
    markup.add(KeyboardButton("Поділитися номером телефону 📲", request_contact=True))
    bot.register_next_step_handler(
        bot.send_message(message.chat.id, "Поділитися вашим номером телефону, для початку реєстрації 📲", reply_markup=markup),
        handle_contact
    )


@bot.message_handler(commands=["start"])
def start_msg(message: Message):
    assert isinstance(message.from_user, User)
    if not queries.is_registered_user(message.from_user.id):
        register_user(message, start_msg)
        return

    if isinstance(user := queries.get_user(message.from_user.id), dict):
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            *[
                InlineKeyboardButton("🛠️ Прайс-лист", callback_data=f"bot_services display_price_list None"),
                InlineKeyboardButton("📅 Мої записи", callback_data=f"bot_services display_future_appointments None"),
                InlineKeyboardButton("🕒 Графік роботи", callback_data=f"bot_services display_schedule None"),
                InlineKeyboardButton("📍 Контакти та адреса", callback_data=f"bot_services display_address None"),
                InlineKeyboardButton("📜 Історія записів", callback_data=f"bot_services display_past_appointments None"),
            ]
        )
        bot.send_message(message.chat.id, f"👋 Вітаємо, {user['fullname']} у чат-боті станції технічного обслуговування 🚗\nОберіть потрібну дію з меню нижче 👇",
                        reply_markup=markup)
        return
    register_user(message, start_msg)


def is_within_working_hours(date_time: datetime, working_hours: list) -> bool:
    day_config = working_hours[date_time.weekday()]
    if day_config is None:
        return False

    def parse(time_to_parse: str) -> time:
        hour, minute = map(int, time_to_parse.split(":"))
        return time(hour, minute)

    start = parse(day_config["start"])
    end = parse(day_config["end"])
    if not (start <= date_time.time() < end):
        return False
    if "break" in day_config and day_config["break"]:
        break_start = parse(day_config["break"][0])
        break_end = parse(day_config["break"][1])
        if break_start <= date_time.time() < break_end:
            return False
    return True




def handle_appointment_datetime(message: Message, service_id: int) -> None:
    assert isinstance(message.from_user, User)

    if not message.text:
        bot.reply_to(message, "❌ Невірний формат. Спробуйте ще раз.")
        return

    try:
        appointment_datetime = datetime.strptime(message.text, "%Y-%m-%d %H:%M")
    except ValueError:
        bot.reply_to(message,"❌ Формат неправильний.\nВикористовуйте: YYYY-MM-DD HH:MM")
        return

    working_hours = data_json.read()["working_hours"]
    if not is_within_working_hours(appointment_datetime, working_hours):
        bot.reply_to(message, "⛔ Обраний час поза робочим графіком або під час перерви. Оберіть інший.")
        bot.register_next_step_handler(message, handle_appointment_datetime, service_id)
        return

    appointment_timestamp = appointment_datetime.strftime("%Y-%m-%d %H:%M")

    if queries.is_timeslot_taken(appointment_timestamp):
        bot.reply_to(message, "⛔ Цей час вже зайнятий. Оберіть інший.")
        bot.register_next_step_handler(message, handle_appointment_datetime, service_id)
        return

    if queries.create_appointment(user_id=message.from_user.id, service_id=service_id, appointment_ts=appointment_timestamp):
        bot.reply_to(message, f"✅ Запис успішно створено!\n🛠 Послуга ID: {service_id}\n🕒 Час: {appointment_timestamp}")
    else:
        bot.reply_to(message, "❌ Помилка створення запису.")

def make_an_appointment(user_id: int, service_id: int) -> None:
    bot.send_message(user_id, "📅 Введіть дату та час запису у форматі:\nYYYY-MM-DD HH:MM\n\nНаприклад: 2026-02-10 14:30")
    bot.register_next_step_handler_by_chat_id(user_id, handle_appointment_datetime, service_id)



@bot.callback_query_handler(lambda _: True)
def callback_query_handler(call: CallbackQuery):
    if call.data is None:
        bot.answer_callback_query(call.id, "Недійсна кнопка! Помилка ❌")
        return
    assert isinstance(call.data, str)
    bot.answer_callback_query(call.id, "Віддано на обробку! ✅")
    call_from, call_to, call_params = call.data.split(' ', 2)
    match call_from:
        case "bot_services":
            match call_to:
                case "display_price_list":
                    display_price_list(call.from_user.id)
                case "display_schedule":
                    display_schedule(call.from_user.id)
                case "display_address":
                    display_address(call.from_user.id)
        case "price_list":
            if "display_service":
                display_service(call.from_user.id, int(call_params))
        case "service":
            if "make_an_appointment":
                make_an_appointment(call.from_user.id, int(call_params))
        case _:
            bot.answer_callback_query(call.id, "Віддано на обробку! ✅")

def display_price_list(user_id: int) -> None:
    services = queries.get_all_services()
    if not services:
        bot.send_message(user_id, "❌ Список послуг порожній.")
        return
    markup = InlineKeyboardMarkup(row_width=1)
    for service in services:
        markup.add(InlineKeyboardButton(f"{service['name']}: {service['price']}{service['currency']}", callback_data=f"price_list display_service {service['id']}"))
    bot.send_message(user_id, "Оберіть потрібну послугу з меню нижче 👇", reply_markup=markup)


def display_service(user_id: int, service_id: int) -> None:
    service = queries.get_service(service_id)
    if not service:
        bot.send_message(user_id, "❌ Послуга не знайдена.")
        return
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Записатись на послугу 📅", callback_data=f"service make_an_appointment {service_id}"))
    bot.send_photo(user_id, service["img_src"],
        (
            f"🛠️ {service['name']}\n"
            f"💰 Ціна: {service['price']} {service['currency']}\n"
            f"⏱️ Тривалість: {service['duration_min']} хв\n"
            f"📝 Опис: {service['description']}"
        ),
        reply_markup=markup
    )

def display_schedule(user_id: int) -> None:
    config = JSON("data.json")
    working_hours: list = config.read()["working_hours"]
    day_names = ["Понеділок", "Вівторок", "Середа", "Четвер", "П’ятниця", "Субота", "Неділя"]
    text = "🕒 Графік роботи СТО 🚗\n\n"

    for i, day_info in enumerate(working_hours):
        text += f"{day_names[i]}\n"
        if day_info is None:
            text += "❌ Вихідний\n\n"
            continue
        text += f"⏰ {day_info['start']} – {day_info['end']}\n"
        if "break" in day_info and day_info["break"]:
            text += f"🥪 Перерва: {day_info['break'][0]} – {day_info['break'][1]}\n"
        text += "\n"

    bot.send_message(user_id, text)


def display_address(user_id: int) -> None:
    # заглушка, пока не файла JSON
    schedule: str = ("Контакти та адреса\n\n"
                     "📍Адреса: м. Харків, вул. Технічна, 12\n"
                     "📞Телефон для довідок: +380 88 005 55 3535\n"
                     "📧Електронна пошта: info@sto.kh.ua"
    )
    bot.send_message(user_id, schedule)

bot.infinity_polling()