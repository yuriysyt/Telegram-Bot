from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
storage = MemoryStorage()

bot = Bot(token='', parse_mode='HTML')
dp = Dispatcher(bot, storage=storage)

