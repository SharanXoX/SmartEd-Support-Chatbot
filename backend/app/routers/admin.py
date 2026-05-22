"""Admin APIs for KB ingestion, FAQs, analytics."""

from __future__ import annotations

import shutil
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from starlette.responses import Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.deps import get_current_admin
from app.models import Conversation, FAQ, KnowledgeAsset, Message, SupportTicket, User, VisualGuide
from app.schemas import AnalyticsSummary, ConversationSummary, FAQCreate, FAQOut, MessageOut, VisualGuideOut
from app.services import rag_service
from app.services.support_indexer import get_support_indexer, invalidate_flow_cache

router = APIRouter(prefix="/admin", tags=["admin"])


def _safe_filename(name: str) -> str:
    return Path(name).name.replace("..", "_")


@router.get("/analytics/summary", response_model=AnalyticsSummary)
def analytics_summary(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
) -> AnalyticsSummary:
    since = datetime.utcnow() - timedelta(hours=24)
    conv24 = db.query(func.count(Conversation.id)).filter(Conversation.created_at >= since).scalar() or 0
    msg24 = db.query(func.count(Message.id)).filter(Message.created_at >= since).scalar() or 0
    tickets_open = db.query(func.count(SupportTicket.id)).filter(SupportTicket.status == "open").scalar() or 0
    faq_count = db.query(func.count(FAQ.id)).scalar() or 0
    kb_docs = db.query(func.count(KnowledgeAsset.id)).scalar() or 0
    return AnalyticsSummary(
        conversations_24h=int(conv24),
        messages_24h=int(msg24),
        tickets_open=int(tickets_open),
        faq_count=int(faq_count),
        kb_documents=int(kb_docs),
    )


@router.get("/faqs", response_model=list[FAQOut])
def list_faqs(db: Session = Depends(get_db), _: User = Depends(get_current_admin)) -> list[FAQ]:
    return db.query(FAQ).order_by(FAQ.created_at.desc()).limit(500).all()


@router.post("/faqs", response_model=FAQOut, status_code=status.HTTP_201_CREATED)
def create_faq(body: FAQCreate, db: Session = Depends(get_db), _: User = Depends(get_current_admin)) -> FAQ:
    row = FAQ(question=body.question, answer=body.answer, category=body.category)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/faqs/{faq_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_faq(faq_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_admin)) -> Response:
    row = db.query(FAQ).filter(FAQ.id == faq_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="FAQ not found")
    db.delete(row)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/knowledge/upload", status_code=status.HTTP_201_CREATED)
async def upload_knowledge(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: User = Depends(get_current_admin),
) -> dict:
    uploads = Path(settings.uploads_dir)
    uploads.mkdir(parents=True, exist_ok=True)
    fname = _safe_filename(file.filename or "document.bin")
    dest = uploads / f"{uuid.uuid4().hex}_{fname}"
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    source_tag = f"upload:{dest.name}"
    try:
        chunks = rag_service.ingest_document(settings, path=dest, source_tag=source_tag)
    except Exception as exc:
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    asset = KnowledgeAsset(
        filename=fname,
        stored_path=str(dest),
        source_tag=source_tag,
        mime_type=file.content_type,
    )
    db.add(asset)
    db.commit()
    return {"id": asset.id, "chunks": chunks, "path": dest.name}


@router.delete("/knowledge/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge(
    asset_id: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: User = Depends(get_current_admin),
) -> Response:
    asset = db.query(KnowledgeAsset).filter(KnowledgeAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Not found")
    store = rag_service.get_store(settings)
    if store:
        store.delete_source(asset.source_tag)
    Path(asset.stored_path).unlink(missing_ok=True)
    db.delete(asset)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/visuals/upload", response_model=VisualGuideOut, status_code=status.HTTP_201_CREATED)
async def upload_visual(
    title: str = Form(...),
    description: str | None = Form(None),
    tags: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: User = Depends(get_current_admin),
) -> VisualGuideOut:
    visuals = Path(settings.visual_assets_dir)
    visuals.mkdir(parents=True, exist_ok=True)
    fname = _safe_filename(file.filename or "image.png")
    dest = visuals / f"{uuid.uuid4().hex}_{fname}"
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    guide = VisualGuide(title=title, description=description, image_path=str(dest), tags=tags)
    db.add(guide)
    db.commit()
    db.refresh(guide)
    image_url = f"/uploads/visuals/{dest.name}"
    return VisualGuideOut(
        id=guide.id,
        title=guide.title,
        description=guide.description,
        image_url=image_url,
        tags=guide.tags,
        created_at=guide.created_at,
    )


@router.get("/visuals", response_model=list[VisualGuideOut])
def list_visuals(db: Session = Depends(get_db), _: User = Depends(get_current_admin)) -> list[VisualGuideOut]:
    rows = db.query(VisualGuide).order_by(VisualGuide.created_at.desc()).limit(200).all()
    out: list[VisualGuideOut] = []
    for g in rows:
        name = Path(g.image_path).name
        out.append(
            VisualGuideOut(
                id=g.id,
                title=g.title,
                description=g.description,
                image_url=f"/uploads/visuals/{name}",
                tags=g.tags,
                created_at=g.created_at,
            )
        )
    return out


@router.post("/support/reindex")
def reindex_support_catalog(
    settings: Settings = Depends(get_settings),
    _: User = Depends(get_current_admin),
) -> dict:
    """Rescan support-assets/ after admin uploads or folder changes."""
    invalidate_flow_cache()
    count = get_support_indexer().refresh(settings, force=True)
    return {"indexed_flows": count, "catalog": get_support_indexer().catalog_summary(settings)}


@router.get("/conversations", response_model=list[ConversationSummary])
def list_conversations(
    db: Session = Depends(get_db), _: User = Depends(get_current_admin), limit: int = 50
) -> list[Conversation]:
    return db.query(Conversation).order_by(Conversation.updated_at.desc()).limit(limit).all()


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageOut])
def list_messages(
    conversation_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_admin)
) -> list[Message]:
    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )
