import asyncio
import httpx
from typing import Optional, Tuple, List
from selectolax.parser import HTMLParser
from bs4 import BeautifulSoup  # Fallback
import re
from app.adapters.base import InstrumentRef
from app.utils import get_headers, parse_number


TV_URLS = {
    "indices": "https://www.tradingview.com/markets/indices/quotes-all/",
    "crypto": "https://www.tradingview.com/markets/cryptocurrencies/prices-all/",
    "forex": "https://www.tradingview.com/markets/currencies/rates-all/",
    "futures": "https://www.tradingview.com/markets/futures/quotes-all/",
    "stocks": "https://www.tradingview.com/markets/stocks-usa/market-movers-large-cap/",
}


def normalize_number(text: str) -> Optional[float]:
    if not text:
        return None
    t = (text.replace("\xa0", " ")
              .replace("USD", "")
              .replace("$", "")
              .replace(",", "")
              .replace("%", "")
              .strip())
    t = re.sub(r"\s+", " ", t)
    if t == "" or t in {"-", "N/A"}:
        return None
    try:
        return float(t)
    except ValueError:
        # Intentar coma como decimal
        try:
            return float(t.replace(" ", "").replace(",", "."))
        except ValueError:
            return None


async def fetch_html(client: httpx.AsyncClient, url: str, timeout: int = 8) -> Optional[str]:
    headers = get_headers()
    headers["Accept-Language"] = "es-CO,es;q=0.9,en;q=0.8"
    try:
        resp = await client.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"❌ fetch_html error: {e}")
        return None


def extract_rows_selectolax(html: str) -> list:
    tree = HTMLParser(html)
    # Intentar varias tablas/cuerpos
    rows = tree.css("table tbody tr")
    if rows:
        return rows
    # Fallback: cualquier tr
    rows = tree.css("tr")
    return rows


def find_header_positions(html: str) -> dict:
    # Usar BeautifulSoup para leer headers por texto
    soup = BeautifulSoup(html, "html.parser")
    thead = soup.find("thead")
    positions = {}
    if not thead:
        return positions
    headers = thead.find_all("th")
    for idx, th in enumerate(headers):
        txt = th.get_text(strip=True).lower()
        if "price" in txt or "last" in txt:
            positions["price"] = idx
        if "24" in txt and "%" in txt:
            positions["change24"] = idx
    return positions


def parse_row(row, category: str, header_pos: dict) -> Optional[InstrumentRef]:
    # Intentar Selectolax API si el row es Node, sino fallback a bs4 Tag
    def cell_texts():
        try:
            tds = row.css("td")
            return [td.text(strip=True) for td in tds]
        except Exception:
            tds = row.find_all("td") if hasattr(row, "find_all") else []
            return [td.get_text(strip=True) for td in tds]

    cells = cell_texts()
    if len(cells) < 2:
        return None

    # Símbolo suele ir en la primera celda como enlace/texto
    symbol = cells[0].split()[0] if cells[0] else None
    if not symbol or len(symbol) > 20:
        return None

    # Precio
    price = None
    if "price" in header_pos and header_pos["price"] < len(cells):
        price = normalize_number(cells[header_pos["price"]])
    if price is None:
        # Fallback: buscar en primeras 4 celdas numérico
        for i in range(1, min(5, len(cells))):
            val = normalize_number(cells[i])
            if val is not None:
                price = val
                break

    # Cambio 24h si existe
    change_24h = None
    if "change24" in header_pos and header_pos["change24"] < len(cells):
        change_24h = normalize_number(cells[header_pos["change24"]])

    if price is None or price <= 0:
        return None

    return InstrumentRef(
        symbol=symbol,
        name=None,
        exchange=None,
        currency="USD" if category in ("crypto", "stocks") else None,
        category=category,  # type: ignore
        price=price,
        change_24h_pct=change_24h,
        change_1h_pct=None,
    )


async def list_refs_for_category(category: str, cursor: Optional[str], page_size: int) -> tuple[list[InstrumentRef], Optional[str], int]:
    url = TV_URLS[category]
    start_offset = 0
    if cursor:
        try:
            import base64, json
            start_offset = int(json.loads(base64.urlsafe_b64decode(cursor.encode()).decode()).get("offset", 0))
        except Exception:
            start_offset = 0

    refs: list[InstrumentRef] = []
    expected_rows = 0
    async with httpx.AsyncClient(http2=True, timeout=8) as client:
        page = 1
        while len(refs) < start_offset + page_size and page <= 10:
            page_url = url if page == 1 else f"{url}?page={page}"
            html = await fetch_html(client, page_url, timeout=8)
            if not html:
                break
            header_pos = find_header_positions(html)
            rows = extract_rows_selectolax(html)
            expected_rows += len(rows) if rows else 0
            for node in rows:
                ref = parse_row(node, category, header_pos)
                if ref:
                    refs.append(ref)
            if not rows:
                break
            page += 1

    total = len(refs)
    sliced = refs[start_offset:start_offset + page_size]
    next_cursor = None
    if start_offset + page_size < total:
        import base64, json
        next_cursor = base64.urlsafe_b64encode(json.dumps({"offset": start_offset + page_size}).encode()).decode()
    return sliced, next_cursor, expected_rows


