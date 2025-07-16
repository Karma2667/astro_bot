from aiogram.fsm.state import StatesGroup, State

class DateState(StatesGroup):
    date = State()