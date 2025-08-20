from .common import list_refs_for_category
from app.adapters.base import InstrumentRef
from typing import Optional


async def list_refs(client, cursor: Optional[str], page_size: int) -> tuple[list[InstrumentRef], Optional[str], int]:
    return await list_refs_for_category("futures", cursor, page_size)


