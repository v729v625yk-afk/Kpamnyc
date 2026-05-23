import asyncio

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN

from handlers.start import router as start_router
from handlers.mine import router as mine_router
from handlers.profile import router as profile_router
from handlers.inventory import router as inventory_router

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.include_router(start_router)
dp.include_router(mine_router)
dp.include_router(profile_router)
dp.include_router(inventory_router)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
