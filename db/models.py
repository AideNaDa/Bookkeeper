from datetime import datetime
from sqlalchemy import BigInteger, String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


class User(Base):
    __tablename__ = "users"

    base_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)

    state: Mapped[str] = mapped_column(String, default="idle")

    temp_amount: Mapped[int] = mapped_column(BigInteger, default=0)
    temp_category: Mapped[str] = mapped_column(String(50), default="")
    temp_description: Mapped[str] = mapped_column(String(255), default="")

    budget_needs: Mapped[int] = mapped_column(BigInteger, default=0)
    budget_dopamine: Mapped[int] = mapped_column(BigInteger, default=0)
    budget_save: Mapped[int] = mapped_column(BigInteger, default=0)

    operations: Mapped[list["Operation"]] = relationship(
        "Operation", back_populates="user", cascade="all, delete-orphan"
    )


class Operation(Base):
    __tablename__ = "operations"

    base_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.user_id")
    )

    amount: Mapped[int] = mapped_column(BigInteger, default=0)
    category: Mapped[str] = mapped_column(String(50), default="")
    description: Mapped[str] = mapped_column(String(255), default="")

    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    user: Mapped["User"] = relationship("User", back_populates="operations")
