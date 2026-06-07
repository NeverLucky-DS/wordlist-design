from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas import TopicOut, TopicSummaryOut
from app.services import topic_pack_service

router = APIRouter(prefix="/api/topics", tags=["topics"])


@router.get("", response_model=list[TopicSummaryOut])
async def list_topics():
    slugs = topic_pack_service.list_topic_slugs()
    out: list[TopicSummaryOut] = []
    for slug in slugs:
        pack = topic_pack_service.load_topic_pack(slug)
        if not pack:
            continue
        topic = pack.get("topic") or {}
        out.append(
            TopicSummaryOut(
                slug=str(topic.get("slug", slug)),
                title_de=str(topic.get("title_de", slug)),
                title_ru=str(topic.get("title_ru", "")),
                level_default=str(topic.get("level_default", "B1")),
            )
        )
    return out


@router.get("/{slug}", response_model=TopicOut)
async def get_topic(slug: str, db: AsyncSession = Depends(get_db)):
    meta = await topic_pack_service.get_topic_meta(db, slug.strip().lower())
    if not meta:
        raise HTTPException(status_code=404, detail="Topic not found")
    return TopicOut(**meta)


@router.post("/{slug}/import")
async def import_topic(slug: str, db: AsyncSession = Depends(get_db)):
    try:
        result = await topic_pack_service.import_topic_pack(db, slug.strip().lower())
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return result
