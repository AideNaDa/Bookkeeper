import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import CommandStart

from services.operation import OperationService
from telegram.adapter import TelegramAdapter
from controller.router import Router, Value
from core.states import States

from db.database import SessionLocal


async def main():
    bot = Bot(token="")
    dp = Dispatcher()

    @dp.message(CommandStart())
    async def start_handle(message: Message):

        with SessionLocal() as session:
            keyboard = Router.main_menu_btn()

            user = OperationService.get_or_create_user(
                session, message.from_user.id
            )

            user.state = States.IDLE.name
            session.commit()

        await message.answer("Welcome. Enter a number.", reply_markup=keyboard)

    @dp.message()
    async def message_handle(message: Message):
        await TelegramAdapter(Router()).handle_message(message)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
