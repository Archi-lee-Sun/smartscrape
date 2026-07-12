from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..vault import save_to_vault
from ..vault_queries import search_vault, get_all_entries, get_full_entry
from ..schemas import SynthesizedCluster

router = APIRouter()

class VaultEntrySummary(BaseModel):
    id : int
    title : str
    created_at : str


class VaultEntryFull(BaseModel):
    id: int
    source_type: str
    source_name: str
    title: str
    content: str
    url: str
    published_at: str
    fetched_at: str
    summary: str
    mode: str
    cluster_size: int
    created_at: str


@router.post("/vault/save")
async def save_entry(payload : SynthesizedCluster) -> dict :
    save_to_vault(
    source_type=payload.source_type,
    source_name=payload.source_name,
    title=payload.title,
    content=payload.content,
    url=payload.url,
    published_at=payload.published_at,
    fetched_at=payload.fetched_at,
    summary=payload.summary,
    mode=payload.mode,
    cluster_size=payload.cluster_size,
    )
    return {"status" : "saved"}


@router.get("/vault/search", response_model=list[VaultEntrySummary])
async def search(q: str) -> list[VaultEntrySummary]:
    rows = search_vault(q)
    return [VaultEntrySummary(**dict(row)) for row in rows]

@router.get("/vault/entries", response_model=list[VaultEntrySummary])
async def list_entries() -> list[VaultEntrySummary]:
    rows = get_all_entries()
    return [VaultEntrySummary(**dict(row)) for row in rows]

@router.get("/vault/entries/{entry_id}", response_model=VaultEntryFull)
async def get_entry(entry_id : int) -> VaultEntryFull :
    row = get_full_entry(entry_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Entry not found")
    return VaultEntryFull(**dict(row))
