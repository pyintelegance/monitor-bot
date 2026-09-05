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

# игнор — распыление
IGNORE_KEYWORDS = [
    "pos", "vending", "avtomat", "kassa", "crm",
    "flutter", "android", "ios",
    "corel", "coreldraw", "montaj", "video", "smm",
    "play market"
]

TEAMWORK_CHANNEL_URL = "https://t.me/s/teamwork_uz"
TEAMWORK_TASKS_URL = "https://teamwork.uz/tasks"
DOWORK_PROJECTS_URL = "https://dowork.uz/uz/projects"
