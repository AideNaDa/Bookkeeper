from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc
from db.models import User, Operation
from sqlalchemy.exc import SQLAlchemyError
from core.states import States


class OperationService:
    @staticmethod
    def get_or_create_user(session: Session, user_id: int) -> User:
        stmt = select(User).where(User.user_id == user_id)
        user = session.execute(stmt).scalar_one_or_none()

        if not user:
            user = User(user_id=user_id)
            session.add(user)
            session.flush()

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

        return (result or 0) / 100

    @staticmethod
    def get_budget_by_key(session: Session, user_id: int, key: str) -> float:
        user = OperationService.get_or_create_user(session, user_id)
        value = getattr(user, f"budget_{key}", 0)
        return value / 100

    @staticmethod
    def get_all_balance_info(session: Session, user_id: int) -> str:
        user = OperationService.get_or_create_user(session, user_id)
        balance = OperationService.get_balance(session, user_id)

        budgets = {
            "Needs": user.budget_needs / 100,
            "Dopamine": user.budget_dopamine / 100,
            "Save": user.budget_save / 100,
            "Indefinite": user.budget_indefinite / 100,
        }

        lines = [f"{k:<13}{v:>10.2f} " for k, v in budgets.items()]

        text = (
            "<pre>"
            f"Total balance{balance:>10.2f} \n"
            "-----------------------\n" + "\n".join(lines) + "</pre>\n⠀"
        )

        return text

    @staticmethod
    def get_operations(session: Session, user_id: int, limit: int = 15) -> str:
        stmt = (
            select(Operation)
            .where(Operation.user_id == user_id)
            .order_by(desc(Operation.timestamp))
            .limit(limit)
        )

        result = session.execute(stmt).scalars().all()

        if not result:
            return "<i>No transactions yet</i>"

        lines = []
        count = 1
        for row in result:
            amount = row.amount / 100
            sign = "🟩+" if amount > 0 else "🟥-"

            lines.append(
                f"<pre>- - - - - - - - - - {count} - - - - - - - - - -\n{sign}${abs(amount)}\n{row.category}\n({row.description})\n{row.timestamp.strftime("%Y.%m.%d %H:%M:%S")}\n</pre>"
            )
            count += 1
        count = 1
        lines.reverse()
        return "\n".join(lines) + "\n⠀"

    @staticmethod
    def get_top_expense_description(
        session: Session, user_id: int, is_income: bool = False, limit: int = 5
    ) -> list[str]:

        condition = Operation.amount > 0 if is_income else Operation.amount < 0

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
    def set_state(
        session: Session, user_id: int, state: str = States.IDLE.name
    ):
        user = OperationService.get_or_create_user(session, user_id)
        user.state = state

    @staticmethod
    def set_temp_amount(session: Session, user_id: int, amount: float = 0):
        user = OperationService.get_or_create_user(session, user_id)
        user.temp_amount = int(amount * 100)

    @staticmethod
    def set_temp_category(session: Session, user_id: int, category: str = ""):
        user = OperationService.get_or_create_user(session, user_id)
        user.temp_category = category

    @staticmethod
    def set_temp_description(
        session: Session, user_id: int, description: str = ""
    ):
        user = OperationService.get_or_create_user(session, user_id)
        user.temp_description = description

    @staticmethod
    def save(session: Session, user: User | None = None):
        try:
            if user:
                session.add(user)
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise
