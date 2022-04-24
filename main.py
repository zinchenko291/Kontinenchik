import os
import asyncio
import logging
import aioschedule
from datetime import date
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup

from db import BotDB


#Инициализация бота
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
logging.basicConfig(level=logging.INFO)


#Настройки бота
groups = { #Существующие группы
    'запад': 1,
    'восток': 2
}


#Машина состояний
class StateMachine(StatesGroup):
    groupChoose = State()
    wait = State()


#Команда старт
@dp.message_handler(state='*', commands='start')
async def cmdStart(message: types.Message) -> None:
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add('Запад')
    markup.add('Восток')
    await message.answer(f'👋 Привет, {message.from_user.first_name}! Меня зовут Континенчик 🌏, и я буду сопровождать тебя на протяжении всей смены.')
    await asyncio.sleep(0.5)
    if db.userExists(message.from_user.id):
        await message.answer(f'Эй! Я тебя уже знаю. Не волнуйся, я про тебя никогда не забуду 😎!')
    else:
        await message.answer('Можешь не волноваться насчёт пропуска встречи, ведь я обязательно напомню тебе 😉.')
        await asyncio.sleep(0.5)
        await message.answer(f'А теперь давай узнаем кто ты? 🤔 Из какой ты группы', reply_markup=markup)
        await StateMachine.groupChoose.set()

#Выбор группы/потока
@dp.message_handler(state=StateMachine.groupChoose)
async def cmdChooseGroup(message: types.Message, state: FSMContext) -> None:
    removeMarkup = types.ReplyKeyboardRemove()
    if message.text.lower() in groups.keys():
        await message.answer('Всё, я записал. Теперь осталось только ждать ближайшее событие. 😎', reply_markup=removeMarkup)
        user = message.from_user
        db.addUser(user.id, user.first_name, groups.get(message.text.lower()), message.chat.id)
        logging.info(f'Зарегистрирован новый пользователь - {user.id}')
        await state.reset_state(with_data=True)
    else:
        await message.answer(f'😧 Похоже ты указал группу, которую я не знаю. Давай попробуем ещё раз?')
        dp.register_message_handler(cmdChooseGroup)

#Help, видео и ссылки
@dp.message_handler(commands='help')
async def cmdHelp(message: types.Message) -> None:
    await message.answer('Я могу выводить видео о наших международных каникулах или делиться полезными ссылками. 😎')
    await message.answer('/videos - посмотреть записи мероприятий')
    await message.answer('/links - посмотреть полезные ссылки')
    logging.info(f'Команда help от - {message.from_user.id}')

@dp.message_handler(commands='videos')
async def cmdVideos(message: types.Message) -> None:
    await message.answer('Вот наши замечательные видео:')
    for video in db.getVideos():
        await message.answer(f'<a href="{video[1]}">Видео</a> - {video[2]}', parse_mode=types.ParseMode.HTML)
        await asyncio.sleep(0.25)
    logging.info(f'Команда videos от - {message.from_user.id}')

@dp.message_handler(commands='links')
async def cmdLinks(message: types.Message) -> None:
    await message.answer('Вот полезные ссылки:')
    for link in db.getLinks():
        await message.answer(f'<a href="{link[1]}">{link[2]}</a> - {link[3]}', parse_mode=types.ParseMode.HTML)
        await asyncio.sleep(0.25)
    logging.info(f'Команда links от - {message.from_user.id}')

#Блок рассылки
async def broadcaster(link: str, eventDate: str, eventName: str, groupId: int):
    day = int(eventDate[0:2])
    month = int(eventDate[3:5])
    year = int('20' + eventDate[6:8])
    users = [i for i in db.getUsersInGroup(groupId)]
    if date.today().day != day and date.today().month != month and date.today().year != year:
        return
    count = 0
    for user in users:
        try:
            await bot.send_message(user[4], f'Привет, {user[2]}! Приходи к нам на мероприятие - "{eventName}". Торопись! 😉')
            await bot.send_message(user[4], f'Ссылка: {link}')
            await asyncio.sleep(.1)
            count += 1
        except Exception as e:
            logging.error(e)
    logging.info(f'Количество отосланных сообщений: {count}/{len(users)}')
    return aioschedule.CancelJob
async def scheduler() -> None:
    groupsIds = [i[0] for i in db.getGroups()]
    eventsByGroup = []
    for groupId in groupsIds:
        eventsByGroup.append([j for j in db.getEventsInGroup(groupId)])
    for group in range(len(groupsIds)):
        events = eventsByGroup[group]
        for event in events:
            eventName = event[1]
            link = event[2]
            date = event[3] #DD.MM.YY;HH:MM
            startAt = f'{date[9:11]}:{date[12:14]}'
            aioschedule.every().day.at(startAt).do(broadcaster, link=link, eventDate=date, eventName=eventName, groupId=groupsIds[group])
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)
async def on_startup(_) -> None:
    asyncio.create_task(scheduler())

if __name__ == '__main__':
    logging.info('Запуск бота')
    db = BotDB(os.getenv("DATABASE_FILE_PATH"))
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
    db.close()
    logging.info('Завершение работы бота')