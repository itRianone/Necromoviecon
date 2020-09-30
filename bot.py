import logging
import sqlite3
import random
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from configuration.sqliteTry import db, cursor
from configuration.states import MyStates
from configuration.settings import token

logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=token)
dp = Dispatcher(bot, storage=MemoryStorage())

#add to db func
@dp.message_handler(commands=["add"], state=None)
async def add_to_db(message: types.Message):
    await bot.send_message(message.chat.id, "Напиши имя произведения, которое ты хочешь добавить в бд")

    await MyStates.add_name.set()

#add name of object
@dp.message_handler(state=MyStates.add_name)  
async def add_movie_name(message: types.message, state: FSMContext):
    m_name = message.text.upper()
    cursor.execute(
        "SELECT name FROM movies WHERE name = (?)", ([m_name.strip()]))

    if m_name.startswith("/"):
        await state.finish()
        await bot.send_message(message.chat.id, "Ты ввел знак вызова команды (/), работа FSM приостановлена")
    elif cursor.fetchone() is None:
        await state.update_data(answer1=m_name)

        await bot.send_message(
            message.chat.id, f"Отправь мне вид произведения, к которому принадлежит {m_name} (Фильм, сериал и тд)")

        await MyStates.next()
    else:
        await bot.send_message(message.chat.id, "Произведение " + m_name + " уже есть в базе данных")
        await state.finish()

#add type of object
@dp.message_handler(state=MyStates.add_type)  
async def add_movie_type(message: types.message, state: FSMContext):
    data = await state.get_data()
    m_name = data.get("answer1")
    
    m_type = message.text.upper()

    cursor.execute("INSERT INTO movies VALUES (?, ?)", (m_name.strip(), m_type.strip()))
    db.commit()    
    
    await bot.send_message(message.chat.id, f"{m_name, m_type} добавлено в бд")
    await state.finish()

#remove from db func, FSM
@dp.message_handler(commands=["remove"])
async def delete_from_db(message: types.Message):
    await bot.send_message(
        message.chat.id, "Отправь название произведения, и, если оно есть в бд, я его удалю")
        
    await MyStates.remove.set()

#object which will be romoved
@dp.message_handler(state=MyStates.remove)
async def delete_from_db(message: types.Message, state: FSMContext):
    arg = message.text.upper()

    cursor.execute("SELECT name FROM movies WHERE name = (?)", [(arg.strip())])

    if arg.startswith("/"):
        await state.finish()
        await bot.send_message(message.chat.id, "Ты ввел знак вызова команды (/), работа FSM приостановлена")
    elif cursor.fetchone():
        cursor.execute("DELETE FROM movies WHERE name = (?)", [(arg.strip())])
        db.commit()

        await bot.send_message(message.chat.id, f"'{arg.strip()}' удалено из бд")
    else:
        await bot.send_message(message.chat.id, "Не могу удалить того, чего нет в бд")
    await state.finish()

#edit in db func, FSM
@dp.message_handler(commands=["edit"], state=None)
async def edit_in_db(message: types.Message):
    await message.answer("Какое из произведений в бд редактировать?")

    await MyStates.edit_from.set()

#object which will be edited
@dp.message_handler(state=MyStates.edit_from)
async def edit_from(message: types.Message, state: FSMContext):  
    post_passed = message.text.upper()

    cursor.execute("SELECT name FROM movies WHERE name = (?)", ([post_passed.strip()]))
    if cursor.fetchone():
        await state.update_data(answer1=post_passed)
        await bot.send_message(message.chat.id, post_passed + " будет редактировано на:")

        await MyStates.next()
    else:
        await bot.send_message(message.chat.id, "Не могу редачить то, чего нет в базе")
        await state.finish()

#object which will be edit for
@dp.message_handler(state=MyStates.edit_to)
async def edit_from(message: types.Message, state: FSMContext):
    post_took = message.text.upper()

    data = await state.get_data()   
    post_passed = data.get("answer1")
    await bot.send_message(
        message.chat.id, f"Хорошо, {post_passed} был(а) отредактировано на {post_took}")


    cursor.execute("UPDATE movies SET name = (?) WHERE name = (?)", (post_took.strip(), post_passed.strip()))
    db.commit()
    await state.finish()

#watch all in db func
@dp.message_handler(commands=["all"])
async def db_work(message: types.Message):
    all_m = []
    for m in cursor.execute("SELECT * FROM movies"):

        all_m.append(m)

    all_m = '\n'.join([', '.join(map(str, m)) for m in all_m])
    
    await bot.send_message(
        message.chat.id, "Все произведения, которые ты хотел посмотреть:" + f"\n{all_m}")

#welcome func
@dp.message_handler(commands=["start", "s", "ы"])
async def send_welcome(message: types.Message):
    await message.reply("Hi, {}!\nI'm Necromoviecon!\nТвой личный дневник, бот, раб, кролик, стул, стол и все, что тебе нужно."
        " Умею добавлять/изменять/удалять инфу о заинтересовавших тебя(меня) произведениях в бд."
        " Напиши команду /help,"
        " чтобы я показал тебе все мои команды и что они делают".format(
            message.from_user.first_name))

    hi_id = "CAACAgQAAxkBAAOjXzlEMdclmrIEiRsaw51Ookp4ftQAAj4BAAKoISEGsnLxgT5isgwaBA"
    await message.answer_sticker(r"{}".format(hi_id))

#сука помогите func
@dp.message_handler(commands=["help"])
async def send_welcome(message: types.Message):
    await message.reply(
        "{}, вот список команд:"
        "\nСтартовые команды - /start, /s"
        "\nКоманда help, на которую ты кликнул - /help"
        "\nКоманды для добавления/удаления/изменения произведений из базы данных:"
        "\n/add, /remove, /edit"
        "\nРабота добавления использует FSM, если ты отправишь (/) во время вопросов, то FSM остановится"
        "\nА еще можешь чекнуть всю базу - /all"
        "\nИ сыграть в рулеточку) - /rullete, /рулетка".format(message.from_user.first_name))

#for sticks 
@dp.message_handler(content_types=types.ContentType.STICKER)
async def stick_id(message: types.Message):
    #Включай если надо узнать id стикера, фото и тд
    await message.reply("{}".format(message.sticker.file_id))

#russian rullete(why not?)
def rullete(random):
    global god_change
    god_change = random.randint(1, 2)
    global other_var_life
    other_var_life = random.randint(2, 3)
    global other_var_death
    other_var_death = random.randint(4, 5)

# ↑
@dp.message_handler(commands=["rullete","рулетка"])
async def rus_rullete(message: types.Message):
    #russian rullete(why not?)
    rullete(random)

    if god_change == 1:
        await bot.send_message(message.chat.id, f"{message.from_user.first_name}, ты выжил, гц")
        life = "CAACAgIAAxkBAAII5l9P67aFBqrmeND0V5ZHGidV3iT6AAJTAQACe04qEB9UH_TkgUMJGwQ"
        if other_var_life == 2:
            await message.answer_sticker(r"{}".format(life))
        if other_var_life == 3:
            await message.answer_sticker(r"{}".format(life))
    if god_change == 2:
        await bot.send_message(message.chat.id, f"{message.from_user.first_name}, ты не выжил, f")
        death = "CAACAgIAAxkBAAIJB19P7QTk6-4usNsg5mLYIj8elJEbAAJjAQACe04qEFNWbvXKCmwLGwQ"
        if other_var_death == 4:
            await message.answer_sticker(r"{}".format(death))
        if other_var_death == 5:
            await message.answer_sticker(r"{}".format(death))
            
#classic
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
    db.commit()
