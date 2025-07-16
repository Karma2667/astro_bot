from aiogram.fsm.state import StatesGroup, State

class RegistrationStates(StatesGroup):
    title = State()
    birth_date = State()
    birth_time = State()
    birth_location = State()
    current_location = State()