# - *- coding: utf- 8 - *-
from aiogram.types import ReplyKeyboardMarkup

def check_user_adm(user_id):
     return True

def check_user_adm(user_id):
    return True

def moder_func(user_id):
    if check_user_adm(user_id):
        menu_default = ReplyKeyboardMarkup(resize_keyboard=True)
        menu_default.row("✔️ Одобренные", "📝 Проверка")
        menu_default.row("📞 Всего жалоб", "ℹ️ Информация")
        menu_default.row("⬅ На главную")

        return menu_default

def check_user_out_func(user_id):
    menu_default = ReplyKeyboardMarkup(resize_keyboard=True)
    menu_default.row("💎 Подать жалобу", "🎁 Система наград")
    menu_default.row("📞 Тех.поддержка", "📖 Информация")
    if check_user_adm(user_id):
        menu_default.row("⚙ Модерация")
    return menu_default

all_back_to_main_default = ReplyKeyboardMarkup(resize_keyboard=True)
all_back_to_main_default.row("⬅ На главную")

