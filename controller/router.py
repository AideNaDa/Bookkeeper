from db.models import User, Operation
from core.states import States
from core.response import Response
from dataclasses import dataclass
from services.operation import OperationService
from db.database import SessionLocal


MAIN_MENU_BTN = ["Balance", "History", "Settings"]


@dataclass
class Value:
    user_id: int
    text: str | None = None


class Router:
    def __init__(self):
        self.session = SessionLocal()

    @staticmethod
    def clear_temp(user: User):
        user.temp_amount = 0
        user.temp_category = ""
        user.temp_description = ""

    @staticmethod
    def main_menu_btn():
        from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

        btns = ["Balance", "History", "Settings"]
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=btn)] for btn in btns],
            resize_keyboard=True,
        )
        return keyboard

    def process(self, value: Value) -> Response:
        user = OperationService.get_or_create_user(self.session, value.user_id)

        if not user:
            return Response(text="User not found", new_state=States.IDLE)

        if not value.text:
            return Response(
                text="Please, enter any command", new_state=States.IDLE
            )

        try:
            current_state = States[user.state]
        except Exception:
            current_state = States.IDLE

        match current_state:
            case States.IDLE:
                response = self._handle_idle(user, value.text)
            case States.WAITING_TOPUP_DESCRIPTION:
                pass
                # response = self._handle_topup_description(user, value.text)
            case States.WAITING_TOPUP_CATEGORY:
                response = self._handle_waiting_topup_category(
                    user, value.text
                )
            case States.WAITING_EXPENSE_DESCRIPTION:
                response = self._handle_waiting_expense_description(
                    user, value.text
                )
            case States.WAITING_EXPENSE_CATEGORY:
                response = self._handle_waiting_expense_category(
                    user, value.text
                )
            case States.SETTINGS:
                response = self._handle_settings(user, value.text)
            case _:
                response = Response(
                    text="Unknown state", new_state=States.IDLE
                )

        if response.new_state:
            user.state = response.new_state.name

        OperationService.save(self.session, user)
        return response

    def _handle_idle(self, user: User, text: str) -> Response:
        if not text:
            return Response(text="Enter a number")

        match text:
            case "Balance":
                return Response(
                    text=OperationService.get_all_balance_info(
                        self.session, user.user_id
                    ),
                    keyboard=MAIN_MENU_BTN,
                )
            case "History":
                return Response(
                    text=OperationService.get_operations(
                        self.session, user.user_id
                    ),
                    keyboard=MAIN_MENU_BTN,
                )

        try:
            OperationService.set_temp_amount(
                self.session, user.user_id, float(text.replace(",", ".", 1))
            )
            if user.temp_amount > 0:
                return Response(
                    text="Select a top-up category",
                    keyboard=[
                        "Needs",
                        "Dopamine",
                        "Save",
                        "Standard split",
                        "Custom split",
                        "Cancel",
                    ],
                    new_state=States.WAITING_TOPUP_CATEGORY,
                )
            elif user.temp_amount < 0:
                keyboard = OperationService.get_top_expense_description(
                    self.session, user.user_id
                )
                keyboard.append("Cancel")
                return Response(
                    text="Choose from popular options or enter a description",
                    keyboard=keyboard,
                    new_state=States.WAITING_EXPENSE_DESCRIPTION,
                )
        except ValueError:
            return Response(
                text="Please enter a valid number or choose a command."
            )
        except Exception as e:
            print(f"System Error: {e}")
            return Response(text="Something went wrong on our side.")

        return Response(text="Enter a number. Format: 1, -1, 1.11")

    def _handle_waiting_topup_category(
        self, user: User, text: str
    ) -> Response:
        user.temp_description = "Top-up"
        user.temp_category = text
        match text:
            case "Needs":
                user.budget_needs += user.temp_amount

            case "Dopamine":
                user.budget_dopamine += user.temp_amount

            case "Save":
                user.budget_save += user.temp_amount

            case "Standard split":
                sum = 0

                part = int(user.temp_amount * 0.5)
                user.budget_needs += part
                sum += part
                part = int(user.temp_amount * 0.3)
                user.budget_dopamine += part
                sum += part
                last_part = user.temp_amount - sum
                user.budget_save += last_part
                user.temp_category = "Split (50/30/20)"

            case "Custom split":
                pass

            case "Cancel":
                self.clear_temp(user)
                return Response(
                    text="Start menu",
                    keyboard=MAIN_MENU_BTN,
                    new_state=States.IDLE,
                )

            case _:
                return Response(
                    text="Please, select a category",
                )

        OperationService.add_operation(self.session, user.user_id)
        self.clear_temp(user)

        return Response(
            text=f"Success\n\n\n{OperationService.get_all_balance_info(self.session, user.user_id)}",
            keyboard=MAIN_MENU_BTN,
            new_state=States.IDLE,
        )

    def _handle_waiting_expense_description(
        self, user: User, text: str
    ) -> Response:
        OperationService.set_temp_description(self.session, user.user_id, text)
        return Response(
            text="Select a category",
            keyboard=[
                "Needs",
                "Dopamine",
                "indefinite",
                "Cancel",
            ],
            new_state=States.WAITING_EXPENSE_CATEGORY,
        )

    def _handle_waiting_expense_category(
        self, user: User, text: str
    ) -> Response:
        user.temp_category = text
        match text:
            case "Needs":
                user.budget_needs -= abs(user.temp_amount)
            case "Dopamine":
                user.budget_dopamine -= abs(user.temp_amount)
            case "Save":
                user.budget_save -= abs(user.temp_amount)
            case "indefinite":
                user.budget_indefinite -= abs(user.temp_amount)
            case "Cancel":
                self.clear_temp(user)
                return Response(
                    text="Start menu",
                    keyboard=MAIN_MENU_BTN,
                    new_state=States.IDLE,
                )
            case _:
                return Response(
                    text="Please, select a category",
                )

        OperationService.add_operation(self.session, user.user_id)
        self.clear_temp(user)

        return Response(
            text=f"Success\n\n\n{OperationService.get_all_balance_info(self.session, user.user_id)}",
            keyboard=MAIN_MENU_BTN,
            new_state=States.IDLE,
        )

    def _handle_settings(self, user, text):
        pass
