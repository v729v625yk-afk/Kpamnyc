from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

import random

from data.resources import RESOURCES
from data.talismans import TALISMANS

from utils.cooldowns import check_cooldown

router = Router()

@router.message(Command("mine"))
async def mine_command(message: Message):

    user_id = message.from_user.id

    if not check_cooldown(user_id):

        await message.answer("⏳ Подождите 5 секунд.")
        return

    resource = random.choice(RESOURCES)

    amount = random.randint(1, 50)

    xp = random.randint(5, 25)

    text = f"""
⛏️ Вы добыли:

{resource} x{amount}

✨ +{xp} XP
"""

    found_talisman = None

    for talisman in TALISMANS.values():

        if random.randint(1, talisman["chance"]) == 1:

            found_talisman = talisman

            break

    if found_talisman:

        text += f"""

🍀 Вы нашли талисман!

{found_talisman["name"]}

⚡ Эффект:
{found_talisman["bonus"]}
"""

    await message.answer(text)
