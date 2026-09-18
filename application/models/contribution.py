import enum

from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, NUMERIC, String, BOOLEAN
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from marshmallow import Schema, fields

from . import ModelBase

from dataclasses import dataclass


# Used to avoid circular imports for FK relationship
if TYPE_CHECKING:
    from .user import User

class ContributionType(enum.Enum):
    RETIREMENT = "retirement"
    INVESTMENT = "investment"
    SAVINGS = "savings"
    PERSONAL_GOAL = "personal goal"
    OTHER = "other"

class Contribution(ModelBase):
    __tablename__ = "contribution"

    id: Mapped[int] = mapped_column(primary_key=True)
    frequency: Mapped[float] = mapped_column(NUMERIC())     # Frequency of occurrence relative to a month. For example, quarterly is 1/3 the total monthly cost, applied every month (frequency = '1/3')
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String(511))
    amount: Mapped[float] = mapped_column(NUMERIC())
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    type: Mapped[ContributionType] = mapped_column(nullable=False)
    monthly_cost: Mapped[float] = column_property(amount * frequency)


    def __repr__(self) -> str:
        return f"Contribution(id={self.id}, user={self.user_id}, name={self.name}, amount={self.amount}, frequency={self.frequency})"
    

# Pydantic dataclasses for endpoint parameters
@dataclass
class ContributionCreate():
    frequency: float
    name: str
    description: str
    amount: float
    user_id: int
    type: ContributionType


@dataclass
class ContributionUpdate():
    frequency: float
    name: str
    description: str
    amount: float
    type: ContributionType



# Marshmallow Schema for serialization/deserialization
class ContributionSchema(Schema):
    frequency = fields.Float()
    name = fields.Str()
    description = fields.Str()
    amount = fields.Float()
    user_id = fields.Int()
    type = fields.Enum(ContributionType)
    monthly_cost = fields.Float()