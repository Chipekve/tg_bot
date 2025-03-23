import random
import string
import datetime
import os
from config import BASE_DIR, KEYS_FILE

def generate_order_number():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def log_confirmation(user_id, username, product_name, product_price, key, order_number):
    log_file = os.path.join(BASE_DIR, 'orders.log')
    user_info = f"@{username}" if username else f"ID: {user_id}"
    with open(log_file, 'a') as file:
        file.write(
            f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} - Пользователь: {user_info}\n"
            f"Товар: {product_name}\nЦена: {product_price}\nКлюч: {key}\nНомер заказа: {order_number}\n\n"
        )

def get_key(product_id):
    """
    Получает ключ для товара по его ID.
    Если ключ найден, он удаляется из файла.
    """
    try:
        keys = []
        with open(KEYS_FILE, "r") as file:
            keys = file.readlines()
        for key in keys:
            if key.startswith(product_id):
                keys.remove(key)
                with open(KEYS_FILE, "w") as file:
                    file.writelines(keys)
                return key.split(";")[1].strip()
        return None
    except FileNotFoundError:
        return None