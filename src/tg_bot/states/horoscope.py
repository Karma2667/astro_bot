from aiogram.fsm.state import StatesGroup, State # type: ignore

class DateState(StatesGroup):
    date = State()

class CompatibilitySignsState(StatesGroup):
    waiting_for_first_sign = State()
    waiting_for_second_sign = State()