from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()

@router.message(Command("start"))
async def start_command(message: Message):

    text = """
✨ Добро пожаловать в KpamnycBot!

👤 Создатель бота: zexon02

Здесь тебя ждёт:
⛏️ Добыча ресурсов
🎴 Талисманы
👹 Боссы
🎰 Казино
🛒 Рынок
🌌 Редкие предметы

📌 Чтобы начать игру, используй:
/mine

❓ Для списка всех команд:
/help
"""

    await message.answer(text)
