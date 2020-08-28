from aiogram.dispatcher.filters.state import StatesGroup, State


class MyStates(StatesGroup):
    add_name = State()
    add_type = State()
    edit_from = State()
    edit_to = State()
    remove = State()

