import os
import re
from telebot import TeleBot
from telebot.types import Message, User, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, Contact, CallbackQuery
from typing import Any, TypedDict, Callable
from dotenv import load_dotenv

from modules.SQLite3 import SQLite
from modules.SQL_Queries import SQL_Queries

load_dotenv(override = True)

bot = TeleBot(os.environ["BOT_TOKEN"])
print(f"Bot @{bot.get_me().username} started!")

sql_db: SQLite = SQLite({"database": "./data.db", "isolation_level": "IMMEDIATE", "autocommit": True}, True)
queries: SQL_Queries = SQL_Queries(sql_db)

class ServiceDict(TypedDict):
    id: int
    name: str
    img_src: str
    price: float
    currency: str
    duration_min: float
    description: str

test_price_list: list[ServiceDict] = [
    {
        "id": 1,
        "name": "Заміна моторної оливи",
        "price": 800,
        "currency": "UAH",
        "duration_min": 30,
        "description": "Заміна моторної оливи та масляного фільтра з перевіркою рівнів рідин.",
        "img_src": "https://di-uploads-pod36.dealerinspire.com/cutterbuickgmc/uploads/2023/03/AdobeStock_334203483.jpg"
    },
    {
        "id": 2,
        "name": "Комп’ютерна діагностика авто",
        "price": 600,
        "currency": "UAH",
        "duration_min": 40,
        "description": "Зчитування та аналіз помилок електронних систем автомобіля.",
        "img_src": "https://www.r2cthemes.com/eocte/i/bg/services-diagnostic-service.jpg"
    },
    {
        "id": 3,
        "name": "Заміна гальмівних колодок",
        "price": 1200,
        "currency": "UAH",
        "duration_min": 60,
        "description": "Демонтаж старих та встановлення нових гальмівних колодок.",
        "img_src": "https://st.depositphotos.com/1637787/2927/i/450/depositphotos_29272913-stock-photo-brake-repair.jpg"
    },
    {
        "id": 4,
        "name": "Розвал-сходження",
        "price": 1500,
        "currency": "UAH",
        "duration_min": 50,
        "description": "Налаштування кутів коліс для стабільної та безпечної їзди.",
        "img_src": "https://www.r2cthemes.com/eocte/i/pages/services/service-cardiagnostic.webp"
    },
    {
        "id": 5,
        "name": "Діагностика акумулятора",
        "price": 400,
        "currency": "UAH",
        "duration_min": 20,
        "description": "Перевірка стану акумулятора, напруги та пускового струму.",
        "img_src": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQO5kCepNdhZvDKJtmPAIWnloSdTal7N1CQaA&s"
    },
    {
        "id": 6,
        "name": "Комплексна мийка автомобіля",
        "price": 700,
        "currency": "UAH",
        "duration_min": 45,
        "description": "Зовнішня мийка, чистка салону та килимків.",
        "img_src": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQO5kCepNdhZvDKJtmPAIWnloSdTal7N1CQaA&s"
    }
]


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
    # для регистрации нужны: номер телефона, айди (тг), имя
    assert isinstance(message.from_user, User)
    if not queries.is_registered_user(message.from_user.id):
        register_user(message, start_msg)
        return

    # проверять на None и если пользователя нет - регать заново
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
                # сделать запись пользователя на выбраный сервис
                ...
        case _:
            bot.answer_callback_query(call.id, "Віддано на обробку! ✅")

def display_price_list(user_id: int) -> None:
    markup = InlineKeyboardMarkup(row_width=1)
    for service in test_price_list:
        markup.add(InlineKeyboardButton(f"{service['name']}: {service['price']}{service['currency']}", callback_data=f"price_list display_service {service['id']}"))

    bot.send_message(user_id, f"Оберіть потрібну послугу з меню нижче 👇", reply_markup=markup)
    return


def display_service(user_id: int, service_id: int) -> None:
    # заглушка, пока нет DB
    service: ServiceDict = test_price_list[service_id - 1]
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Записатись на послугу 📅", callback_data=f"service make_an_appointment {service_id}"))
    bot.send_photo(user_id, service["img_src"], (
        f"🛠️ {service['name']}\n"
        f"💰 Ціна: {service['price']} {service['currency']}\n"
        f"⏱️ Тривалість: {service['duration_min']} хв\n"
        f"📝 Опис: {service['description']}"
        ), reply_markup=markup
    )


def display_schedule(user_id: int) -> None:
    # заглушка, пока не файла JSON
    schedule: str = ("🕒 Графік роботи СТО 🚗\n\n"
                    "Понеділок – П’ятниця\n"
                    "⏰ 09:00 – 18:00\n"
                    "🥪 Перерва: 13:00 – 14:00\n\n"
                    "Субота\n"
                    "⏰ 10:00 – 16:00\n"
                    "🥪 Перерва: 12:30 – 13:00\n\n"
                    "Неділя\n"
                    "❌ Вихідний\n"
                    "⚠️ Тільки запис на майбутні дні\n"
    )
    bot.send_message(user_id, schedule)


def display_address(user_id: int) -> None:
    # заглушка, пока не файла JSON
    schedule: str = ("Контакти та адреса\n\n"
                     "📍Адреса: м. Харків, вул. Технічна, 12\n"
                     "📞Телефон для довідок: +380 88 005 55 3535\n"
                     "📧Електронна пошта: info@sto.kh.ua"
    )
    bot.send_message(user_id, schedule)

bot.infinity_polling()