from dataclasses import dataclass

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import ModelBase


# Used to avoid circular imports for FK relationship
if TYPE_CHECKING:
    from .income import Income


class User(ModelBase):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(50))
    hashed_password: Mapped[str] = mapped_column(String(255))

    # Map foreign key relationships so are accessible from user object
    income: Mapped["Income"] = relationship(back_populates="user", cascade="all, delete-orphan")


    def __repr__(self) -> str:
        return f"User(id={self.id}, email={self.email})"


# Pydantic dataclasses for endpoint parameters
@dataclass
class UserCreate():
    email: str
    unhashed_password: str
    
    