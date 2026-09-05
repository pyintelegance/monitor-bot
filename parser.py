import re
import aiohttp
from bs4 import BeautifulSoup
from config import KEYWORDS, IGNORE_KEYWORDS

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def is_relevant(text: str) -> bool:
    t = text.lower()
    for ig in IGNORE_KEYWORDS:
        if ig in t:
            return False
    for kw in KEYWORDS:
        if kw in t:
            return True
    return False

async def fetch_teamwork_channel():
    """Парсит t.me/s/teamwork_uz — ищет Buyurtma №"""
    url = "https://t.me/s/teamwork_uz"
    results = []
    try:
        async with aiohttp.ClientSession(headers=HEADERS) as s:
            async with s.get(url, timeout=20) as r:
                html = await r.text()
        soup = BeautifulSoup(html, "lxml")
        # каждый пост — tg-widget
        msgs = soup.select("div.tgme_widget_message")
        for m in msgs[-20:]:  # последние 20
            text_el = m.select_one("div.tgme_widget_message_text")
            if not text_el:
                continue
            text = text_el.get_text(" ", strip=True)
            if "Buyurtma №" not in text:
                continue
            # номер
            num_match = re.search(r"Buyurtma №(\d+)", text)
            if not num_match:
                continue
            num = num_match.group(1)
            # ссылка
            link_el = m.select_one("a.tgme_widget_message_date")
            link = link_el["href"] if link_el else f"https://t.me/s/teamwork_uz"
            # дата — внутри time
            # заголовок Mavzu
            mavzu = ""
            m2 = re.search(r"Mavzu:\s*(.+?)\s*Vazifa:", text)
            if m2:
                mavzu = m2.group(1).strip()[:80]
            # цена
            price = ""
            p2 = re.search(r"Narxi:\s*([^\n]+)", text)
            if p2:
                price = p2.group(1).strip()
            # фильтр
            if not is_relevant(text):
                continue
            # игнор старых без цены? оставляем все релевантные
            results.append({
                "id": f"tw_{num}",
                "num": num,
                "title": mavzu or f"Buyurtma №{num}",
                "text": text[:900],
                "price": price,
                "url": f"https://teamwork.uz/task/{num}",
                "source": "teamwork"
            })
    except Exception as e:
        print(f"[parser] teamwork channel error: {e}")
    return results

async def fetch_dowork_projects():
    """Парсит dowork.uz/uz/projects — новые проекты"""
    results = []
    try:
        async with aiohttp.ClientSession(headers=HEADERS) as s:
            async with s.get("https://dowork.uz/uz/projects", timeout=20) as r:
                html = await r.text()
        soup = BeautifulSoup(html, "lxml")
        # проекты — ссылки вида /uz/projects/...
        for a in soup.select('a[href*="/uz/projects/"]'):
            href = a.get("href", "")
            if "/uz/projects/create" in href:
                continue
            title = a.get_text(strip=True)
            if len(title) < 10:
                continue
            full = href if href.startswith("http") else f"https://dowork.uz{href}"
            # дедуп по href
            if any(r["url"] == full for r in results):
                continue
            if not is_relevant(title):
                continue
            # цена рядом — ищем в родителе
            price = ""
            parent = a.parent
            if parent:
                pt = parent.get_text(" ", strip=True)
                pm = re.search(r"(\d[\d\s]*UZS)", pt)
                if pm:
                    price = pm.group(1)
            results.append({
                "id": f"dw_{full.split('/')[-1][:40]}",
                "num": full.split("/")[-1][:20],
                "title": title[:80],
                "text": title,
                "price": price,
                "url": full,
                "source": "dowork"
            })
            if len(results) >= 8:
                break
    except Exception as e:
        print(f"[parser] dowork error: {e}")
    return results

async def fetch_all():
    tw = await fetch_teamwork_channel()
    dw = await fetch_dowork_projects()
    # мердж
    all_items = tw + dw
    return all_items
