import aiogram
import re
import datetime
import time, random
import asyncio
from aiogram.types import CallbackQuery
from setting import * 
from database import create_bdx, add_complaint, find_complaint, get_complaints_stats, get_user_id_by_unique_id, update_complaint_status, get_earliest_complaint
from create_bot import dp, bot
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from keyboard.default.menu import check_user_out_func, all_back_to_main_default, moder_func, check_user_adm 
from keyboard.inline.get_ban_unban import pc_or_mobile, set_default_commands, send_or_not, full_reviewed, check_or_not, check_func, sort_by, sort_by_server, sort_by_time
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from aiogram.dispatcher import DEFAULT_RATE_LIMIT
from aiogram.dispatcher.handler import CancelHandler, current_handler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.utils.exceptions import Throttled

storage = RedisStorage2(db=5)


def rate_limit(limit: int, key=None):

    def decorator(func):
        setattr(func, 'throttling_rate_limit', limit)
        if key:
            setattr(func, 'throttling_key', key)
        return func

    return decorator


class ThrottlingMiddleware(BaseMiddleware):

    def __init__(self, limit=DEFAULT_RATE_LIMIT, key_prefix='antiflood_'):
        self.rate_limit = limit
        self.prefix = key_prefix
        super(ThrottlingMiddleware, self).__init__()

    async def on_process_message(self, message: types.Message, data: dict):
        handler = current_handler.get()
        dispatcher = Dispatcher.get_current()
        if handler:
            limit = getattr(handler, 'throttling_rate_limit', self.rate_limit)
            key = getattr(handler, 'throttling_key', f"{self.prefix}_{handler.__name__}")
        else:
            limit = self.rate_limit
            key = f"{self.prefix}_message"

        try:
            await dispatcher.throttle(key, rate=limit)
        except Throttled as t:
            await self.message_throttled(message, t)

            raise CancelHandler()

    async def message_throttled(self, message: types.Message, throttled: Throttled):
        """
        Notify user only on first exceed and ignore additional commands for some time

        :param message:
        :param throttled:
        """
        handler = current_handler.get()
        dispatcher = Dispatcher.get_current()
        if handler:
            key = getattr(handler, 'throttling_key', f"{self.prefix}_{handler.__name__}")
        else:
            key = f"{self.prefix}_message"

        # Calculate how many time is left till the block ends
        delta = throttled.rate - throttled.delta

        # Prevent flooding
        if throttled.exceeded_count == 2:
            await message.reply('🔸 Братиш, ну не флуди :( ')

        # Sleep.
        await asyncio.sleep(delta)

        # Check lock status
        thr = await dispatcher.check_key(key)

        # If current message is not last with current key - do not send message
        if thr.exceeded_count == throttled.exceeded_count:
            # await message.reply('')
             pass

intro_message = (
        "<b>📖 Бот Артуриус: Подача жалобы</b>\n\n"
        "<b>Описание:</b>\n\n"
        "Привет! Добро пожаловать в бота Артуриуса - твоего помощника в подаче анонимных жалоб. "
        "Этот бот предоставляет удобный способ сообщить о нарушениях на сервере, сохраняя при этом твою анонимность.\n\n"
        "<b>Как пользоваться:</b>\n\n"
        "<b>📌 На главной странице:</b>\n"
        "/start: Показывает приветственное сообщение.\n"
        "<b>⬅ На главную:</b> Возвращает на главную страницу.\n"
        "💎 <b>Подать жалобу:</b>\n\n"
        "Выбери сервер: ПК или МОБАЙЛ.\n"
        "Укажи номер своего сервера.\n"
        "Введи никнейм нарушителя (от 3 до 20 символов).\n"
        "Опиши проблему подробно в одном сообщении, предоставь все необходимые доказательства.\n\n"
        "<b>📞 Тех.поддержка:</b>\n\n"
        "Если у тебя возникли трудности, свяжись с технической поддержкой:\n"
        "Телеграм: @yurasalt\n\n"
        "<b>Примечание:</b>\n\n"
        "Твоя анонимность гарантирована.\n"
        "Некорректные и ложные жалобы могут повлечь за собой последствия.\n\n"
        "Благодарим за внимание! Приятного использования бота Артуриуса. 🔸" )

intro_message_moder = (
    "⚙ <b>Модерация</b>\n\n"
    "При нажатии на эту кнопку вы попадете в главное меню модерации, где сможете выбрать раздел "
    "<b>📝 Проверка</b> или <b>✅ Одобренные</b>.\n\n"
    "📝 <b>Проверка</b>\n\n"
    "Этот раздел предназначен для просмотра новых жалоб от пользователей.\n\n"
    "При входе вы увидите две кнопки:\n\n"
    "1) <b>🎲 Любая</b> - откроет случайную жалобу без фильтрации.\n"
    "2) <b>⚙ Параметры</b> - позволит отфильтровать жалобы по различным критериям.\n\n"
    "Если выбрать <b>⚙ Параметры</b>, появятся несколько переключателей для фильтрации:\n\n"
    "- <b>✅ Сервер</b> - фильтр по номеру сервера\n"
    "- <b>✅ Время</b> - фильтр по времени подачи жалобы (новые/старые)\n"
    "- <b>✅ Никнейм</b> - фильтр по никнейму нарушителя\n"
    "- <b>✅ Теги</b> - фильтр по тегам, указанным в жалобе\n\n"
    "После выбора нужных фильтров нажмите <b>▶️ Начать поиск</b>.\n\n"
    "Отобразится жалоба с полной информацией и кнопками действий:\n\n"
    "- <b>✅ Одобрить</b> - принять жалобу\n"
    "- <b>❌ Отклонить</b> - отклонить жалобу (требуется комментарий)\n"
    "- <b>🛑 Забанить</b> - забанить пользователя, подавшего жалобу\n"
    "- <b>⬅ Назад</b> - вернуться к выбору фильтров\n\n"
    "✔️ <b>Одобренные</b>\n\n"
    "В этом разделе находятся ранее одобренные жалобы.\n\n"
    "Кнопка <b>Любая</b> покажет случайную одобренную жалобу.\n"
    "<b>⚙ Параметры</b> позволит отфильтровать жалобы, как и в разделе <b>Проверка</b>.\n\n"
    "Под каждой одобренной жалобой будут следующие кнопки:\n\n"
    "- <b>✅ Разобрались</b> - пометить жалобу как рассмотренную\n"
    "- <b>📞 Связаться анонимно</b> - связаться с пользователем анонимно\n"
    "- <b>🗑 Скрыть</b> - скрыть данную жалобу\n\n"
    "Используйте эти кнопки для эффективного управления жалобами.\n Если возникнут вопросы - обращайтесь к руководству."
)




class ThisStatecer(StatesGroup):
    type = State()
    server = State()
    your_nickname = State()
    enemy_nickname = State()
    information = State()
    finish = State()
    tags = State()

class Moder(StatesGroup):
     comment = State()

class Filter(StatesGroup):
     under_begin = State()
     begin = State()
     server = State()
     time = State()
     nick = State()
     tags = State()
     start_search = State()
     check = State()
     
# Обработка кнопки "На главную" и команды "/start"
@dp.message_handler(regexp="/start", state="*")
@rate_limit(1, 'start')
async def filter_messages2(message: aiogram.types.Message, state: FSMContext):
        await state.finish()
        await message.delete()
        image = open('images/meeten_main.jpeg', 'rb')
        await bot.send_photo(chat_id=message.chat.id, photo=image, caption=f"<b>🔸 Добро пожаловать в бота Артуриуса</b>\n\n"
                            "🔸 Это бот для подачи жалобы\n"
                            "🔸 Используйте кнопки внизу для управления",
                            reply_markup=check_user_out_func(message.chat.id))

@dp.message_handler(regexp="⬅ На главную", state="*")
async def filter_messages2(message: aiogram.types.Message, state: FSMContext):
        await state.finish()
        image = open('images/meeten_main.jpeg', 'rb')
        await bot.send_photo(chat_id=message.chat.id, photo=image, caption=f"<b>🔸 Добро пожаловать в бота Артуриуса</b>\n\n"
                            "🔸 Это бот для анонимной подачи жалобы\n"
                            "🔸 Используйте кнопки внизу для управления",
                            reply_markup=check_user_out_func(message.chat.id))
        
@dp.message_handler(regexp="📞 Тех.поддержка", state="*")
@rate_limit(1, 'start')
async def filter_messages2(message: aiogram.types.Message, state: FSMContext):
        await state.finish()
        await message.delete()
        image = open('images/meeten_main.jpeg', 'rb')
        await bot.send_photo(chat_id=message.chat.id, photo=image, caption=f"<b>🔸 Если у вас возникли трудности пишите: </b>\n\n"
                            "🔸 <b>Телеграм:</b> @yurasalt\n",
                            reply_markup=check_user_out_func(message.chat.id))
        
@dp.message_handler(regexp="📖 Информация", state="*")
@rate_limit(1, 'start')
async def filter_messages2(message: aiogram.types.Message, state: FSMContext):
        await state.finish()
        await message.delete()
        await message.answer(intro_message, parse_mode='HTML')

@dp.message_handler(regexp="ℹ️ Информация", state="*")
@rate_limit(1, 'start')
async def filter_messages2(message: aiogram.types.Message, state: FSMContext):
    
        await state.finish()
        await message.delete()
        await message.answer(intro_message_moder, parse_mode='HTML')

@dp.message_handler(regexp="📞 Всего жалоб", state="*")
@rate_limit(1, 'start')
async def filter_messages2(message: aiogram.types.Message, state: FSMContext):
    
        await state.finish()
        stats = get_complaints_stats()
        text = f"<b>📞 Всего жалоб:</b> <code>{stats['total_complaints']}</code>\n\n"
        text += "<b>Статистика по серверам:</b>\n"
        
        for server, server_stats in stats['server_stats'].items():
            text += f"<b>{server}:</b>\n"
            text += f"  • Всего: <code>{server_stats['total']}</code>\n"
            text += f"  • Проверенные: <code>{server_stats['checked']}</code>\n"
            text += f"  • Непроверенные: <code>{server_stats['unchecked']}</code>\n"
            text += "  • Топ-3 тегов: "
            
            if server_stats['top_tags']:
                top_tags = [f"<code>{tag}</code>" for tag, count in server_stats['top_tags']]
                text += ', '.join(top_tags)
            else:
                text += "<i>нет данных</i>"
            
            text += "\n\n"
        
        await message.answer(text, parse_mode="HTML")

@dp.message_handler(regexp="🎁 Система наград", state="*")
@rate_limit(1, 'start')
async def filter_messages2(message: aiogram.types.Message, state: FSMContext):
        await state.finish()
        await message.reply(
                    "<b>🎁 Система наград за жалобу</b>\n\n"
                    "<b>💰 Вознаграждение за ваш вклад</b>\n\n"
                    "Мы высоко ценим вашу заботу о чистоте наших серверов! За активное участие в борьбе с нарушителями "
                    "мы предлагаем вам систему наград.\n\n"
                    "🏆 В зависимости от важности и актуальности "
                    "вашей жалобы, вы можете рассчитывать на особые бонусы и приятные сюрпризы.\n\n"
                    "Чем детальнее и информативнее ваша жалоба, тем выше шансы получить дополнительные бонусы. Мы всегда стараемся "
                    "поощрять ответственных игроков!\n\n"
                    "Не забывайте: <b>ваша анонимность гарантирована</b>. Благодарим вас за вклад в поддержание порядка на серверах! 🔸",
        parse_mode='HTML'
    )

        
@dp.message_handler(regexp="⚙ Модерация", state="*")
@rate_limit(1, 'start')
async def filter_messages2(message: aiogram.types.Message, state: FSMContext):
    
        await state.finish()
        await message.reply("🔸 <b>Добро пожаловать в панель модерации</b> ",
        reply_markup=moder_func(message.chat.id))

@dp.message_handler(regexp="📝 Проверка", state="*")
async def filter_messages2(message: aiogram.types.Message, state: FSMContext):
    
        await state.finish()
        await message.reply("🔸 <b>Начните проверять жалобы от игроков: </b> \n\n"
                            "<b>🎲 Любая</b> - откроет случайную жалобу без фильтрации.\n"
                            "<b>⚙ Параметры</b> - позволит отфильтровать жалобы по различным критериям.\n\n",
        reply_markup=check_func(message.chat.id))
        await Filter.under_begin.set()
    
@dp.callback_query_handler(text='random', state=Filter.under_begin)
async def qiwi_payment(callback: aiogram.types.CallbackQuery, state: FSMContext):
    if check_user_adm(callback.message.chat.id):
        earliest_complaint = get_earliest_complaint()
        print(earliest_complaint)
        await callback.message.answer(f"🔸 Новая жалоба: \n\n"
                                f"<b>Тип сервера:</b> <code>{earliest_complaint[2]}</code>\n"
                                f"<b>Номер сервера:</b> <code>{earliest_complaint[3]}</code>\n"
                                f"<b>Никнейм нарушителя:</b> <code>{earliest_complaint[4]}</code>\n"
                                f"<b>Время подачи:</b> <code>{earliest_complaint[5]}</code>\n"
                                f"<b>Айди:</b> <code>{earliest_complaint[6]}</code>\n"
                                f"<b>Теги:</b> <code>{earliest_complaint[9]}</code>\n"
                                f"<b>Жалоба:</b> \n\n{earliest_complaint[7]}\n", reply_markup=check_or_not(earliest_complaint[1], earliest_complaint[6]))
        await Filter.check.set()


@dp.message_handler(regexp="✔️ Одобренные", state="*")
async def filter_messages2(message: aiogram.types.Message, state: FSMContext):
    
        await state.finish()
        await message.reply("🔸 <b>Начните поиск проверенных жалоб: </b> \n\n"
                            "<b>🎲 Любая</b> - откроет случайную жалобу без фильтрации.\n"
                            "<b>⚙ Параметры</b> - позволит отфильтровать жалобы по различным критериям.\n\n",
        reply_markup=check_func(message.chat.id))
        async with state.proxy() as data:
            data['only_see'] = 'True'
        await Filter.under_begin.set()
    
@dp.callback_query_handler(text='parametr', state=Filter.under_begin)
async def qiwi_payment(callback: aiogram.types.CallbackQuery, state: FSMContext):
    if check_user_adm(callback.message.chat.id):
        async with state.proxy() as data:
            await callback.message.edit_text("🔸 <b>Пожалуйста, выберите фильтры: </b> \n\n"
                                            "<b>🔹 Сервер</b> - фильтр по номеру сервера\n"
                                            "<b>🔹 Время</b> - фильтр по времени подачи жалобы (новые/старые)\n"
                                            "<b>🔹 Никнейм</b> - фильтр по никнейму нарушителя\n"
                                            "<b>🔹 Теги</b> - фильтр по тегам, указанным в жалобе\n\n",
            reply_markup=sort_by(callback.message.chat.id, data))
        await Filter.begin.set()
        
@dp.callback_query_handler(text='sort_server', state=Filter.begin)
async def qiwi_payment(callback: aiogram.types.CallbackQuery, state: FSMContext):
    if check_user_adm(callback.message.chat.id):
        await callback.message.edit_reply_markup(sort_by_server(callback.message.chat.id))
        await Filter.server.set()


@dp.callback_query_handler(regexp="server_([0-9]*)", state=Filter.server)
async def qiwi_payment(callback: aiogram.types.CallbackQuery, state: FSMContext):
    server = re.findall(r'^server_(\d+)', callback.data)[0]
    if check_user_adm(callback.message.chat.id):
        async with state.proxy() as data:
            data["server"] = server
            print(data)
            await callback.message.edit_reply_markup(sort_by(callback.message.chat.id, data))
            await Filter.begin.set()

@dp.callback_query_handler(text='sort_time', state=Filter.begin)
async def qiwi_payment(callback: aiogram.types.CallbackQuery, state: FSMContext):
    if check_user_adm(callback.message.chat.id):
        await callback.message.edit_reply_markup(sort_by_time(callback.message.chat.id))
        await Filter.time.set()

@dp.callback_query_handler(regexp="time_(new|old)", state=Filter.time)
async def time_handler(callback: aiogram.types.CallbackQuery, state: FSMContext):
    if check_user_adm(callback.message.chat.id):
        time_type = re.findall(r'^time_(new|old)', callback.data)[0]

        async with state.proxy() as data:
            data["time"] = time_type
            await callback.message.edit_reply_markup(sort_by(callback.message.chat.id, data))
            await Filter.begin.set()

@dp.callback_query_handler(text='sort_nick', state=Filter.begin)
async def qiwi_payment(callback: aiogram.types.CallbackQuery, state: FSMContext):
    if check_user_adm(callback.message.chat.id):
        await callback.message.edit_text(text="🔸 <b>Пожалуйста, укажите никнейм: </b> ", reply_markup=None)
        async with state.proxy() as data:
            data["callback"] = callback.message
        await Filter.nick.set()

@dp.message_handler(state=Filter.nick)
async def filter_messages2(message: aiogram.types.Message, state: FSMContext):
    
        async with state.proxy() as data:
            data["nick"] = message.text
            await message.delete()
            callback = data["callback"]
            await callback.edit_text(text="🔸 <b>Пожалуйста, выберите фильтры: </b> ", reply_markup = sort_by(message.chat.id, data))
            data.pop("callback", None)
            print(data)
            await Filter.begin.set()

@dp.callback_query_handler(text='sort_tags', state=Filter.begin)
async def qiwi_payment(callback: aiogram.types.CallbackQuery, state: FSMContext):
    if check_user_adm(callback.message.chat.id):
        await callback.message.edit_text(text=(f"🔸 Пожалуйста, укажите теги: \n\n"
                                    f"<b>Пример:</b> <code>#вирты</code> <code>#админ</code> <code>#слив</code> \n"),
                                      reply_markup=None)
        async with state.proxy() as data:
            data["callback"] = callback.message
        await Filter.tags.set()

@dp.message_handler(state=Filter.tags)
async def filter_messages2(message: aiogram.types.Message, state: FSMContext):
    
        async with state.proxy() as data:
            data["tags"] = message.text
            await message.delete()
            callback = data["callback"]
            await callback.edit_text(text="🔸 <b>Пожалуйста, выберите фильтры: </b> ", reply_markup = sort_by(message.chat.id, data))
            data.pop("callback", None)
            print(data)
            await Filter.begin.set()

@dp.callback_query_handler(text='sort_start', state=Filter.begin)
async def qiwi_payment(callback: aiogram.types.CallbackQuery, state: FSMContext):
    if check_user_adm(callback.message.chat.id):
        async with state.proxy() as data:
            only_see = data.get('only_see', False)
            complaint = find_complaint(data, 1 if only_see else 0)
        if len(complaint) != 0 and not only_see:
            complaint = complaint[0]
            await callback.message.edit_text(f"🔸 Новая жалоба: \n\n"
                                    f"<b>Тип сервера:</b> <code>{complaint[2]}</code>\n"
                                    f"<b>Номер сервера:</b> <code>{complaint[3]}</code>\n"
                                    f"<b>Никнейм нарушителя:</b> <code>{complaint[4]}</code>\n"
                                    f"<b>Время подачи:</b> <code>{complaint[5]}</code>\n"
                                    f"<b>Айди:</b> <code>{complaint[6]}</code>\n"
                                    f"<b>Теги:</b> <code>{complaint[9]}</code>\n"
                                    f"<b>Жалоба:</b> \n\n{complaint[7]}\n", reply_markup=check_or_not(complaint[1], complaint[6]))
            await Filter.check.set()
        elif len(complaint) != 0 and only_see:
            await callback.message.edit_text(f"🔸 Проверенные жалобы: \n\n")
            # Assuming you have the list of complaints stored in the variable 'complaints'
            for complaints in complaint:
                await asyncio.sleep(0.5)
                await callback.message.answer(f"🔸 Проверенная жалоба: \n\n"
                                        f"<b>Тип сервера:</b> <code>{complaints[2]}</code>\n"
                                        f"<b>Номер сервера:</b> <code>{complaints[3]}</code>\n"
                                        f"<b>Никнейм нарушителя:</b> <code>{complaints[4]}</code>\n"
                                        f"<b>Время подачи:</b> <code>{complaints[5]}</code>\n"
                                        f"<b>Айди:</b> <code>{complaints[6]}</code>\n"
                                        f"<b>Теги:</b> <code>{complaints[9]}</code>\n"
                                        f"<b>Жалоба:</b> \n\n{complaints[7]}\n", reply_markup=full_reviewed(complaints[1], complaints[6]))
                await Filter.check.set()
        else:
             await callback.message.edit_text(text="⛔️ <b>По данным фильтрам ничего не найдено, продолжайте проверку: </b> ", reply_markup = sort_by(callback.message.chat.id, data)) 
             await Filter.begin.set()

@dp.callback_query_handler(text='hide', state=Filter.check)
async def qiwi_payment(callback: aiogram.types.CallbackQuery, state: FSMContext):
    await callback.message.delete()

@dp.callback_query_handler(text='comeback', state=Filter.check)
async def qiwi_payment(callback: aiogram.types.CallbackQuery, state: FSMContext):
    if check_user_adm(callback.message.chat.id):
        async with state.proxy() as data:
            await callback.message.edit_text(text="🔸 <b>Пожалуйста, выберите фильтры: </b> ", reply_markup = sort_by(callback.message.chat.id, data))
            await Filter.begin.set()

@dp.message_handler(text="💎 Подать жалобу")
@rate_limit(1, 'start')
async def filter_messages2(message: aiogram.types.Message, state: FSMContext):
    await state.finish()
    print(check_user_banned(message.chat.id))
    if not check_user_banned(message.chat.id):
        await message.delete()
        image = open('images/meeten_nick.jpeg', 'rb')
        msg = await bot.send_photo(chat_id=message.chat.id, photo=image, caption=f"🔸 <b>Отлично, приступим! </b>\n\n"
                            "🔸 Сервер - <b>ПК</b> или <b>МОБАЙЛ</b>? ",
                            reply_markup=pc_or_mobile())
        async with state.proxy() as data:
             data['msg']=  msg
        await ThisStatecer.type.set()
    else:
         await message.answer(f"🔸 <b>К сожалению, вы забанены. Свяжитесь с модерацией. </b>\n\n")
    

@dp.callback_query_handler(regexp="server_type_(pc|mobile)", state=ThisStatecer.type)
async def time_handler(callback: aiogram.types.CallbackQuery, state: FSMContext):
        server_type = re.findall(r'^server_type_(pc|mobile)', callback.data)[0]
        async with state.proxy() as data:
                data["type"] = server_type
                msg = data['msg']
        print(msg)
        await bot.edit_message_caption(
            caption=f"<b>🔸 Теперь нам требуется номер сервера: </b>\n\n"
                            "<b>Укажите номер сервера: </b>",
            chat_id=callback.message.chat.id,
            message_id=msg.message_id,
            reply_markup=None)
        await ThisStatecer.server.set()

@dp.message_handler(state=ThisStatecer.server)
@rate_limit(1, 'start')
async def filter_messages2(message: aiogram.types.Message, state: FSMContext):
    if not check_user_banned(message.chat.id):
        await message.delete()
        status = False
        if message.text.isdigit():
            async with state.proxy() as data:
                type = data["type"]
                msg = data ["msg"]

            if type == "pc":
                if not int(message.text) > 0 or not int(message.text) < 29:
                    await bot.edit_message_caption(
                        caption=f"<b>🔸 Неверно указан номер сервера </b>\n\n"
                                        "Укажите номер вашего сервера: ",
                        chat_id=message.chat.id,
                        message_id=msg.message_id,
                        reply_markup=None)
                    await ThisStatecer.server.set()
                else:
                    status = True


            elif type == "mobile":
                if not int(message.text) > 0 or not int(message.text) < 4:
                    await bot.edit_message_caption(
                        caption=f"<b>🔸 Неверно указан номер сервера </b>\n\n"
                                        "Укажите номер вашего сервера: ",
                        chat_id=message.chat.id,
                        message_id=msg.message_id,
                        reply_markup=None)
                    await ThisStatecer.server.set()
                else:
                    status = True

            if status:
                async with state.proxy() as data:
                            data["number"] = message.text

                await bot.edit_message_caption(
                        caption=f"<b>🔸 Укажите один никнейм нарушителя: </b>",
                        chat_id=message.chat.id,
                        message_id=msg.message_id,
                        reply_markup=None)
                
                await ThisStatecer.enemy_nickname.set()
    else:
        await message.answer(f"🔸 <b>К сожалению, вы забанены. Свяжитесь с модерацией. </b>\n\n")

@dp.message_handler(state=ThisStatecer.enemy_nickname)
@rate_limit(1, 'start')
async def filter_messages2(message: aiogram.types.Message, state: FSMContext):
    await message.delete()
    if len(message.text) > 2 and len(message.text) < 21:
        async with state.proxy() as data:
                data["nickname"] = message.text
                msg = data['msg']
        image = open('images/meeten_nick.jpeg', 'rb')
        await bot.edit_message_caption(
                        caption=f"🔸 <b>Мы практически у цели </b>\n\n"
                                        "Пожалуйста, подробно распишите вашу проблему в одном сообщении\n" 
                                        "Все доказательства должны быть предоставлены ссылкой, иначе Артур их не увидет. ",
                        chat_id=message.chat.id,
                        message_id=msg.message_id,
                        reply_markup=None)
        await ThisStatecer.information.set()
    else:
        await bot.edit_message_caption(
                        caption=f"🔸 <b>Неверно указан нийнейм</b>"
                                    "Его длина должна быть от 3 до 20 симоволов \n\n"
                                            "Укажите никнейм нарушителя: ",
                        chat_id=message.chat.id,
                        message_id=msg.message_id,
                        reply_markup=None)
        await ThisStatecer.enemy_nickname.set()

@dp.message_handler(state=ThisStatecer.information)
async def filter_messages2(message: aiogram.types.Message, state: FSMContext):
    await message.delete()
    async with state.proxy() as data:
        data["information"] = message.text
        msg = data['msg']
        await bot.edit_message_caption(
                        caption=f"🔸 Теперь пожалуйста укажите теги: \n\n"
                                    f"<b>Пример:</b> <code>#вирты</code> <code>#админ</code> <code>#слив</code> \n",
                        chat_id=message.chat.id,
                        message_id=msg.message_id,
                        reply_markup=None)
        await ThisStatecer.tags.set()
        
@dp.message_handler(state=ThisStatecer.tags)
async def filter_messages2(message: aiogram.types.Message, state: FSMContext):
    await message.delete()
    image = open('images/meeten_nick.jpeg', 'rb')
    async with state.proxy() as data:
            data["id"] = generate_complaint_id()
            data["tags"] = message.text
            msg = data['msg']
            await bot.edit_message_caption(
                        caption=f"🔸 Отлично, мы завершили: \n\n"
                                        f"<b>Тип сервера:</b> <code>{data['type']}</code>\n"
                                        f"<b>Номер сервера:</b> <code>{data['number']}</code>\n"
                                        f"<b>Никнейм нарушителя:</b> <code>{data['nickname']}</code>\n"
                                        f"<b>Айди:</b> <code>{data['id']}</code>\n"
                                        f"<b>Теги:</b> <code>{data['tags']}</code>\n"
                                        f"<b>Жалоба:</b> \n\n{data['information']}\n\n",
                        chat_id=message.chat.id,
                        message_id=msg.message_id,
                        reply_markup=send_or_not())
    await ThisStatecer.finish.set()

def generate_complaint_id():
    timestamp = int(time.time())
    random_component = random.randint(1000, 9999)
    complaint_id = f"{timestamp}{random_component}"
    return complaint_id

@dp.callback_query_handler(text='yes_send', state=ThisStatecer.finish)
@rate_limit(1, 'start')
async def qiwi_payment(callback: aiogram.types.CallbackQuery, state: FSMContext):
    await bot.delete_message(callback.message.chat.id, int(callback.message.message_id))
    async with state.proxy() as data:
        data["time"] = get_dates()
        data["user"] = callback.message.chat.id
        image = open('images/meeten_ban.jpeg', 'rb')
        await bot.send_message(group_moderation, f"🔸 Отлично, мы завершили: \n\n"
                                        f"<b>Тип сервера:</b> <code>{data['type']}</code>\n"
                                        f"<b>Номер сервера:</b> <code>{data['number']}</code>\n"
                                        f"<b>Никнейм нарушителя:</b> <code>{data['nickname']}</code>\n"
                                        f"<b>Айди:</b> <code>{data['id']}</code>\n"
                                        f"<b>Теги:</b> <code>{data['tags']}</code>\n"
                                        f"<b>Жалоба:</b> \n\n{data['information']}\n\n", reply_markup=check_or_not(callback.message.chat.id, data['id']))
        await bot.send_photo(chat_id=callback.message.chat.id, photo=image, caption= f"🔸 Отлично, мы завершили: \n\n"
                                        f"<b>Тип сервера:</b> <code>{data['type']}</code>\n"
                                        f"<b>Номер сервера:</b> <code>{data['number']}</code>\n"
                                        f"<b>Никнейм нарушителя:</b> <code>{data['nickname']}</code>\n"
                                        f"<b>Айди:</b> <code>{data['id']}</code>\n"
                                        f"<b>Теги:</b> <code>{data['tags']}</code>\n"
                                        f"<b>Жалоба:</b> \n\n{data['information']}\n\n", reply_markup=check_user_out_func(callback.message.chat.id))
        add_complaint(data)
    await state.finish()
                                                                                
    
@dp.callback_query_handler(text='no_send', state=ThisStatecer.finish)
@rate_limit(1, 'start')
async def qiwi_payment(callback: aiogram.types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback.message.delete()
    await bot.send_message(chat_id=callback.message.chat.id, 
                        text=f"🔸 <b>Не отчаивайтесь! Попробуйте ещё раз! </b> \n\n", reply_markup=check_user_out_func(callback.message.chat.id))

@dp.callback_query_handler(regexp="no_check_([0-9]*)", state=Filter.check)
async def qiwi_payment(callback: aiogram.types.CallbackQuery, state: FSMContext):
    unique_id = re.findall(r'^no_check_(\d+)', callback.data)[0]
    del_msg = await callback.message.reply("🔸 Пожалуйста, прокомментаруйте отказ: ")
    async with state.proxy() as data:
            data["unique_id"] = unique_id
            data["del_msg"] = del_msg
            await callback.message.edit_text(text="🔸 <b>Пожалуйста, выберите фильтры: </b> ", reply_markup = sort_by(callback.message.chat.id, data))
            await Filter.begin.set()
    await Moder.comment.set()


@dp.message_handler(state=Moder.comment)
async def filter_messages2(message: aiogram.types.Message, state: FSMContext):
     await message.delete()
     async with state.proxy() as data:
            user_id = get_user_id_by_unique_id(data["unique_id"])
            await data["del_msg"].delete()
            await bot.send_message(chat_id=user_id, text= "🔸 <b>Ваша жалоба была отклонена </b>\n"
                                                        f"🔸Айди: {data['unique_id']}\n"
                                                        f"🔸 <b>Причина:</b> {message.text}", reply_markup=check_user_out_func(message.chat.id))
            update_complaint_status(data['unique_id'], -1)
     await state.finish()

@dp.callback_query_handler(regexp="yes_check_([0-9]*)", state=Filter.check)
async def qiwi_payment(callback: aiogram.types.CallbackQuery, state: FSMContext):
    unique_id = re.findall(r'^yes_check_(\d+)', callback.data)[0]
    async with state.proxy() as data:
            data["unique_id"] = unique_id
            print(data)
            update_complaint_status(data['unique_id'], 1)
            user_id = get_user_id_by_unique_id(data["unique_id"])
            await bot.send_message(chat_id=user_id, text= "🔸 <b>Ваша жалоба была принята </b>\n"
                                                        f"🔸 Айди: {unique_id}\n", reply_markup=check_user_out_func(user_id))
            await callback.message.edit_text(text="💚 <b>Жалоба принята, продолжайте проверку: </b> ", reply_markup = sort_by(callback.message.chat.id, data))
            await Filter.begin.set()

@dp.callback_query_handler(regexp="yes_review_([0-9]*)", state=Filter.check)
async def qiwi_payment(callback: aiogram.types.CallbackQuery, state: FSMContext):
    unique_id = re.findall(r'^yes_review_(\d+)', callback.data)[0]
    async with state.proxy() as data:
            data["unique_id"] = unique_id
            update_complaint_status(data['unique_id'], 3)
            user_id = get_user_id_by_unique_id(data["unique_id"])
            await bot.send_message(chat_id=user_id, text= "🔸 <b>Ваша жалоба была рассмотрена </b>\n"
                                                        f"🔸 Айди: {unique_id}\n")
            await callback.message.edit_text(text="💚 <b>Жалоба проверена, продолжайте проверку: </b> ", reply_markup = sort_by(callback.message.chat.id, data))
            await Filter.begin.set()

# Получение текущей даты
def get_dates():
    return datetime.datetime.today().replace(microsecond=0)

@dp.message_handler(content_types=['text', 'photo', 'video'])
async def filter_messages2(message: aiogram.types.Message):
    print(message.chat.id)


@dp.callback_query_handler(regexp="ban_([0-9]*)", state=Filter.check)
async def delete_message(call: CallbackQuery):
    get_channel_id_from_out_range = re.findall(r'^ban_(\d+)', call.data)[0]
    with open('text/blacklist.txt', 'a+', encoding='utf-8') as f_1:
        f_1.write(get_channel_id_from_out_range + ' ')
        f_1.flush()
    await call.message.edit_text(f'<b>Пользователь больше не сможет писать</b> \n<b>Его ID: </b> {get_channel_id_from_out_range}\n\nСпасибо, что вы с нами ❤️')



@dp.callback_query_handler(regexp="add_([0-9]*)", state="*")
async def delete_message(call: CallbackQuery):
    get_channel_id_from_out_range = re.findall(r'^ban_(\d+)', call.data)[0]
    with open('text/blacklist.txt', 'a+', encoding='utf-8') as f_1:
        f_1.write(get_channel_id_from_out_range + ' ')
        f_1.flush()
    await call.message.edit_text(f'<b>Пользователь больше не сможет писать</b> \n<b>Его ID: </b> {get_channel_id_from_out_range}\n\nСпасибо, что вы с нами ❤️')

def check_user_banned(user_id):
    return False

@dp.callback_query_handler(regexp="unban_([0-9]*)", state="*")
async def delete_message(call: CallbackQuery):
    get_channel_id_from_out_range = re.findall(r'^unban_(\d+)', call.data)[0]
    await bot.unban_chat_sender_chat(chat_id=username_group_frametamer, sender_chat_id=int('-' + get_channel_id_from_out_range))
    f_1 = open('whitelist.txt', 'a+', encoding='utf-8')
    f_1.write(get_channel_id_from_out_range+' ')
    f_1.close()
    await call.message.edit_text(f'<b>Пользователь разбанен и занесен в белый список</b>\n<b>Его ID: </b> {get_channel_id_from_out_range}  \n\nСпасибо, что вы с нами ❤️')

async def on_startup(dp):
    await set_default_commands(dp)

if __name__ == "__main__":
    create_bdx()
    dp.middleware.setup(ThrottlingMiddleware())
    aiogram.executor.start_polling(dp, skip_updates=True, on_startup=on_startup)