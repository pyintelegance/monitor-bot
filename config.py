import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "773870189"))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "600"))

# фильтр — только эти заказы интересны Жахангиру
KEYWORDS = [
    "sayt", "sayt yaratish", "landing", "veb-sayt", "web", "site",
    "bot", "telegram", "aiogram", "python", "dasturlash",
    "frontend", "figma", "html", "css", "javascript"
]

# расширяемый фильтр — почти подходит, можно подучить и взять
EXPAND_KEYWORDS = [
    "qr", "qr-kod", "deep link", "payme", "click", "uzum", "to'lov",
    "crm", "pos", "kassa", "fiskal", "ikpu", "shtrix", "sklad", "ombor",
    "vending", "avtomat"
]

# подсказки что подучить для expand-заказов
GAP_HINTS = {
    "qr": "QR + deep link (aiogram + PostgreSQL) — 1 день",
    "deep link": "QR + deep link — 1 день",
    "payme": "Payme/Click API — 1 день, пример в tech-store",
    "click": "Payme/Click API — 1 день",
    "uzum": "Uzum Pay API — 1 день",
    "crm": "CRM на Django + PostgreSQL — 2-3 дня",
    "pos": "POS веб-версия вместо Desktop — 2-3 дня",
    "kassa": "POS/кassa веб-версия — 2-3 дня",
    "fiskal": "Fiskalizatsiya API (soliq.uz) — 2 дня",
    "vending": "Vending + to'lov (без SDK, веб-обвязка) — 2 дня",
}

# игнор — распыление (строго не подходит)
IGNORE_KEYWORDS = [
    "flutter", "android", "ios",
    "corel", "coreldraw", "montaj", "video", "smm",
    "play market", "brand face", "reklama"
]

# не слать заказы старше N часов (защита от вечных повторов старых Buyurtma из t.me/s)
MAX_AGE_HOURS = int(os.getenv("MAX_AGE_HOURS", "48"))

TEAMWORK_CHANNEL_URL = "https://t.me/s/teamwork_uz"
TEAMWORK_TASKS_URL = "https://teamwork.uz/tasks"
DOWORK_PROJECTS_URL = "https://dowork.uz/uz/projects"
