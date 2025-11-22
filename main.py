import asyncio
import logging
import sys
from os import getenv

from aiogram import Bot, html, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message

from config import BOT_TOKEN
from handlers import create_user, leave_management


async def main():
    dp = Dispatcher()
    bot = Bot(token=BOT_TOKEN)
    dp.include_router(create_user.router)
    dp.include_router(leave_management.router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
                        stream=sys.stdout)
    asyncio.run(main())
