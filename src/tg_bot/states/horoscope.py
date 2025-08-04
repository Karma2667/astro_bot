from aiogram.fsm.state import StatesGroup, State

class DateState(StatesGroup):
    date = State()

class CompatibilitySignsState(StatesGroup):
    waiting_for_first_sign = State()
    waiting_for_second_sign = State()