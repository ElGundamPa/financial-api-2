from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from typing import Optional, Literal
from datetime import datetime
import httpx
import random

from app.adapters.tradingview import crypto, indices, forex, futures, stocks
from app.adapters.tradingview.common import list_refs_for_category
from app.adapters.base import InstrumentRef
from app.schemas import InstrumentSnapshot, ApiMeta, Price24hResponse


app = FastAPI()


async def compute_price24(snapshot: InstrumentSnapshot) -> InstrumentSnapshot:
    if snapshot.change_24h_pct is None:
        snapshot.price_24h = None
    else:
        try:
            snapshot.price_24h = round(snapshot.price / (1 + snapshot.change_24h_pct / 100.0), 8)
        except Exception:
            snapshot.price_24h = None
    return snapshot


CATEGORY_MAP = {
    "crypto": crypto,
    "indices": indices,
    "forex": forex,
    "futures": futures,
    "stocks": stocks,
}


@app.get("/api/price24h")
async def price24h(
    category: Literal["indices", "crypto", "forex", "futures", "stocks"] = Query(...),
    limit_per_page: int = Query(200, ge=1, le=500),
    cursor: Optional[str] = None,
    format: Literal["json", "jsonl"] = "json",
):
    start_ts = datetime.utcnow()
    try:
        module = CATEGORY_MAP[category]
        refs, next_cursor, expected_rows = await module.list_refs(None, cursor, limit_per_page)
        # Construir snapshots directamente
        data = []
        for ref in refs:
            snap = InstrumentSnapshot(
                provider="tradingview",
                category=category,  # type: ignore
                symbol=ref.symbol,
                name=ref.name,
                price=ref.price,
                change_24h_pct=ref.change_24h_pct,
                price_24h=None,
                ts=datetime.utcnow(),
            )
            snap = await compute_price24(snap)
            data.append(snap)
        status = "ok" if len(data) > 0 else "degraded"
        meta = ApiMeta(
            ts=start_ts,
            provider="tradingview",
            category=category,  # type: ignore
            limit_per_page=limit_per_page,
            next_cursor=next_cursor,
            status=status,  # type: ignore
        )
        return JSONResponse(Price24hResponse(meta=meta, data=data).model_dump())
    except Exception as e:
        meta = ApiMeta(
            ts=start_ts,
            provider="tradingview",
            category=category,  # type: ignore
            limit_per_page=limit_per_page,
            next_cursor=None,
            status="fail",  # type: ignore
        )
        return JSONResponse({"meta": meta.model_dump(), "error": str(e)}, status_code=500)


@app.get("/api/verify")
async def verify():
    report = {"tradingview": {}}
    for category in ["indices", "crypto", "forex", "futures", "stocks"]:
        try:
            # Contar expected recorriendo páginas hasta que no haya más
            refs, cursor, expected_rows = await list_refs_for_category(category, None, 200)
            all_refs = list(refs)
            cur = cursor
            while cur:
                batch, cur, _ = await list_refs_for_category(category, cur, 200)
                all_refs.extend(batch)
                if len(all_refs) > 5000:
                    break
            scraped_count = len(all_refs)
            # Muestra de 3 elementos con change_24h_pct para validar cálculo
            candidates = [r for r in all_refs if r.change_24h_pct is not None][:50]
            random.shuffle(candidates)
            checks = []
            for r in candidates[:3]:
                price = r.price
                change = r.change_24h_pct or 0.0
                try:
                    price_24h = round(price / (1 + change / 100.0), 8)
                    # Recalcular error
                    recomputed = (price / price_24h - 1.0) * 100.0
                    ok = abs(recomputed - change) <= 0.05
                except Exception:
                    price_24h = None
                    ok = False
                checks.append({
                    "symbol": r.symbol,
                    "price": price,
                    "price_24h": price_24h,
                    "change_24h_pct": change,
                    "ok": ok,
                })
            status = "ok" if expected_rows == scraped_count and all(c.get("ok", True) for c in checks) else ("degraded" if scraped_count > 0 else "fail")
            report["tradingview"][category] = {
                "expected_count": expected_rows,
                "scraped_count": scraped_count,
                "sample_price_checks": checks,
                "status": status,
            }
        except Exception as e:
            report["tradingview"][category] = {"status": "fail", "error": str(e)}
    return JSONResponse(report)


