# -*- coding: utf-8 -*-
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except: pass

import aiohttp
import config
from parser import fetch_all

DATA_FILE = Path("data/sent.json")
DATA_FILE.parent.mkdir(exist_ok=True)

API = f"https://api.telegram.org/bot{config.BOT_TOKEN}"
ADMIN = config.ADMIN_ID

def load_sent():
    if DATA_FILE.exists():
        try:
            data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            # поддержка старого формата list и нового dict с meta
            if isinstance(data, dict) and "ids" in data:
                return set(data["ids"])
            if isinstance(data, list):
                return set(data)
            return set()
        except:
            return set()
    return set()

def save_sent(s):
    # храним с меткой времени для диагностики рестартов
    payload = {"ids": sorted(list(s)), "updated": datetime.now().isoformat()}
    DATA_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

sent_ids = load_sent()
# флаг первого запуска после сброса файла (Render ephemeral fix)
_first_boot = len(sent_ids) == 0
offset = 0

TPL_TEXT = (
    "Salom! Men Jahongir - landing + Telegram botlar (aiogram + PostgreSQL).\n"
    "Portfolio: jahongir-freelance.vercel.app + tech-store-z3ev.onrender.com\n"
    "Narx: landing 350k, bot 500k, dokon 1.2M. 2-3 kunda tayyor.\n"
    "Aloqa: @jahongir_lab"
)

WELCOME = (
    "<b>Jahongir Monitor</b> - 24/7 freelance watcher\n\n"
    "Sources: t.me/teamwork_uz + teamwork.uz + dowork.uz\n"
    "Filter: sayt, landing, bot, python\n"
    f"Interval: {config.CHECK_INTERVAL//60} min\n\n"
    "Commands:\n"
    "/check - check now\n"
    "/stats - stats\n"
    "/test - test"
)

async def tg_call(method, data=None):
    async with aiohttp.ClientSession() as s:
        url = f"{API}/{method}"
        async with s.post(url, json=data) as r:
            return await r.json()

async def send_msg(text, kb=None):
    payload = {"chat_id": ADMIN, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    if kb:
        payload["reply_markup"] = kb
    await tg_call("sendMessage", payload)

def kb_for(url):
    return {"inline_keyboard": [[{"text": "Open order", "url": url}], [{"text": "Template", "callback_data": "tpl"}]]}

async def handle_updates():
    global offset
    while True:
        try:
            data = await tg_call("getUpdates", {"offset": offset, "timeout": 25, "allowed_updates": ["message","callback_query"]})
            if not data.get("ok") or not data.get("result"):
                await asyncio.sleep(2)
                continue
            for upd in data["result"]:
                offset = upd["update_id"] + 1
                msg = upd.get("message")
                cb = upd.get("callback_query")
                if cb and cb.get("data") == "tpl":
                    await tg_call("answerCallbackQuery", {"callback_query_id": cb["id"]})
                    await tg_call("sendMessage", {"chat_id": ADMIN, "text": TPL_TEXT})
                    continue
                if not msg:
                    continue
                if msg.get("from",{}).get("id") != ADMIN:
                    continue
                text = msg.get("text","").strip()
                if text.startswith("/start") or text.startswith("/help"):
                    await send_msg(WELCOME)
                elif text.startswith("/stats"):
                    await send_msg(f"Sent: <b>{len(sent_ids)}</b> | first_boot={'yes' if _first_boot else 'no'}")
                elif text.startswith("/check"):
                    await send_msg("Checking...")
                    n = await scan_and_send(force=True)
                    await send_msg(f"Done, new: {n} | total: {len(sent_ids)}")
                elif text.startswith("/test"):
                    await send_msg("Test - bot works! Next check in 10 min.", kb_for("https://teamwork.uz/tasks"))
                # ignore other
        except Exception as e:
            print(f"[poll] {e}")
            await asyncio.sleep(5)

async def scan_and_send(force=False):
    global sent_ids, _first_boot
    items = await fetch_all()

    # FIX для Render ephemeral: первый скан после сброса файла
    # Старые заказы (>2ч) молча запоминаем, свежие (<=2ч) — шлем
    # + защита от вечных повторов: parser уже фильтрует старше MAX_AGE_HOURS
    if not force and _first_boot and len(sent_ids) == 0:
        if len(items) == 0:
            _first_boot = False
            return 0
        # есть свежие — разделим по возрасту dt
        from datetime import timezone, timedelta
        now = datetime.now(timezone.utc)
        to_send = []
        to_silent = []
        for it in items:
            dt_str = it.get("dt")
            try:
                dt = datetime.fromisoformat(dt_str.replace("Z","+00:00")) if dt_str else None
                if dt and dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                age_h = (now - dt).total_seconds()/3600 if dt else 999
            except:
                age_h = 999
            # старше 2ч считаем старым (уже был в ленте до рестарта)
            if age_h > 2:
                to_silent.append(it)
            else:
                to_send.append(it)
        if to_silent:
            for it in to_silent:
                sent_ids.add(it["id"])
            save_sent(sent_ids)
            print(f"[dedup] first boot - silently memorized {len(to_silent)} old ids")
            try:
                if to_silent:
                    await send_msg(f"♻️ Бот перезапущен — запомнил <b>{len(to_silent)}</b> старых заказов как просмотренные. Новых в ленте: {len(to_send)}")
            except: pass
        _first_boot = False
        # продолжим отправкой только свежих (to_send), а не всех items
        items = to_send
        if not items:
            return 0

    # если когда-то уже был хотя бы один id, снимаем флаг
    if _first_boot and len(sent_ids) > 0:
        _first_boot = False

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
            await send_msg(text, kb_for(it["url"]))
            sent_ids.add(it["id"])
            save_sent(sent_ids)
            new += 1
            await asyncio.sleep(0.8)
        except Exception as e:
            print(f"send {e}")
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
            print(f"[sched] {e}")
        await asyncio.sleep(config.CHECK_INTERVAL)

async def health_server():
    from aiohttp import web
    import subprocess
    try:
        ver = subprocess.check_output(["git","rev-parse","--short","HEAD"], timeout=2).decode().strip()
    except:
        ver = "unknown"
    async def handle(request):
        return web.Response(text="ok")
    async def version(request):
        return web.Response(text=f"ver:{ver} sent:{len(sent_ids)} first_boot:{_first_boot} max_age:{config.MAX_AGE_HOURS}h")
    app = web.Application()
    app.router.add_get("/", handle)
    app.router.add_get("/health", handle)
    app.router.add_get("/version", version)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", "10000")))
    await site.start()
    print(f"[health] port {os.getenv('PORT','10000')} ver={ver}")
    while True:
        await asyncio.sleep(3600)

async def main():
    await asyncio.gather(
        handle_updates(),
        scheduler(),
        health_server()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
