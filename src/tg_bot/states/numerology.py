from aiogram.fsm.state import State, StatesGroup # type: ignore

class AngelNumbersStates(StatesGroup):
    waiting_for_numbers = State() 
    waiting_for_birthdate = State()