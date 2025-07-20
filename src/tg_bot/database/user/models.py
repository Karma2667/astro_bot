from sqlalchemy import (
    Enum as SAEnum,
    DateTime,
    BigInteger,
    String,
    Boolean
)
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from typing import Optional
from enum import Enum

from database.base import Base

class Subscription(Enum):
    FOREVER = 'forever'
    MONTHLY = 'monthly'
    FREELY = 'freely'

class User(Base):
    __tablename__ = 'users'  # Исправлено на нижний регистр для конвенции PostgreSQL

    id: Mapped[BigInteger] = mapped_column(
        BigInteger, unique=True, index=True, nullable=False, primary_key=True, autoincrement=True
    )

    user_id: Mapped[Optional[BigInteger]] = mapped_column(
        BigInteger, unique=True, nullable=True
    )

    name: Mapped[str] = mapped_column(
        String, nullable=False
    )

    locale: Mapped[str] = mapped_column(
        String, nullable=False
    )

    current_profile_id: Mapped[Optional[BigInteger]] = mapped_column(
        BigInteger, nullable=True  # Убрал unique, если не требуется
    )

    subscription: Mapped[Subscription] = mapped_column(
        SAEnum(Subscription), nullable=False, default=Subscription.FREELY
    )

    subscription_expiration_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, default=None
    )

    is_mail_subscribed: Mapped[bool] = mapped_column(
        nullable=False, default=True
    )

    is_admin: Mapped[bool] = mapped_column(  # Добавлено поле is_admin
        Boolean, nullable=False, default=False
    )

    def __repr__(self):
        """String representation of User for debugging."""
        return f"User(user_id={self.user_id}, name={self.name}, is_admin={self.is_admin})"

    __str__ = __repr__  # Используем __repr__ как __str__