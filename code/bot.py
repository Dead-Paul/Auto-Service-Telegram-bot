import os
from telebot import TeleBot
from telebot.types import Message, User, InlineKeyboardMarkup, InlineKeyboardButton
from typing import TypedDict
from dotenv import load_dotenv

load_dotenv(override = True)

bot = TeleBot(os.environ["BOT_TOKEN"])
print(f"Bot @{bot.get_me().username} started!")

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


@bot.message_handler(commands=["start"])
def start_msg(message: Message):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        *[
            InlineKeyboardButton("🛠️ Послуги / Прайс-лист", callback_data="none"),
            InlineKeyboardButton("📅 Онлайн-запис", callback_data="none"),
            InlineKeyboardButton("🕒 Графік роботи", callback_data="none"),
            InlineKeyboardButton("📍 Контакти та адреса", callback_data="none"),
            InlineKeyboardButton("📜 Історія записів", callback_data="none"),
        ]
    )

    assert isinstance(message.from_user, User)
    bot.send_message(message.chat.id, f"👋 Вітаємо, {message.from_user.first_name}!\nВи у чат-боті станції технічного обслуговування 🚗\nОберіть потрібну дію з меню нижче 👇",
                    reply_markup=markup)
    return

@bot.message_handler(commands=["price_list"])
def price_list_msg(message: Message):
    markup = InlineKeyboardMarkup(row_width=1)
    for service in test_price_list:
        markup.add(InlineKeyboardButton(f"{service['name']}: {service['price']}{service['currency']}", callback_data="none"))

    bot.send_message(message.chat.id, f"Оберіть потрібну послугу з меню нижче 👇", reply_markup=markup)
    return


@bot.message_handler(commands=["get_service"])
def get_service_msg(message: Message):
    service_index: int = int(str(message.text).split(' ', 1)[1])
    service: ServiceDict = test_price_list[service_index]
    bot.send_photo(message.chat.id, service["img_src"], (
        f"🛠️ {service['name']}\n"
        f"💰 Ціна: {service['price']} {service['currency']}\n"
        f"⏱️ Тривалість: {service['duration_min']} хв\n"
        f"📝 Опис: {service['description']}"
        )
    )

bot.infinity_polling()