import telebot
import sqlite3
from telebot import types
import csv
import datetime
from dotenv import load_dotenv
import os
import threading
from telebot.apihelper import ApiTelegramException

load_dotenv()

 
bot = telebot.TeleBot(os.getenv('BOT_TOKEN'))


with sqlite3.connect('users.db') as conn:
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users
             (
              chat_id INTEGER NOT NULL PRIMARY KEY,
              full_name TEXT NOT NULL,
              completed INTEGER DEFAULT 0)''')
    conn.commit()



@bot.message_handler(commands=['start'])
def handle_start(message):
    try:
        sent_msg = bot.send_message(message.chat.id, "Пожалуйста, введите ваше ФИО (ответом на это сообщение)")
    except ApiTelegramException as e:
        print(e.description, ' in ', message.chat.id)
        clear_blocker(message.chat.id)
    bot.register_next_step_handler(sent_msg, handle_name)


@bot.message_handler(commands=['get_list'])
def handle_get_list(message):
    with sqlite3.connect('users.db') as conn:
        c = conn.cursor()
        c.execute('SELECT full_name, completed FROM users')
        users = c.fetchall()

    with open('users.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['full_name', 'completed'])
        writer.writerows(users)

    with open('users.csv', 'rb') as f:
        bot.send_document(message.chat.id, f)

    os.remove('users.csv')
        

def handle_name(message):
    with sqlite3.connect('users.db') as conn:
        c = conn.cursor()
        c.execute('INSERT INTO users values(?, ?, ?)', (message.chat.id, message.text, 0))

        conn.commit()

    try:
        bot.send_message(message.chat.id, f"Добро пожаловать, {message.text}!")
    except ApiTelegramException as e:
        clear_blocker(message.chat.id)
        print(e.description, ' in ', message.chat.id)
    send_messages_upd()



def send_messages_upd():
    with sqlite3.connect('users.db') as conn:
        c = conn.cursor()

        message_text = 'Салем! Вы уже подписали документ?'

        keyboard = types.InlineKeyboardMarkup()
        approve_button = types.InlineKeyboardButton(text='Да', callback_data='approve')
        disapprove_button = types.InlineKeyboardButton(text='Пока нет:(', callback_data='disapprove')
        keyboard.add(approve_button, disapprove_button)

        
        for user in c.execute("SELECT * FROM users WHERE completed=0"):
            try:
                bot.send_message(user[0], message_text, reply_markup=keyboard)
            except ApiTelegramException as e:
                print(e.description, ' in ', user[0])
                clear_blocker(user[0])
  


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):

    if call.message:
        if call.data == "approve":
            chat_id = call.from_user.id
            provide_confirmation(chat_id)
            pass
        else:
            keyboard = types.InlineKeyboardMarkup()
            link_button = types.InlineKeyboardButton(text='Подписать!', url='https://astanahub.com/ru/')
            keyboard.add(link_button)
            try:
                bot.send_message(call.message.chat.id, 'Можете подписать по ссылке:', reply_markup=keyboard)
            except ApiTelegramException as e:
                print(e.description, ' in ', call.message.chat.id)
                clear_blocker(call.message.chat.id)



def provide_confirmation(chat_id):
    try:
        sent_msg = bot.send_message(chat_id, 'Пожалуйста подтвердите, что вы подписали документ, отправьте screenshot')
    except ApiTelegramException as e:
        print(e.description, ' in ', chat_id)
        clear_blocker(chat_id)
    bot.register_next_step_handler(sent_msg, handle_confirmation)


def handle_confirmation(message, content_types=['photo']):
    if message.content_type != 'photo':
        try:
            sent_msg = bot.reply_to(message, 'Пожалуйста, отправьте изображение')
        except ApiTelegramException as e:
            print(e.description, ' in ', message.chat.id)
            clear_blocker(message.chat.id)
        bot.register_next_step_handler(sent_msg, handle_confirmation)
        return
    else:
        with sqlite3.connect('users.db') as conn:
            c = conn.cursor()
            c.execute('UPDATE users SET completed=1 WHERE chat_id=?', (message.chat.id, ))
            conn.commit()
        try:
            bot.reply_to(message, 'Спасибо!')
        except ApiTelegramException as e:
            print(e.description, ' in ', message.chat.id)
            clear_blocker(message.chat.id)


def schedule_messages():
    send_messages_upd()

    next_run = datetime.datetime.now() + datetime.timedelta(hours=4)
    delay = (next_run - datetime.datetime.now()).total_seconds()
    threading.Timer(delay, schedule_messages).start()


def clear_blocker(chat_id):
    with sqlite3.connect('users.db') as conn:
        c = conn.cursor()
        c.execute('DELETE FROM users WHERE chat_id=?', (chat_id, ))
        conn.commit()


schedule_messages()
bot.polling()
