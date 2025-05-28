import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials

# Получение токена и данных из переменных окружения
BOT_TOKEN = os.environ['BOT_TOKEN']
SPREADSHEET_ID = os.environ['SPREADSHEET_ID']
CREDS_JSON = json.loads(os.environ['GOOGLE_CREDS'])

# Авторизация Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(CREDS_JSON, scope)
client = gspread.authorize(credentials)
sheet = client.open_by_key(SPREADSHEET_ID).sheet1

bot = telebot.TeleBot(BOT_TOKEN)
user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    user_data[message.chat.id] = {}
    markup = InlineKeyboardMarkup()
    for day in range(1, 32):
        markup.add(InlineKeyboardButton(str(day), callback_data=f"day_{day}"))
    bot.send_message(message.chat.id, "Выбери день месяца:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("day_"))
def handle_day(call):
    day = call.data.split("_")[1]
    user_data[call.message.chat.id]['day'] = day
    msg = bot.send_message(call.message.chat.id, "Введи имя лида (или выбери существующее):")
    bot.register_next_step_handler(msg, ask_lead_name)

def ask_lead_name(message):
    user_data[message.chat.id]['lead'] = message.text.strip()
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("Общались", callback_data="action_talked"),
        InlineKeyboardButton("Не общались", callback_data="action_not_talked"),
        InlineKeyboardButton("$", callback_data="action_money")
    )
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("action_"))
def handle_action(call):
    action = call.data.split("_")[1]
    if action == "money":
        msg = bot.send_message(call.message.chat.id, "Введи сумму от 0 до 100000:")
        bot.register_next_step_handler(msg, save_money)
    else:
        save_to_sheet(call.message.chat.id, action)
        bot.send_message(call.message.chat.id, f"Сохранено: {action}")

def save_money(message):
    try:
        amount = int(message.text)
        if 0 <= amount <= 100000:
            save_to_sheet(message.chat.id, str(amount))
            bot.send_message(message.chat.id, f"Сохранено: ${amount}")
        else:
            bot.send_message(message.chat.id, "Число вне допустимого диапазона. Попробуй снова.")
    except ValueError:
        bot.send_message(message.chat.id, "Ошибка: введи число.")

def save_to_sheet(chat_id, value):
    day = user_data[chat_id].get('day')
    lead = user_data[chat_id].get('lead')
    sheet.append_row([str(day), lead, value])

bot.infinity_polling()
