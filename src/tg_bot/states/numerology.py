from aiogram.fsm.state import State, StatesGroup # type: ignore

class AngelNumbersStates(StatesGroup):
    waiting_for_numbers = State() 
    waiting_for_birthdate = State()
    
class NumerologyMatrixStates(StatesGroup):
    """Состояния для расчета Матрицы Судьбы."""
    waiting_for_birth_date = State() # Ожидание даты рождения