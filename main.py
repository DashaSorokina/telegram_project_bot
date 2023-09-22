import json
import os
from dotenv import load_dotenv
import telebot
import sqlite3
import webbrowser
from telebot import types
import requests
from currency_converter import CurrencyConverter

load_dotenv()

bot = telebot.TeleBot(os.getenv("BOT_KEY"))
API = os.getenv("API_KEY")

name = None
currency = CurrencyConverter()  #object created on class
amount = 0

@bot.message_handler(commands=['start', 'help'])
#parametr will store information about user and chat
def start(message):
    # from parametr message we can get id of my chat
    markup = types.ReplyKeyboardMarkup()
    btn1 = types.KeyboardButton('Add user to db')
    markup.row(btn1)
    btn2 = types.InlineKeyboardButton('Find weather')
    btn3 = types.InlineKeyboardButton('Convert Currency')  # now buttons just send text in chat
    markup.row(btn2, btn3)

    bot.send_message(message.chat.id, f'Hi,  {message.from_user.first_name} {message.from_user.last_name}!\n This bot is a studing project based on youtube video lesson, also add some functionality by myself. '
                                      f'Here you can see button of what bot can do:', reply_markup=markup)
    #if we want to do something with this text
    bot.register_next_step_handler(message, on_click)

def on_click(message):
    if message.text == 'Find weather':
         weather(message)
    elif message.text == 'Convert Currency':
         convert(message)
    elif message.text == 'Add user to db':
         registr(message)



@bot.message_handler(commands=['converter'])
def convert(message):
    bot.send_message(message.chat.id, 'Hello, write amoun:')
    bot.register_next_step_handler(message, summa)

def summa(message):
    global amount
    try:
        amount = int(message.text.strip())
    except ValueError:
        bot.send_message(message.chat.id, 'Wrong data format. Write amount')
        bot.register_next_step_handler(message, summa)
        return
    if amount > 0:
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton('USD/EUR', callback_data='usd/eur')
        btn2 = types.InlineKeyboardButton('EUR/USD', callback_data='eur/usd')
        btn3 = types.InlineKeyboardButton('USD/RUB', callback_data='usd/RUB')
        btn4 = types.InlineKeyboardButton('Another value', callback_data='else')
        markup.add(btn1, btn2, btn3, btn4)
        bot.send_message(message.chat.id, 'Get currency', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, 'Amount should be larger then 0. Try again. Enter amount:')
        bot.register_next_step_handler(message, summa)


@bot.callback_query_handler(func=lambda curr: True)
def callback_currency(curr):
    if curr.data != 'else':
        values = curr.data.upper().split('/')
        res = currency.convert(amount, values[0], values[1])
        bot.send_message(curr.message.chat.id, f'Result:{round(res, 2)}. You can enter new amount again')
        bot.register_next_step_handler(curr.message, summa)
    else:
        bot.send_message(curr.message.chat.id, "Enter two currencies as in the example __/__: ")
        bot.register_next_step_handler(curr.message, my_currency)

def my_currency(message):
    try:
        values = message.text.upper().split('/')
        res = currency.convert(amount, values[0], values[1])
        bot.send_message(message.chat.id, f'Result:{round(res, 2)}. You can enter new amount again')
        bot.register_next_step_handler(message, summa)
    except Exception:
        bot.send_message(message.chat.id, "Something went wrong, try again.\n Enter two currencies as in the example __/__: ")
        bot.register_next_step_handler(message, my_currency)


# This function can register users and store them in database
@bot.message_handler(commands=['registration'])
def registr(message):
    conn = sqlite3.connect('itproger.sql')
    cur = conn.cursor()

    cur.execute('CREATE TABLE IF NOT EXISTS users (id int auto_increment primary key, name varchar(50), pass varchar(50))')
    conn.commit()
    cur.close()
    conn.close() #close connection with database
    bot.send_message(message.chat.id, 'Hi, we will register you in our bd, enter your name')
    bot.register_next_step_handler(message, user_name)

def user_name(message):
    global name
    name = message.text.strip()
    bot.send_message(message.chat.id, 'Enter password')
    bot.register_next_step_handler(message, user_pass)

def user_pass(message):
    password = message.text.strip()

    conn = sqlite3.connect('itproger.sql')
    cur = conn.cursor()

    cur.execute("INSERT INTO users (name, pass) VALUES ('%s', '%s')"%(name, password))
    conn.commit()
    cur.close()
    conn.close()
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('List of users', callback_data='users'))
    bot.send_message(message.chat.id, 'User registered', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    conn = sqlite3.connect('itproger.sql')
    cur = conn.cursor()

    cur.execute("SELECT * FROM users")
    users = cur.fetchall()
    info = ''
    for el in users:
        info += f'name: {el[1]}, password: {el[2]}\n'
    cur.close()
    conn.close()

    bot.send_message(call.message.chat.id, info)



# function to get temperature by enter city
@bot.message_handler(commands=['weather'])
def weather(message):
    bot.send_message(message.chat.id, "Hi nice too meet you! write the name of city: ")

# user will enter text
@bot.message_handler(content_types=['text'])
def get_weather(message):
    city = message.text.strip().lower()
    res = requests.get(f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API}&units=metric')
    if res.status_code == 200:
        data = json.loads(res.text)
        temp = data["main"]["temp"]
        bot.reply_to(message, f'Weather now: {temp}')

        image = 'sun.png' if temp>25.0 else 'sun_cloud.jpg'
        file = open('./' + image, 'rb')
        bot.send_photo(message.chat.id, file)
        return
    else:
        bot.reply_to(message, f"I don't now this city")





# Function to open website in link
@bot.message_handler(commands=['site', 'website'])
def site(message):
    webbrowser.open('https://itproger.com')




# @bot.message_handler(commands=['start'])
# def start(message):
#     markup = types.ReplyKeyboardMarkup()
#     btn1 = types.KeyboardButton('Go to site')
#     markup.row(btn1)
#     btn2 = types.InlineKeyboardButton('Delete photo')
#     btn3 = types.InlineKeyboardButton('Edit text') #now buttons just send text in chat
#     markup.row(btn2, btn3)
#     bot.send_message(message.chat.id, 'Hey bro!', reply_markup=markup)
#     # if we want to do something with this text
#     bot.register_next_step_handler(message, on_click)
#
# def on_click(message):
#     if message.text == 'Go to site':
#         bot.send_message(message.chat.id, 'website is open')
#
#     elif message.text == 'Delete photo':
#         bot.send_message(message.chat.id, 'photo was deleted')





#
# @bot.message_handler(commands=['help'])
# #parametr will store information about user and chat
# def main(message):
#     # from parametr message we can get id of my chat
#     bot.send_message(message.chat.id, '<b>Help</b> <em><u>information</u></em>!', parse_mode='html')

#how to get file or image
#inline buttons(кнопки около сообщения)
# @bot.message_handler(content_types=['photo'])
# def get_photo(message):
#     markup = types.InlineKeyboardMarkup()
#     btn1 = types.InlineKeyboardButton('Go to site', url='https://itproger.com')
#     markup.row(btn1)
#     btn2 = types.InlineKeyboardButton('Delete photo', callback_data='delete')
#     btn3 = types.InlineKeyboardButton('Edit text', callback_data='edit')
#     markup.row(btn2, btn3)
#     bot.reply_to(message, 'what a beautiful photo', reply_markup=markup)

# @bot.callback_query_handler(func = lambda callback: True)
# def callback_message(callback):
#     if callback.data == 'delete':
#         bot.delete_message(callback.message.chat.id, callback.message.message_id - 1) #delete previous message
#     elif callback.data == 'edit':
#         bot.edit_message_text('Edit text', callback.message.chat.id, callback.message.message_id)

@bot.message_handler()
def info(message):
    if message.text.lower() == 'hello':
        bot.send_message(message.chat.id, f'Hello,  {message.from_user.first_name} {message.from_user.last_name}')
    elif message.text.lower() == 'id':
        bot.reply_to(message, f'ID: {message.from_user.id}')
    elif message.text.lower() == 'stop':
        bot.reply_to(message, f'ID: {message.from_user.id}')

#bot.infinity_polling()

bot.polling(none_stop=True) #program will always work