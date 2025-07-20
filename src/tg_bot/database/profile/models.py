from sqlalchemy import (
    String,
    DateTime,
    Date,
    Time,
    BigInteger,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from datetime import date, time

from database.base import Base

class Profile(Base):
    __tablename__ = 'Profile'

    id: Mapped[BigInteger] = mapped_column(
        BigInteger, unique=True, index=True, nullable=False, primary_key=True, autoincrement=True
    )

    user_id: Mapped[BigInteger] = mapped_column(
        BigInteger, nullable=False
    )

    creation_date: Mapped[DateTime] = mapped_column(
        DateTime, default=func.now()
    )

    title: Mapped[str] = mapped_column(
        String, nullable=False
    )

    birth_date: Mapped[date] = mapped_column(
        Date, nullable=False
    )

    birth_time: Mapped[time] = mapped_column(
        Time, default=time(0, 0)
    )

    birth_location_name: Mapped[str] = mapped_column(
        String, nullable=True
    )

    zodiac_sign: Mapped[str] = mapped_column(
        String, nullable=True
    )

    def __repr__(self):
        return f'Profile(id={self.id}, user_id={self.user_id}, zodiac_sign={self.zodiac_sign})'

    def __str__(self):
        return f'Profile({self.id})'