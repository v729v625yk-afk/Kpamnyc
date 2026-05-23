import os
import telebot
from telebot import types
import sqlite3
import random
import time
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

# =========================
# CONFIG
# =========================

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# =========================
# DB
# =========================

db = sqlite3.connect("bot.db", check_same_thread=False)
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    coins INTEGER DEFAULT 100,
    messages INTEGER DEFAULT 0,
    mine_level INTEGER DEFAULT 1,
    bank INTEGER DEFAULT 0,
    last_daily REAL DEFAULT 0,
    username TEXT DEFAULT NULL
)
""")

for col in [
    "ALTER TABLE users ADD COLUMN username TEXT",
    "ALTER TABLE users ADD COLUMN coal INTEGER DEFAULT 0",
    "ALTER TABLE users ADD COLUMN iron INTEGER DEFAULT 0",
    "ALTER TABLE users ADD COLUMN gold INTEGER DEFAULT 0",
    "ALTER TABLE users ADD COLUMN diamond INTEGER DEFAULT 0",
    "ALTER TABLE users ADD COLUMN uranium INTEGER DEFAULT 0",
    "ALTER TABLE users ADD COLUMN hellstone INTEGER DEFAULT 0",
    "ALTER TABLE users ADD COLUMN energy INTEGER DEFAULT 0",
    "ALTER TABLE users ADD COLUMN moon INTEGER DEFAULT 0",
    "ALTER TABLE users ADD COLUMN talisman_until REAL DEFAULT 0",
]:
    try:
        cur.execute(col)
    except Exception:
        pass

db.commit()

# =========================
# MEMORY
# =========================

cooldowns = {
    "xp": {},
    "mine": {},
    "daily": {}
}

MINE_COOLDOWN = 4 * 60 * 60
DAILY_COOLDOWN = 24 * 60 * 60

RARITIES = {
    "COMMON":    "⚪",
    "RARE":      "🔵",
    "EPIC":      "🟣",
    "LEGENDARY": "🟡",
    "MYTHIC":    "🔴"
}

TALISMANS = [
    ("🪬 Затерянный талисман",    "LEGENDARY", "x2 ресурсы 12ч"),
    ("🔥 Адский талисман",        "EPIC",      "x3 шанс редких ресурсов"),
    ("⚡ Энергетический талисман", "RARE",      "+100% XP"),
    ("🌙 Лунный талисман",         "MYTHIC",    "убирает кулдаун шахты"),
    ("☢ Талисман урана",           "EPIC",      "+50% продажа ресурсов"),
    ("💀 Проклятый талисман",      "LEGENDARY", "казино winrate +25%"),
]

BOSSES = [
    ("💀 Скелет шахтёра",   150),
    ("🐉 Пещерный дракон",  400),
    ("👹 Каменный голем",   250),
    ("🕷 Гигантский паук",  180),
    ("☠ Король тьмы",      600),
    ("🦇 Вампир подземелья", 220),
]

ITEMS = [
    ("💎 Кристалл пустоты", "MYTHIC"),
    ("☠ Череп древнего",    "LEGENDARY"),
    ("🔥 Осколок ада",      "EPIC"),
    ("🌌 Космическая пыль", "RARE"),
    ("🗿 Камень шахтёра",   "COMMON"),
]

MINE_RESOURCES = {
    1: ("🪨 Уголь", 5),
    2: ("⛓ Железо", 10),
    3: ("💛 Золото", 20),
    4: ("💎 Алмазы", 35),
    5: ("☢ Уран", 50),
    6: ("🔥 Адский кристалл", 80),
    7: ("⚡ Энергетический осколок", 120),
    8: ("🌙 Лунный камень", 200)
}

# =========================
# HELPERS
# =========================

def clean(text):
    return text.strip().lower() if text else ""

def get_user(uid, message=None):
    user = cur.execute(
        "SELECT * FROM users WHERE user_id=?",
        (uid,)
    ).fetchone()

    if not user:
        name = message.from_user.first_name if message else "Игрок"

        cur.execute("""
        INSERT INTO users (user_id, username)
        VALUES (?, ?)
        """, (uid, name))

        db.commit()

        user = cur.execute(
            "SELECT * FROM users WHERE user_id=?",
            (uid,)
        ).fetchone()

    return user


# =========================
# BUTTONS
# =========================

BUTTONS = {
    "📊 стата",
    "🏆 топ",
    "💬 чат топ",
    "🎰 казино",
    "⛏ шахта",
    "🎁 daily",
    "🏦 банк",
    "⬆ улучшить",
    "🎁 подарок",
    "🎒 инвентарь",
    "👤 профиль",
    "🖼 аватар",
    "💱 продать",
    "📦 кейс"
}

def menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)

    kb.row("👤 профиль", "📊 стата")
    kb.row("🏆 топ", "💬 чат топ")
    kb.row("🎰 казино", "⛏ шахта")
    kb.row("🎁 daily", "🎁 подарок")
    kb.row("🏦 банк", "⬆ улучшить")
    kb.row("🎒 инвентарь", "🖼 аватар")
    kb.row("💱 продать", "📦 кейс")

    return kb


# =========================
# START
# =========================

@bot.message_handler(commands=['start'])
def start(message):
    get_user(message.from_user.id, message)

    bot.send_message(
        message.chat.id,
        "👋 Добро пожаловать в Kpamnyc Bot",
        reply_markup=menu()
    )


# =========================
# ROUTER (ГЛАВНЫЙ ДВИГАТЕЛЬ)
# =========================

@bot.message_handler(func=lambda m: m.text and clean(m.text) in BUTTONS)
def router(message):
    text = clean(message.text)

    if text == "📊 стата":
        stat(message)

    elif text == "🏆 топ":
        top(message)

    elif text == "💬 чат топ":
        chat_top(message)

    elif text == "🎰 казино":
        casino(message)

    elif text == "⛏ шахта":
        mine(message)

    elif text == "🎁 daily":
        daily(message)

    elif text == "🏦 банк":
        bank(message)

    elif text == "⬆ улучшить":
        upgrade(message)

    elif text == "🎁 подарок":
        daily(message)

    elif text == "🎒 инвентарь":
        inventory(message)

    elif text == "👤 профиль":
        profile(message)

    elif text == "🖼 аватар":
        avatar(message)

    elif text == "💱 продать":
        sell(message)

    elif text == "📦 кейс":
        case(message)


# =========================
# НИК
# =========================

@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("ник "))
def change_nick(message):
    uid = message.from_user.id
    new_name = message.text[4:].strip()

    if len(new_name) < 2:
        bot.send_message(message.chat.id, "❌ ник слишком короткий")
        return

    cur.execute("""
        UPDATE users
        SET username=?
        WHERE user_id=?
    """, (new_name, uid))

    db.commit()

    bot.send_message(message.chat.id, f"✅ ник изменён: {new_name}")


# =========================
# XP SYSTEM (НЕ ЛОМАЕТ КНОПКИ)
# =========================

@bot.message_handler(func=lambda m: True)
def xp(message):
    text = clean(message.text)

    if text in BUTTONS or text.startswith("/") or text.startswith("ник "):
        return

    uid = message.from_user.id
    now = time.time()

    if uid in cooldowns["xp"] and now - cooldowns["xp"][uid] < 15:
        return

    xp_gain = random.randint(2, 6)
    coins_gain = random.randint(1, 4)

    user = get_user(uid, message)

    cur.execute("""
        UPDATE users
        SET xp = xp + ?,
            coins = coins + ?,
            messages = messages + 1
        WHERE user_id=?
    """, (xp_gain, coins_gain, uid))

    db.commit()

    user = get_user(uid)

    if user[1] >= user[2] * 120:
        cur.execute("""
            UPDATE users
            SET level = level + 1,
                xp = 0
            WHERE user_id=?
        """, (uid,))
        db.commit()

        bot.send_message(message.chat.id, "🔥 LEVEL UP!")

    cooldowns["xp"][uid] = now


# =========================
# FEATURES
# =========================

def stat(message):
    u = get_user(message.from_user.id)

    name = u[8] if u[8] else "Игрок"

    bot.send_message(message.chat.id, f"""
👤 {name}

📊 СТАТИСТИКА

💰 монеты: {u[3]}
⚡ xp: {u[1]}
📈 уровень: {u[2]}
💬 сообщения: {u[4]}
⛏ шахта lvl: {u[5]}
🏦 банк: {u[6]}

🪨 coal: {u[9]}
🔩 iron: {u[10]}
🥇 gold: {u[11]}
""")


def top(message):
    rows = cur.execute("""
        SELECT username, level, coins
        FROM users
        ORDER BY level DESC
        LIMIT 10
    """).fetchall()

    text = "🏆 ТОП ИГРОКОВ\n\n"

    for i, r in enumerate(rows, 1):
        name = r[0] if r[0] else "Игрок"
        text += f"{i}. {name} | LVL {r[1]} | 💰 {r[2]}\n"

    bot.send_message(message.chat.id, text)


def chat_top(message):
    rows = cur.execute("""
        SELECT user_id, messages, username
        FROM users
        ORDER BY messages DESC
        LIMIT 10
    """).fetchall()

    text = "💬 ТОП ЧАТА\n\n"

    for i, r in enumerate(rows, 1):
        name = f"@{r[2]}" if r[2] else f"ID {r[0]}"
        text += f"{i}. {name} | 💬 {r[1]}\n"

    bot.send_message(message.chat.id, text)


def casino(message):
    u = get_user(message.from_user.id)

    if u[3] < 50:
        bot.send_message(message.chat.id, "❌ мало монет")
        return

    if random.randint(1, 100) > 55:
        win = random.randint(50, 200)

        cur.execute("UPDATE users SET coins = coins + ? WHERE user_id=?",
                    (win, message.from_user.id))
        db.commit()

        bot.send_message(message.chat.id, f"🎰 WIN +{win}")
    else:
        cur.execute("UPDATE users SET coins = coins - 50 WHERE user_id=?",
                    (message.from_user.id,))
        db.commit()

        bot.send_message(message.chat.id, "💀 LOSE -50")


def mine(message):
    uid = message.from_user.id
    u = get_user(uid)

    now = time.time()

    if uid in cooldowns["mine"]:
        if now - cooldowns["mine"][uid] < MINE_COOLDOWN:
            left = int(MINE_COOLDOWN - (now - cooldowns["mine"][uid]))
            h = left // 3600
            m = (left % 3600) // 60

            bot.send_message(message.chat.id, f"⏳ шахта на перезарядке: {h}ч {m}м")
            return

    lvl = min(u[5], 8)
    resource_name, price = MINE_RESOURCES[lvl]

    amount = random.randint(3, 8)

    # двойной дроп от талисмана (u[17] = talisman_until)
    if now < u[17]:
        amount *= 2

    resource_column = {
        1: "coal",
        2: "iron",
        3: "gold",
        4: "diamond",
        5: "uranium",
        6: "hellstone",
        7: "energy",
        8: "moon"
    }[lvl]

    cur.execute(f"""
        UPDATE users
        SET {resource_column} = {resource_column} + ?
        WHERE user_id=?
    """, (amount, uid))

    # редкий талисман (1/1000)
    talisman = ""

    if random.randint(1, 1000) == 777:
        talisman_until = now + 43200  # 12 часов

        cur.execute("""
            UPDATE users
            SET talisman_until=?
            WHERE user_id=?
        """, (talisman_until, uid))

        talisman = "\n\n🪬 ТЫ НАШЁЛ ЗАТЕРЯННЫЙ ТАЛИСМАН!\n🔥 x2 ресурсы на 12 часов"

    # босс-встреча (15% шанс)
    boss_text = ""

    if random.randint(1, 100) <= 15:
        boss = random.choice(BOSSES)
        boss_coins = boss[1]

        cur.execute("""
            UPDATE users
            SET coins = coins + ?
            WHERE user_id=?
        """, (boss_coins, uid))

        boss_text = f"""

👹 БОСС ПОБЕЖДЁН

{boss[0]}

💰 Награда:
+{boss_coins} монет"""

    db.commit()

    cooldowns["mine"][uid] = now

    next_res = MINE_RESOURCES.get(lvl + 1)
    unlock_hint = f"✨ Следующий уровень откроет новые ресурсы" if next_res else "🏆 максимальный уровень!"

    bot.send_message(message.chat.id, f"""
⛏ ДОБЫЧА

{resource_name}: +{amount}

💰 Цена ресурса:
{price} монет за 1 шт.

⬆ Уровень шахты: {u[5]}
{unlock_hint}{talisman}{boss_text}
""")


def daily(message):
    uid = message.from_user.id
    u = get_user(uid)

    now = time.time()

    if uid in cooldowns["daily"]:
        if now - cooldowns["daily"][uid] < DAILY_COOLDOWN:
            left = int(DAILY_COOLDOWN - (now - cooldowns["daily"][uid]))
            h = left // 3600

            bot.send_message(message.chat.id, f"⏳ подарок через {h} часов")
            return

    reward = random.randint(150, 500)

    cur.execute("""
        UPDATE users
        SET coins = coins + ?,
            last_daily = ?
        WHERE user_id=?
    """, (reward, now, uid))

    db.commit()

    cooldowns["daily"][uid] = now

    bot.send_message(
        message.chat.id,
        f"""
🎁 ПОДАРОК ПОЛУЧЕН

💰 +{reward} монет

🔥 заходи каждый день!
"""
    )


def bank(message):
    u = get_user(message.from_user.id)

    bot.send_message(message.chat.id, f"""
🏦 БАНК

💰 на руках: {u[3]}
🏦 в банке: {u[6]}
""")


def avatar(message):
    user = bot.get_user_profile_photos(message.from_user.id)

    if not user.photos:
        bot.send_message(message.chat.id, "❌ нет аватарки")
        return

    file_id = user.photos[0][0].file_id

    bot.send_photo(message.chat.id, file_id)


def profile(message):
    uid = message.from_user.id
    u = get_user(uid)

    FONT      = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

    bg   = Image.new("RGB", (900, 450), (20, 20, 30))
    draw = ImageDraw.Draw(bg)

    font_big   = ImageFont.truetype(FONT_BOLD, 40)
    font_small = ImageFont.truetype(FONT, 28)

    name = u[8] if u[8] else "Игрок"

    draw.text((280, 40),  f"{name}",         fill="white",             font=font_big)
    draw.text((280, 120), f"LVL: {u[2]}",    fill="white",             font=font_small)
    draw.text((280, 170), f"Coins: {u[3]}",  fill=(255, 215, 0),       font=font_small)
    draw.text((280, 220), f"Bank: {u[6]}",   fill=(0, 255, 255),       font=font_small)
    draw.text((280, 270), f"Mine: {u[5]}/8", fill=(255, 165, 0),       font=font_small)

    # XP bar
    max_xp  = max(u[2] * 120, 1)
    percent = min(u[1] / max_xp, 1.0)
    draw.rectangle((280, 350, 750, 390), fill=(60, 60, 60))
    draw.rectangle((280, 350, 280 + int(470 * percent), 390), fill=(0, 255, 120))

    # avatar
    photos = bot.get_user_profile_photos(uid)
    if photos.total_count > 0:
        file_id   = photos.photos[0][0].file_id
        file_info = bot.get_file(file_id)
        url       = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
        response  = requests.get(url)
        avatar    = Image.open(BytesIO(response.content)).convert("RGB").resize((200, 200))
        bg.paste(avatar, (40, 100))

    path = f"profile_{uid}.png"
    bg.save(path)

    with open(path, "rb") as photo:
        bot.send_photo(message.chat.id, photo)

    os.remove(path)


def inventory(message):
    u = get_user(message.from_user.id)

    bot.send_message(message.chat.id, f"""
━━━━━━━━━━━━━━
🎒 ИНВЕНТАРЬ

💰 Монеты: {u[3]}

🪨 Уголь: {u[9]}
⛓ Железо: {u[10]}
💛 Золото: {u[11]}
💎 Алмазы: {u[12]}
☢ Уран: {u[13]}
🔥 Адский кристалл: {u[14]}
⚡ Энергия: {u[15]}
🌙 Лунный камень: {u[16]}

🪬 Талисман:
{"АКТИВЕН" if time.time() < u[17] else "нет"}

━━━━━━━━━━━━━━
""")


def case(message):
    uid = message.from_user.id

    luck = random.randint(1, 1000)

    if luck < 500:
        coins = random.randint(100, 500)

        cur.execute("""
            UPDATE users
            SET coins = coins + ?
            WHERE user_id=?
        """, (coins, uid))

        db.commit()

        bot.send_message(message.chat.id, f"""
📦 КЕЙС ОТКРЫТ

💰 Выпало:
{coins} монет
""")

    elif luck < 850:
        item = random.choice(TALISMANS)

        bot.send_message(message.chat.id, f"""
📦 РЕДКИЙ ДРОП

{RARITIES[item[1]]} {item[0]}

✨ Эффект:
{item[2]}
""")

    else:
        bot.send_message(message.chat.id, """
📦 MYTHIC DROP

🔴 🌙 Лунный талисман

🔥 СУПЕР РЕДКИЙ ПРЕДМЕТ
""")


def sell(message):
    uid = message.from_user.id
    u = get_user(uid)

    # (name, u_index, price_per_unit)
    resources = [
        ("coal",      9,  5),
        ("iron",      10, 10),
        ("gold",      11, 20),
        ("diamond",   12, 35),
        ("uranium",   13, 50),
        ("hellstone", 14, 80),
        ("energy",    15, 120),
        ("moon",      16, 200),
    ]

    total = 0
    lines = []

    for name, index, price in resources:
        amount = u[index]

        if amount > 0:
            earned = amount * price
            total += earned
            lines.append(f"  {amount} шт. → +{earned} монет")

        cur.execute(f"UPDATE users SET {name}=0 WHERE user_id=?", (uid,))

    if total == 0:
        bot.send_message(message.chat.id, "🎒 нечего продавать — сначала сходи в шахту")
        return

    cur.execute("UPDATE users SET coins = coins + ? WHERE user_id=?", (total, uid))
    db.commit()

    detail = "\n".join(lines)

    bot.send_message(message.chat.id, f"""
💱 ПРОДАЖА РЕСУРСОВ

{detail}

💰 Итого: +{total} монет
""")


def gift(message):
    uid = message.from_user.id
    user = get_user(uid)
    now = time.time()

    if now - user[7] < 86400:
        bot.send_message(message.chat.id, "⏳ подарок уже получен")
        return

    reward = random.randint(100, 400)

    cur.execute("""
        UPDATE users
        SET coins = coins + ?,
            last_daily = ?
        WHERE user_id=?
    """, (reward, now, uid))

    db.commit()

    bot.send_message(message.chat.id, f"🎁 ты получил +{reward} монет")


def upgrade(message):
    uid = message.from_user.id
    u = get_user(uid)

    cost = 300

    if u[3] < cost:
        bot.send_message(message.chat.id, "❌ не хватает монет (нужно 300)")
        return

    new_lvl = u[5] + 1

    cur.execute("""
        UPDATE users
        SET coins = coins - ?,
            mine_level = ?
        WHERE user_id=?
    """, (cost, new_lvl, uid))

    db.commit()

    bot.send_message(
        message.chat.id,
        f"""
⬆ ШАХТА УЛУЧШЕНА

🏗 новый уровень: {new_lvl}

✨ открыты новые ресурсы!
💰 доход увеличен!
"""
    )


# =========================
# WIPE
# =========================

@bot.message_handler(commands=['wipe'])
def wipe(message):
    cur.execute("""
        UPDATE users
        SET
            xp = 0,
            level = 1,
            coins = 0,
            messages = 0,
            mine_level = 1,
            bank = 0,
            coal = 0,
            iron = 0,
            gold = 0,
            diamond = 0,
            uranium = 0,
            hellstone = 0,
            energy = 0,
            moon = 0,
            talisman_until = 0
        WHERE username != 'Дьявол'
    """)

    db.commit()

    bot.send_message(
        message.chat.id,
        "🧹 Вся статистика сброшена\n👑 Игрок Дьявол сохранён"
    )


# =========================
# RUN
# =========================

print("BOT STARTED STABLE VERSION")
bot.infinity_polling(skip_pending=True)
# Пример для SQLite: сбросить статистику всех игроков,
# кроме игрока с ником "Дьявол"

import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# Обнуление статистики
cursor.execute("""
UPDATE players
SET
    coins = 0,
    xp = 0,
    level = 0,
    messages = 0,
    mine_lvl = 0,
    coal = 0,
    iron = 0,
    gold = 0
WHERE nickname != 'Дьявол'
""")

conn.commit()
conn.close()

print("Статистика всех игроков сброшена.")
import sqlite3

conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS players (
    user_id INTEGER PRIMARY KEY,
    nickname TEXT,
    coins REAL DEFAULT 0,
    xp REAL DEFAULT 0,
    level INTEGER DEFAULT 0,
    messages INTEGER DEFAULT 0,
    mine_lvl REAL DEFAULT 1,
    coal INTEGER DEFAULT 0,
    iron INTEGER DEFAULT 0,
    gold INTEGER DEFAULT 0
)
""")

conn.commit()
print("BOT STARTED STABLE VERSION")
bot.infinity_polling(skip_pending=True)
# =========================
# NEW MINE SYSTEM
# =========================

def mine(message):
    uid = message.from_user.id
    u = get_user(uid)

    now = time.time()

    # cooldown
    if uid in cooldowns["mine"]:
        left = MINE_COOLDOWN - (now - cooldowns["mine"][uid])

        if left > 0:
            h = int(left // 3600)
            m = int((left % 3600) // 60)

            bot.send_message(
                message.chat.id,
                f"⏳ Шахта перезаряжается\n\n⌛ Осталось: {h}ч {m}м"
            )
            return

    # уровень шахты
    lvl = min(u[5], 8)

    resource_name, price = MINE_RESOURCES[lvl]

    amount = random.randint(3, 8)

    # x2 талисман
    if now < u[17]:
        amount *= 2

    # ресурс
    resource_column = {
        1: "coal",
        2: "iron",
        3: "gold",
        4: "diamond",
        5: "uranium",
        6: "hellstone",
        7: "energy",
        8: "moon"
    }[lvl]

    # добавляем ресурс
    cur.execute(f"""
        UPDATE users
        SET {resource_column} = {resource_column} + ?
        WHERE user_id = ?
    """, (amount, uid))

    # XP
    xp_gain = random.randint(5, 15)

    cur.execute("""
        UPDATE users
        SET xp = xp + ?
        WHERE user_id = ?
    """, (xp_gain, uid))

    # монеты
    money = amount * price

    cur.execute("""
        UPDATE users
        SET coins = coins + ?
        WHERE user_id = ?
    """, (money, uid))

    # LEVEL UP
    updated = get_user(uid)

    levelup = ""

    if updated[1] >= updated[2] * 120:

        cur.execute("""
            UPDATE users
            SET
                level = level + 1,
                xp = 0
            WHERE user_id = ?
        """, (uid,))

        levelup = "\n\n🔥 LEVEL UP!"

    # босс
    boss_text = ""

    if random.randint(1, 100) <= 15:

        boss = random.choice(BOSSES)

        reward = boss[1]

        cur.execute("""
            UPDATE users
            SET coins = coins + ?
            WHERE user_id = ?
        """, (reward, uid))

        boss_text = f"""

👹 БОСС ПОБЕЖДЁН

{boss[0]}

💰 +{reward} монет
"""

    # талисман
    talisman_text = ""

    if random.randint(1, 1000) == 777:

        talisman_until = now + 43200

        cur.execute("""
            UPDATE users
            SET talisman_until = ?
            WHERE user_id = ?
        """, (talisman_until, uid))

        talisman_text = """

🪬 НАЙДЕН ТАЛИСМАН

🔥 x2 ресурсы на 12 часов
"""

    db.commit()

    cooldowns["mine"][uid] = now

    bot.send_message(
        message.chat.id,
        f"""
⛏ ШАХТА

{resource_name}: +{amount}

💰 Продано:
+{money} монет

⚡ XP:
+{xp_gain}

⬆ Уровень шахты:
{lvl}/8
{boss_text}
{talisman_text}
{levelup}
"""
    )


# =========================
# NEW PROFILE SYSTEM
# =========================

def profile(message):

    uid = message.from_user.id
    u = get_user(uid)

    width = 1000
    height = 550

    bg = Image.new("RGB", (width, height), (18, 18, 30))
    draw = ImageDraw.Draw(bg)

    FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

    font_title = ImageFont.truetype(FONT_BOLD, 42)
    font_text = ImageFont.truetype(FONT, 28)

    # аватарка
    photos = bot.get_user_profile_photos(uid)

    if photos.total_count > 0:

        file_id = photos.photos[0][0].file_id

        file_info = bot.get_file(file_id)

        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"

        response = requests.get(file_url)

        avatar = Image.open(BytesIO(response.content)).convert("RGB")

        avatar = avatar.resize((220, 220))

        bg.paste(avatar, (50, 150))

    # ник
    name = u[8] if u[8] else "Игрок"

    draw.text(
        (320, 40),
        name,
        fill="white",
        font=font_title
    )

    # статистика
    stats = [
        f"⚡ XP: {u[1]}",
        f"📈 Уровень: {u[2]}",
        f"💰 Монеты: {u[3]}",
        f"💬 Сообщения: {u[4]}",
        f"⛏ Шахта: {u[5]}/8",
        f"🏦 Банк: {u[6]}",
        f"🪨 Уголь: {u[9]}",
        f"⛓ Железо: {u[10]}",
        f"💛 Золото: {u[11]}",
        f"💎 Алмазы: {u[12]}",
    ]

    y = 140

    for stat in stats:

        draw.text(
            (320, y),
            stat,
            fill=(230, 230, 230),
            font=font_text
        )

        y += 40

    # XP BAR
    max_xp = max(u[2] * 120, 1)

    percent = min(u[1] / max_xp, 1)

    draw.rectangle(
        (320, 500, 850, 530),
        fill=(50, 50, 50)
    )

    draw.rectangle(
        (320, 500, 320 + int(530 * percent), 530),
        fill=(0, 255, 120)
    )

    draw.text(
        (320, 460),
        f"XP {u[1]} / {max_xp}",
        fill="white",
        font=font_text
    )

    path = f"profile_{uid}.png"

    bg.save(path)

    with open(path, "rb") as img:
        bot.send_photo(message.chat.id, img)

    os.remove(path)
