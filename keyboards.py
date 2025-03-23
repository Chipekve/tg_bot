from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import PRODUCTS

def get_main_menu():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🛍️Витрина", callback_data="show_store"))
    markup.add(InlineKeyboardButton("🤝Работа с нами", callback_data="work_with_us"))
    markup.add(InlineKeyboardButton("📞 Связь с администрацией", callback_data="contact_admin"))  # Новая кнопка
    return markup

def get_main_menu_button():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Главное меню", callback_data="back_to_main"))
    return markup

def get_work_with_us_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📞 Связь с администрацией", callback_data="contact_admin"))
    markup.add(InlineKeyboardButton("Главное меню", callback_data="back_to_main"))
    return markup

def get_store_menu():
    markup = InlineKeyboardMarkup()
    for idx, product in enumerate(PRODUCTS):
        markup.add(InlineKeyboardButton(product["name"], callback_data=f"view_product_{idx}"))
    markup.add(InlineKeyboardButton("Назад", callback_data="back_to_main"))
    return markup

def get_product_menu(product_index):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Купить", callback_data=f"buy_product_{product_index}"))
    markup.add(InlineKeyboardButton("Назад", callback_data="show_store"))
    return markup