from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc
from db.models import User, Operation
from typing import Sequence


class OperationService:
    @staticmethod
    def get_or_create_user(session: Session, user_id: int) -> User:
        stmt = select(User).where(User.user_id == user_id)
        user = session.execute(stmt).scalar_one_or_none()

        if not user:
            user = User(user_id=user_id)
            session.add(user)
            session.commit()
            session.refresh(user)

        return user

    @staticmethod
    def add_operation(session: Session, user_id: int):
        user = OperationService.get_or_create_user(session, user_id)

        operation = Operation(
            user_id=user.user_id,
            amount=user.temp_amount,
            category=user.temp_category,
            description=user.temp_description,
        )

        session.add(operation)
        session.commit()

    @staticmethod
    def get_balance(session: Session, user_id: int) -> int:
        stmt = select(func.sum(Operation.amount)).where(
            Operation.user_id == user_id
        )
        result = session.execute(stmt).scalar()

        return result or 0

    @staticmethod
    def get_budget_by_key(session: Session, user_id: int, key: str) -> int:
        user = OperationService.get_or_create_user(session, user_id)

        budgets = {
            "needs": user.budget_needs,
            "dopamine": user.budget_dopamine,
            "save": user.budget_save,
        }

        return budgets.get(key, 0)

    @staticmethod
    def get_operations(
        session: Session, user_id: int, limit: int = 20
    ) -> Sequence[Operation]:
        stmt = (
            select(Operation)
            .where(Operation.user_id == user_id)
            .order_by(Operation.timestamp)
            .limit(limit)
        )

        return session.execute(stmt).scalars().all()

    @staticmethod
    def get_top_expense_description(
        session: Session, user_id: int, is_expense: bool, limit: int = 5
    ) -> list[str]:

        condition = (
            Operation.amount > 0 if is_expense else Operation.amount < 0
        )

        stmt = (
            select(
                Operation.description,
                func.count(Operation.user_id).label("cnt"),
            )
            .where(
                Operation.user_id == user_id,
                condition,
                Operation.description.is_not(None),
                Operation.description != "",
            )
            .group_by(Operation.description)
            .order_by(desc("cnt"))
            .limit(limit)
        )

        result = session.execute(stmt).all()
        return [row[0] for row in result] if result else []

    @staticmethod
    def get_state(session: Session, user_id: int) -> str | None:
        return session.scalar(
            select(User.state).where(User.user_id == user_id)
        )

    @staticmethod
    def set_state(session: Session, user_id: int, state: str = "idle"):
        user = OperationService.get_or_create_user(session, user_id)
        user.state = state

    @staticmethod
    def set_temp_amount(session: Session, user_id: int, amount: float):
        user = OperationService.get_or_create_user(session, user_id)
        user.temp_amount = int(amount * 100)

    @staticmethod
    def set_temp_category(session: Session, user_id: int, category: str):
        user = OperationService.get_or_create_user(session, user_id)
        user.temp_category = category

    @staticmethod
    def set_temp_description(session: Session, user_id: int, description: str):
        user = OperationService.get_or_create_user(session, user_id)
        user.temp_description = description


from db.database import SessionLocal

session = SessionLocal()

telegram_id = 12345

OperationService.add_operation(session, telegram_id)
OperationService.add_operation(session, telegram_id)

balance = OperationService.get_balance(session, telegram_id)

print("Balance:", balance)
