import logging
import sqlite3
from config import token
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from my_db.sqliteTry import db, cursor
from states import MyStates

logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=token)
dp = Dispatcher(bot, storage=MemoryStorage())

#add to db func
@dp.message_handler(commands=["add"])
async def add_to_db(message: types.Message):
    arg = message.get_args().upper()

    cursor.execute(
        f"SELECT name FROM movies WHERE name = '{arg.strip()}'")

    if arg and cursor.fetchone() is None:
        cursor.execute(f"INSERT INTO movies VALUES (?)", [arg.strip()])
                                                                
        db.commit()
        await bot.send_message(message.chat.id, "Произведение " + arg + " было добавлено в базу данных")

    elif not arg:
        await bot.send_message(message.chat.id, "Hельзя добавить воздух")  
    else:
        await bot.send_message(message.chat.id, "Произведение " + arg + " уже есть в базе данных")

#remove from db func
@dp.message_handler(commands=["remove"])
async def delete_from_db(message: types.Message):
    arg = message.get_args().upper()

    cursor.execute(f"SELECT name FROM movies WHERE name = '{arg.strip()}'")

    if arg and cursor.fetchone():
        remo = (f"DELETE FROM movies WHERE name = '{arg.strip()}'")
        cursor.execute(remo)
        db.commit()

        await bot.send_message(message.chat.id, f"'{arg.strip()}' удалено из бд yeye")

    elif not arg:
        await bot.send_message(message.chat.id, "Нельзя удалить пустоту, сука говорил же")
    else:
        await bot.send_message(message.chat.id, "Не могу удалить того, чего нет в бд")

#edit in db func, FSM
@dp.message_handler(commands=["edit"], state=None)
async def edit_in_db(message: types.Message):
    await message.answer("Какое из произведений в бд редактировать?")

    await MyStates.Q1.set()


@dp.message_handler(state=MyStates.Q1)
async def edit_from(message: types.Message, state: FSMContext):  
    post_passed = message.text.upper()

    cursor.execute(f"SELECT name FROM movies WHERE name = '{post_passed.strip()}'")
    if cursor.fetchone():
        await state.update_data(answer1=post_passed)
        await bot.send_message(message.chat.id, post_passed + " будет редактировано на:")

        await MyStates.next()
    else:
        await bot.send_message(message.chat.id, post_passed + "Не могу редачить то, чего нет в базе")
        await state.finish()


@dp.message_handler(state=MyStates.Q2)
async def edit_from(message: types.Message, state: FSMContext):
    post_took = message.text.upper()

    data = await state.get_data()   
    post_passed = data.get("answer1")
    await bot.send_message(message.chat.id, f"Хорошо, {post_passed} был(а) отредактировано на {post_took}")

    edit = f"""
        UPDATE movies 
        SET name = '{post_took.strip()}' 
        WHERE name = '{post_passed.strip()}'
    """

    cursor.execute(edit)
    db.commit()
    await state.finish()

#watch all in db func
@dp.message_handler(commands=["all"])
async def db_work(message: types.Message):
    all_m = []
    for m in cursor.execute("SELECT * FROM movies"):
        all_m.append(m)

    await bot.send_message(message.chat.id,"Все произведения, которые ты хотел посмотреть:" + f"\n{all_m}")

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
        "\nКоманды для добавления/удаления/изменения произведений из базы данных, "
        "где ты пишешь сначала команду, а потом аргумент, например - "
        "/add Твоё Произведение"
        "\nТакже работает с удалением произведения - /remove Твоё Произведение"
        "\nНемного по-другому с изменением произведения - пишешь /edit, следующим сообщением то произведение, какое ты хочешь заменить,"
        " след. сообщением то, на которое меняешь"
        "\nА еще можешь чекнуть всю базу - /all".format(message.from_user.first_name))

#for sticks 
@dp.message_handler(content_types=types.ContentType.STICKER)
async def stick_id(message: types.Message):
    #await message.answer_sticker(r"{}".format(message.sticker.file_id))
    #Включай если надо узнать id стикера, фото и тд
    await message.reply("{}".format(message.sticker.file_id))

#classic
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
    db.commit()
