from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
storage = MemoryStorage()

bot = Bot(token='6936045382:AAHu7SFXgiYWV4RxHpQ840a9NZ-B_Ifd2_o', parse_mode='HTML')
dp = Dispatcher(bot, storage=storage)

