
from aiogram import types
from create_bot import dp
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand

SERVERS = [
    "№0 [Ничего]",
    "№1 [Phoenix]",
    "№2 [Tucson]",
    "№3 [Scottdale]",
    "№4 [Chandler]",
    "№5 [Brainburg]",
    "№6 [Saint Rose]",
    "№7 [Mesa]",
    "№8 [Red-Rock]",
    "№9 [Yuma]",
    "№10 [Surprise]",
    "№11 [Prescott]",
    "№12 [Glendale]",
    "№13 [Kingman]",
    "№14 [Winslow]",
    "№15 [Payson]",
    "№16 [Gilbert]",
    "№17 [Show Low]",
    "№18 [Casa-Grande]",
    "№19 [Page]",
    "№20 [Sun-City]",
    "№21 [Queen-Creek]",
    "№22 [Sedona]",
    "№23 [Holiday]",
    "№24 [Wednesday]",
    "№25 [Yava]",
    "№26 [Faraway]",
    "№27 [Bumble Bee]",
    "№28 [Christmas]",
]

async def set_default_commands(dp):
    await dp.bot.set_my_commands([
        BotCommand("start", "Запустить бота 🔥")
    ])

def check_user_adm(user_id):
    with open("text/admins.txt", 'r') as file:
        banned_users = file.read()

    return True

    
def pc_or_mobile():
    keyboard = InlineKeyboardMarkup()
    YooMoney = InlineKeyboardButton('🖥 ПК', callback_data='server_type_pc')
    Qiwi = InlineKeyboardButton('📱 МОБАЙЛ', callback_data='server_type_mobile')
    keyboard.add(YooMoney, Qiwi)
    return keyboard

def send_or_not():
    keyboard = InlineKeyboardMarkup()
    YooMoney = InlineKeyboardButton('✅ ОТПРАВИТЬ', callback_data='yes_send')
    Qiwi = InlineKeyboardButton('❌ УДАЛИТЬ', callback_data='no_send')
    keyboard.add(YooMoney, Qiwi)
    return keyboard

def check_func(user_id):
    if check_user_adm(user_id):
        keyboard = InlineKeyboardMarkup()
        YooMoney = InlineKeyboardButton("🎲 Любая", callback_data='random')
        Qiwi = InlineKeyboardButton("⚙ Параметры", callback_data='parametr')
        keyboard.add(YooMoney, Qiwi)
        return keyboard
    
def sort_by(user_id, data):
    if check_user_adm(user_id):
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton(f"{'✅' if data.get('server', False) else '❌'} Cервер", callback_data='sort_server'))
        keyboard.add(InlineKeyboardButton(f"{'✅' if data.get('time', False) else '❌'} Время", callback_data='sort_time'))
        keyboard.add(InlineKeyboardButton(f"{'✅' if data.get('nick', False) else '❌'} Никнейм", callback_data='sort_nick'))
        keyboard.add(InlineKeyboardButton(f"{'✅' if data.get('tags', False) else '❌'} Теги", callback_data='sort_tags'))
        keyboard.add(InlineKeyboardButton(f"▶️ Начать поиск", callback_data='sort_start'))

        return keyboard

def sort_by_time(user_id):
    if check_user_adm(user_id):
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("🆕 Новые", callback_data='time_new'))
        keyboard.add(InlineKeyboardButton("🦥 Старые", callback_data='time_old'))
        return keyboard

def sort_by_server(user_id):
    keyboard = InlineKeyboardMarkup(row_width=2)
    for i in range(1, len(SERVERS), 2):
        unique_id_1 = f"server_{i}"
        unique_id_2 = f"server_{i+1}" if i + 1 < len(SERVERS) else None

        button_1 = InlineKeyboardButton(SERVERS[i], callback_data=unique_id_1)

        # Добавляем кнопку только если она существует
        if unique_id_2:
            button_2 = InlineKeyboardButton(SERVERS[i+1], callback_data=unique_id_2)
            keyboard.add(button_1, button_2)
        else:
            keyboard.add(button_1)


    return keyboard

def check_or_not(user_id, unique_id):
    keyboard = InlineKeyboardMarkup()
    YooMoney = InlineKeyboardButton('✅  ОДОБРИТЬ', callback_data=f'yes_check_{unique_id}')
    Qiwi = InlineKeyboardButton('❌ ОТКЛОНИТЬ', callback_data=f'no_check_{unique_id}')
    Ban = InlineKeyboardButton('🛑 ЗАБАНИТЬ', callback_data=f'ban_{user_id}')
    Comeback = InlineKeyboardButton('⬅ НАЗАД', callback_data=f'comeback') 
    keyboard.add(YooMoney, Qiwi)
    keyboard.add(Ban, Comeback)
    return keyboard

def full_reviewed(user_id, unique_id):
    keyboard = InlineKeyboardMarkup()
    YooMoney = InlineKeyboardButton('✅  РАЗОБРАЛИСЬ', callback_data=f'yes_review_{unique_id}')
    Ban = InlineKeyboardButton('📞 СВЯЗАТЬСЯ АНОНИМНО', callback_data=f'connect_{user_id}')
    delete = InlineKeyboardButton('🗑 CКРЫТЬ', callback_data=f'hide') 
    keyboard.add(YooMoney)
    keyboard.add(Ban)
    keyboard.add(delete)
    return keyboard


def get_ban_unban(message_ids, channel_id):
    keyboard = InlineKeyboardMarkup()
    yes_message = InlineKeyboardButton('Забанить', callback_data=f'banned_{message_ids}')
    no_message = InlineKeyboardButton('Разбанить', callback_data=f'unban_{channel_id}')
    keyboard.add(yes_message,  no_message)
    return keyboard