import telebot
from telebot import types
import csv
import datetime
from dotenv import load_dotenv
import os
import threading
from telebot.apihelper import ApiTelegramException
from supabase import create_client


load_dotenv()

 
bot = telebot.TeleBot(os.getenv('BOT_TOKEN'))
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SECRET_KEY')
supabase = create_client(url, key)




def get_users():
    data, count = supabase.table('users').select("*").execute()

    users = [list(user.values()) for user in data[1]]
    return users

def add_user(chat_id, full_name):
    try:
        data, count = supabase.table('users').insert({"chat_id": chat_id, "full_name": full_name}).execute()
    except Exception as e:

        raise e
    print(data)


def get_public_users():
    data, count = supabase.table('users').select("full_name, completed").execute()

    users = [list(user.values()) for user in data[1]]
    return users

def update_user(chat_id):
    try:
        data, count = supabase.table('users').update({"completed": 1}).eq('chat_id', chat_id).execute()
    except Exception as e:
        raise e
    return data



# with sqlite3.connect('users.db') as conn:
#     c = conn.cursor()

#     c.execute('''CREATE TABLE IF NOT EXISTS users
#              (
#               chat_id INTEGER NOT NULL PRIMARY KEY,
#               full_name TEXT NOT NULL,
#               completed INTEGER DEFAULT 0)''')
#     conn.commit()



@bot.message_handler(commands=['start'])
def handle_start(message):
    try:
        sent_msg = bot.send_message(message.chat.id, "Пожалуйста, введите ваше ФИО (ответом на это сообщение)")
    except ApiTelegramException as e:
        print(e.description, ' in ', message.chat.id)

    bot.register_next_step_handler(sent_msg, handle_name)


@bot.message_handler(commands=['get_list'])
def handle_get_list(message):

    users = get_public_users()

    with open('users.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['full_name', 'completed'])
        writer.writerows(users)

    with open('users.csv', 'rb') as f:
        bot.send_document(message.chat.id, f)

    os.remove('users.csv')
        

def handle_name(message):
    if message.text is not None or message.text != '':
        add_user(message.chat.id, message.text)
    else:
        handle_start(message)
        
    try:
        bot.send_message(message.chat.id, f"Добро пожаловать, {message.text}!")
    except ApiTelegramException as e:
        print(e.description, ' in ', message.chat.id)
    
    # send_messages_upd()
    send_message_to_user(message.chat.id)


def send_message_to_user(chat_id):
    message_text = 'Салем! Вы уже подписали документ?'

    keyboard = types.InlineKeyboardMarkup()
    approve_button = types.InlineKeyboardButton(text='Да', callback_data='approve')
    disapprove_button = types.InlineKeyboardButton(text='Пока нет:(', callback_data='disapprove')
    keyboard.add(approve_button, disapprove_button)

    try:
        bot.send_message(chat_id, message_text, reply_markup=keyboard)
    except ApiTelegramException as e:
        print(e.description, ' in ', chat_id)



def send_messages_upd():


    message_text = 'Салем! Вы уже подписали документ?'

    keyboard = types.InlineKeyboardMarkup()
    approve_button = types.InlineKeyboardButton(text='Да', callback_data='approve')
    disapprove_button = types.InlineKeyboardButton(text='Пока нет:(', callback_data='disapprove')
    keyboard.add(approve_button, disapprove_button)

    for user in get_users():
        chat_id = user[0]
        completed = user[2]

        if completed == False:
            try:
                bot.send_message(chat_id, message_text, reply_markup=keyboard)
            except ApiTelegramException as e:
                print(e.description, ' in ', chat_id)

  


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




def provide_confirmation(chat_id):
    try:
        sent_msg = bot.send_message(chat_id, 'Пожалуйста подтвердите, что вы подписали документ, отправьте screenshot')
    except ApiTelegramException as e:
        print(e.description, ' in ', chat_id)

    bot.register_next_step_handler(sent_msg, handle_confirmation)


def handle_confirmation(message, content_types=['photo']):
    if message.content_type != 'photo':
        try:
            sent_msg = bot.reply_to(message, 'Пожалуйста, отправьте изображение')
        except ApiTelegramException as e:
            print(e.description, ' in ', message.chat.id)

        bot.register_next_step_handler(sent_msg, handle_confirmation)
        return
    else:
        update_user(message.chat.id)

        try:
            bot.reply_to(message, 'Спасибо!')
        except ApiTelegramException as e:
            print(e.description, ' in ', message.chat.id)



def schedule_messages():
    send_messages_upd()

    next_run = datetime.datetime.now() + datetime.timedelta(hours=4)
    delay = (next_run - datetime.datetime.now()).total_seconds()
    threading.Timer(delay, schedule_messages).start()



schedule_messages()
bot.polling()
