import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os

BOT_TOKEN = os.environ['BOT_TOKEN']
SPREADSHEET_ID = os.environ['SPREADSHEET_ID']
CREDENTIALS_JSON = os.environ['GOOGLE_CREDS']

bot = telebot.TeleBot(BOT_TOKEN)

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds_dict = json.loads(CREDENTIALS_JSON)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

sheet = client.open_by_key(SPREADSHEET_ID).worksheet("Данные")

@bot.message_handler(commands=["start", "add"])
def handle_start(message):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("Общались", callback_data="talked"),
        InlineKeyboardButton("Не общались", callback_data="no_talk"),
        InlineKeyboardButton("$", callback_data="money")
    )
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    row = [call.from_user.first_name, call.data]
    sheet.append_row(row)
    bot.send_message(call.message.chat.id, f"Сохранено: {row}")

bot.infinity_polling()
