from sqlalchemy import String, BigInteger, Enum as SAEnum, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from enum import Enum
from datetime import datetime, timedelta, timezone

from database.base import Base


class PredictionType(Enum):
    HOROSCOPE = "horoscope"
    EVENT = "event"
    COMPATIBILITY = "compatibility"
    ZODIAC_COMPATIBILITY = "zodiac_compatibility"
    ANGEL_NUMBERS = "angel_numbers"


class Prediction(Base):
    __tablename__ = "Prediction"

    id: Mapped[BigInteger] = mapped_column(
        BigInteger,
        unique=True,
        index=True,
        nullable=False,
        primary_key=True,
        autoincrement=True,
    )

    profile_id: Mapped[BigInteger] = mapped_column(BigInteger, nullable=False)

    prediction: Mapped[str] = mapped_column(String, nullable=False)

    prediction_type: Mapped[PredictionType] = mapped_column(
        SAEnum(PredictionType), nullable=False
    )

    recognition_str: Mapped[str] = mapped_column(
        String,
        nullable=True, 
    )

    expiration_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True, 
        default=lambda: datetime.now(timezone.utc) + timedelta(days=90)
    )

    def __doc__(self):
        return f"{__class__.__name__}({self.id})"

    def __str__(self):
        return f"({self.id})"

