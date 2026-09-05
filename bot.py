# -*- coding: utf-8 -*-
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# fix cp1251 on Windows
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except: pass

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

import config
from parser import fetch_all

DATA_FILE = Path("data/sent.json")
DATA_FILE.parent.mkdir(exist_ok=True)

bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

def load_sent():
    if DATA_FILE.exists():
        try:
            return set(json.loads(DATA_FILE.read_text(encoding="utf-8")))
        except:
            return set()
    return set()

def save_sent(s):
    DATA_FILE.write_text(json.dumps(list(s), ensure_ascii=False), encoding="utf-8")

sent_ids = load_sent()

def make_kb(url):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Open order", url=url)],
        [InlineKeyboardButton(text="Template", callback_data="tpl")]
    ])

WELCOME = (
    "<b>Jahongir Monitor</b> - 24/7 freelance watcher\n\n"
    "Sources: t.me/teamwork_uz + teamwork.uz + dowork.uz\n"
    "Filter: sayt, landing, bot, python, aiogram\n"
    f"Interval: {config.CHECK_INTERVAL//60} min\n\n"
    "Commands:\n"
    "/check - check now\n"
    "/stats - stats\n"
    "/test - test message"
)

TPL_TEXT = (
    "Salom! Men Jahongir - landing + Telegram botlar (aiogram + PostgreSQL).\n"
    "Portfolio: jahongir-freelance.vercel.app + tech-store-z3ev.onrender.com\n"
    "Narx: landing 350k, bot 500k, dokon 1.2M. 2-3 kunda tayyor.\n"
    "Aloqa: @jahongir_lab"
)

@dp.message(CommandStart())
async def start(m: Message):
    if m.from_user.id != config.ADMIN_ID:
        await m.answer("Access denied")
        return
    await m.answer(WELCOME)

@dp.message(Command("help"))
async def help_cmd(m: Message):
    await m.answer(WELCOME)

@dp.message(Command("stats"))
async def stats(m: Message):
    await m.answer(f"Sent: <b>{len(sent_ids)}</b>\nFile: {DATA_FILE}")

@dp.message(Command("check"))
async def check_now(m: Message):
    if m.from_user.id != config.ADMIN_ID:
        return
    await m.answer("Checking...")
    n = await scan_and_send(force=True)
    await m.answer(f"Done, new: {n}")

@dp.message(Command("test"))
async def test(m: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Open", url="https://teamwork.uz/tasks")]])
    await bot.send_message(config.ADMIN_ID, "Test - bot works! Next check in 10 min.", reply_markup=kb)

@dp.callback_query(F.data == "tpl")
async def tpl_cb(cb):
    await cb.answer()
    await cb.message.answer(f"<code>{TPL_TEXT}</code>")

async def scan_and_send(force=False):
    global sent_ids
    items = await fetch_all()
    new = 0
    for it in items:
        if not force and it["id"] in sent_ids:
            continue
        text = (
            f"<b>{it['title']}</b>\n"
            f"{it['price'] or 'Kelishilgan holda'}\n"
            f"{it['source']} | <code>{it['id']}</code>\n\n"
            f"{it['text'][:500]}\n\n"
            f"{it['url']}"
        )
        try:
            kb = make_kb(it["url"])
            await bot.send_message(config.ADMIN_ID, text, reply_markup=kb)
            sent_ids.add(it["id"])
            save_sent(sent_ids)
            new += 1
            await asyncio.sleep(0.8)
        except Exception as e:
            print(f"send error {e}")
        if new >= 5 and not force:
            break
    return new

async def scheduler():
    print(f"[scheduler] interval {config.CHECK_INTERVAL}s")
    await asyncio.sleep(12)
    while True:
        try:
            n = await scan_and_send(force=False)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] scan new={n} total={len(sent_ids)}")
        except Exception as e:
            print(f"[scheduler] {e}")
        await asyncio.sleep(config.CHECK_INTERVAL)

async def health_server():
    from aiohttp import web
    async def handle(request):
        return web.Response(text="ok")
    app = web.Application()
    app.router.add_get("/", handle)
    app.router.add_get("/health", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", "10000")))
    await site.start()
    print(f"[health] port {os.getenv('PORT','10000')}")
    while True:
        await asyncio.sleep(3600)

async def main():
    await asyncio.gather(
        dp.start_polling(bot),
        scheduler(),
        health_server()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
