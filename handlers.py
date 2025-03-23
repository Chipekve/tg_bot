import telebot
from config import API_TOKEN, PRODUCTS, ADMIN_ID
from keyboards import get_main_menu, get_store_menu, get_product_menu, get_main_menu_button, get_work_with_us_keyboard
from utils import generate_order_number, log_confirmation
from telebot.types import ForceReply
import sqlite3

bot = telebot.TeleBot(API_TOKEN)

def init_db():
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()

    # Таблица для заказов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id TEXT NOT NULL,
            key TEXT UNIQUE,
            product_price TEXT NOT NULL,
            order_number TEXT NOT NULL UNIQUE,
            status TEXT DEFAULT 'pending'
        )
    ''')

    # Таблица для ключей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT NOT NULL,
            key TEXT NOT NULL UNIQUE
        )
    ''')

    conn.commit()
    conn.close()

init_db()

def add_order(user_id, product_id, product_price, order_number):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()

    try:
        # Проверяем наличие ключа для товара
        cursor.execute('SELECT key FROM keys WHERE product_id = ? LIMIT 1', (product_id,))
        key_result = cursor.fetchone()
        if not key_result:
            raise ValueError("❌ЗАКОНЧИВСЯ!!")

        key = key_result[0]  # Извлекаем ключ из результата запроса

        # Проверяем, что key является строкой
        if not isinstance(key, str):
            raise ValueError("❌ Некорректный формат ключа.")

        # Добавляем заказ с ключом
        cursor.execute('''
            INSERT INTO orders (user_id, product_id, product_price, order_number, key)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, product_id, product_price, order_number, key))

        conn.commit()
    except Exception as e:
        print(f"Ошибка в add_order: {e}")  # Логируем ошибку
        raise e  # Пробрасываем исключение дальше
    finally:
        conn.close()

def get_order(order_number):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM orders WHERE order_number = ?', (order_number,))
    order = cursor.fetchone()
    conn.close()
    return order

def update_order_status(order_number, status):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE orders SET status = ? WHERE order_number = ?', (status, order_number))
        conn.commit()
        print(f"Статус заказа {order_number} обновлён на {status}")  # Логируем обновление
    except Exception as e:
        print(f"Ошибка при обновлении статуса заказа: {e}")  # Логируем ошибку
    finally:
        conn.close()

def add_key(product_id, key):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO keys (product_id, key) VALUES (?, ?)', (product_id, key))
    conn.commit()
    conn.close()

def delete_key(key):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM keys WHERE key = ?', (key,))
    conn.commit()
    conn.close()

def get_key(product_id):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT key FROM keys WHERE product_id = ? LIMIT 1', (product_id,))
    key = cursor.fetchone()
    conn.close()
    return key[0] if key else None  # Возвращаем ключ или None, если ключей нет

@bot.message_handler(commands=['start'])
def main_menu(message):
    photo_url = 'https://ibb.co/Y3cNMDn'
    welcome_text = """Привет! \nТы попал в магазин ключей."""
    bot.send_photo(chat_id=message.chat.id, photo=photo_url, caption=welcome_text, reply_markup=get_main_menu()
    )

@bot.callback_query_handler(func=lambda call: call.data == "contact_admin")
def contact_admin_handler(call):
    bot.send_message(
        call.message.chat.id,
        "✍️ Напишите ваше сообщение администратору:",
        reply_markup=ForceReply(selective=True)
    )
    bot.register_next_step_handler(call.message, forward_to_admin)

def forward_to_admin(message):
    try:
        bot.send_message(
            ADMIN_ID,
            f"✉️ *Новое сообщение от пользователя:*\n"
            f"ID: `{message.from_user.id}`\n"
            f"Username: @{message.from_user.username}\n"
            f"Текст:\n```\n{message.text}\n```",
            parse_mode="Markdown"
        )
        bot.reply_to(
            message,
            "✅ Ваше сообщение отправлено администратору!",
            reply_markup=get_main_menu_button()  # Добавляем кнопку
        )
    except Exception as e:
        bot.reply_to(
            message, "❌ Произошла ошибка. Попробуйте позже.",
            reply_markup=get_main_menu_button()
        )

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    # Обработка callback-запросов
    if call.data == "show_store":
        bot.send_message(call.message.chat.id, "Выберите товар:", reply_markup=get_store_menu())
    elif call.data == "work_with_us":
        bot.send_message(
            call.message.chat.id,
            "🚀 *Работа с нами*\n\n"
            "Мы всегда рады новым сотрудникам и партнерам! Если ты хочешь присоединиться к нашей команде, "
            "Свяжись с администрацией через кнопку ниже.",
            parse_mode="Markdown",
            reply_markup=get_work_with_us_keyboard()
        )
    elif call.data.startswith("view_product_"):
        product_index = int(call.data.split("_")[2])
        product = PRODUCTS[product_index]
        bot.send_photo(
            call.message.chat.id,
            photo=product["photo_url"],
            caption=f"{product['name']}\n{product['description']}\nЦена: {product['price']}",
            reply_markup=get_product_menu(product_index),
        )
    elif call.data.startswith("buy_product_"):
        product_index = int(call.data.split("_")[2])
        product = PRODUCTS[product_index]
        order_number = generate_order_number()

        try:
            # Проверяем наличия ключа
            key = get_key(product["id"])
            if not key:
                bot.send_message(call.message.chat.id, "❌Соре, закончився (")
                return

            # Сохраняем заказ в базу данных
            add_order(
                user_id=call.message.chat.id,
                product_id=product["id"],
                product_price=product["price"],
                order_number=order_number
            )
        except ValueError as e:
            bot.send_message(call.message.chat.id, str(e))
            return
        except Exception as e:
            print(f"Ошибка при создании заказа: {e}")  # Логируем ошибку в консоль
            bot.send_message(call.message.chat.id, "❌ Произошла ошибка при создании заказа. Попробуйте позже.")
            return

        try:
            bot.send_message(
                ADMIN_ID,
                f"🛒 Новый заказ!\n\n"
                f"Покупатель: {call.message.chat.id}\n"
                f"Товар: {product['name']}\n"
                f"Цена: {product['price']}\n"
                f"Номер заказа: {order_number}\n\n"
                "Подтвердите оплату, отправив:\n"
                f"/confirm {call.message.chat.id} {order_number}",
                parse_mode="Markdown"
            )
        except Exception as e:
            bot.send_message(call.message.chat.id,
                             "❌ Произошла ошибка при отправке заказа администратору. Попробуйте позже.")
            return

        bot.send_message(
            call.message.chat.id,
            f"📋 Для завершения покупки переведите {product['price']} на реквизиты.\n\n"
            f"💳 *Реквизиты:* 1234 5678 9012 3456\n\n"
            f"📌 Обязательно добавь комментарий к платежу: *{order_number}*\n"
            f"Иначе мы не сможем проверить его."
            "\nПосле оплаты дождитесь подтверждения.\nЕсли возникли вопросы, свяжитесь с администратором.",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
    elif call.data == "back_to_main":
        bot.answer_callback_query(call.id)
        main_menu(call.message)

@bot.message_handler(commands=['confirm'])
def confirm_payment(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "⛔ У вас нет прав для выполнения этой команды.")
        return

    try:
        _, user_id, order_number = message.text.split()
        user_id = int(user_id)

        # Ищем заказ в базе данных
        order = get_order(order_number)
        if not order:
            bot.reply_to(message, "❌ Заказ с таким номером не найден.")
            return

        # Проверяем принадлежность заказа пользователю
        if order[1] != user_id:  # order[1] — это user_id
            bot.reply_to(message, "❌ Этот заказ не принадлежит указанному пользователю.")
            return

        # Проверяем статус заказа
        print(f"Статус заказа: {order[6]}")  # Логируем статус заказа
        if order[6] != "pending":
            bot.reply_to(message, "❌ Этот заказ уже обработан.")
            return

        # Получаем ключ из заказа
        key = order[3]  # order[3] — это key
        if not key:
            bot.reply_to(message, "❌ Ключ для данного заказа не найден.")
            return

        # Отправляем ключ пользователю
        bot.send_message(
            order[1],  # order[1] — это user_id
            f"🎉 Оплата подтверждена!\nВаш ключ: {key}\nСпасибо за покупку!",
            parse_mode="Markdown",
            reply_markup=get_main_menu_button()
        )

        # Логируем подтверждение
        username = bot.get_chat(order[1]).username
        log_confirmation(order[1], username, order[4], order[5], key, order_number)
        # order[4] — product_price, order[5] — order_number
        # Уведомляем администратора
        bot.reply_to(
            message,
            f"✅ Покупателю {order[1]} отправлен товар: {order_number},\n Цена: {order[4]}.",
            parse_mode="Markdown"
        )

        # Обновляем статус заказа
        update_order_status(order_number, "completed")
        delete_key(key)
    except ValueError:
        bot.reply_to(message, "❌ Использование: /confirm [user_id] [order_number]")
    except Exception as e:
        bot.reply_to(message, f"❌ Произошла ошибка: {e}")