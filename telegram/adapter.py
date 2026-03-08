from aiogram.types import Message
from controller.router import Router, Value


class TelegramAdapter:
    def __init__(self, router: Router) -> None:
        self.router = router

    async def handle_message(self, message: Message):
        value = Value(
            user_id=message.from_user.id,
            text=message.text,
        )

        response = self.router.process(value)

        if response.keyboard:
            from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text=btn)] for btn in response.keyboard
                ],
                resize_keyboard=True,
            )

            await message.answer(
                response.text, parse_mode="HTML", reply_markup=keyboard
            )
        else:
            from aiogram.types import ReplyKeyboardRemove

            keyboard = ReplyKeyboardRemove()
            await message.answer(
                response.text, parse_mode="HTML", reply_markup=keyboard
            )
