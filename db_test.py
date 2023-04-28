from supabase import create_client, Client
from dotenv import load_dotenv
import os
import csv

load_dotenv()

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SECRET_KEY')
supabase = create_client(url, key)

def add_user(chat_id, full_name):
    data, count = supabase.table('users').insert({"chat_id": chat_id, "full_name": full_name}).execute()
    print(data)


def get_users():
    data, count = supabase.table('users').select("full_name, completed").execute()

    users = [list(user.values()) for user in data[1]]
    return users


def update_user(chat_id):
    data, count = supabase.table('users').update({"completed": 1}).eq('chat_id', chat_id).execute()
    print(data)


update_user(123)
