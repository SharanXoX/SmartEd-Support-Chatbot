"""
Dynamic support flow discovery from support-assets/ folders.

Scans metadata.json, steps.json, and step*.png at startup (and on refresh).
Hybrid matching: keywords + fuzzy + TF-IDF + optional OpenAI embeddings.
"""

from __future__ import annotations

import json
import logging
import re
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.config import Settings
from app.paths import DEFAULT_LEGACY_FLOWS_DIR, DEFAULT_SUPPORT_ASSETS_DIR
from app.services.asset_urls import public_url_for_file, remap_legacy_url, resolve_step_image_url
from app.services.semantic_match import (
    TfidfIndex,
    combine_scores,
    embedding_cosine,
    fuzzy_score,
    keyword_score,
)

logger = logging.getLogger("smarted.support_indexer")

STEP_IMAGE_RE = re.compile(r"^step(\d+)", re.IGNORECASE)
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


class FlowStepDefinition(BaseModel):
    text: str
    image: str | None = None
    open_url: str | None = None
    auto_navigate: bool = False


class SupportFlowDefinition(BaseModel):
    intent: str
    keywords: list[str] = Field(default_factory=list)
    steps: list[FlowStepDefinition] = Field(default_factory=list)
    intro: str | None = None
    suggested_replies: list[str] = Field(default_factory=list)
    title: str | None = None
    description: str | None = None
    folder_id: str | None = None


@dataclass(frozen=True)
class FlowMatch:
    flow: SupportFlowDefinition
    confidence: float
    scores: dict[str, float] = field(default_factory=dict)


@dataclass
class _CatalogEntry:
    flow: SupportFlowDefinition
    search_text: str
    embedding: list[float] | None = None


class SupportIndexer:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._entries: list[_CatalogEntry] = []
        self._tfidf = TfidfIndex()
        self._last_scan: float = 0.0
        self._assets_mtime: float = 0.0
        self._catalog_path: Path | None = None

    def assets_directory(self, settings: Settings) -> Path:
        if settings.support_assets_dir:
            return Path(settings.support_assets_dir).expanduser().resolve()
        return DEFAULT_SUPPORT_ASSETS_DIR.resolve()

    def _public_url(self, flow_id: str, filename: str) -> str:
        return public_url_for_file(flow_id, filename)

    def _folder_keywords(self, flow_id: str, meta: dict[str, Any]) -> list[str]:
        kws = list(meta.get("keywords") or [])
        title = str(meta.get("title") or flow_id.replace("_", " "))
        kws.append(title.lower())
        kws.append(flow_id.replace("_", " "))
        return list(dict.fromkeys(k.strip().lower() for k in kws if k and str(k).strip()))

    def _sort_step_images(self, folder: Path) -> list[Path]:
        images: list[tuple[int, Path]] = []
        for path in folder.iterdir():
            if not path.is_file() or path.suffix.lower() not in IMAGE_EXTS:
                continue
            m = STEP_IMAGE_RE.match(path.stem)
            if m:
                images.append((int(m.group(1)), path))
            elif path.stem.isdigit():
                images.append((int(path.stem), path))
        images.sort(key=lambda x: x[0])
        return [p for _, p in images]

    def _load_steps_json(self, folder: Path, flow_id: str) -> list[FlowStepDefinition]:
        path = folder / "steps.json"
        if not path.is_file():
            return []
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return []
        steps: list[FlowStepDefinition] = []
        if isinstance(raw, list):
            for item in raw:
                if not isinstance(item, dict):
                    continue
                img = item.get("image")
                raw = str(img).strip() if img else ""
                if raw.startswith("/demo-assets/"):
                    raw = remap_legacy_url(raw, flow_id)
                image_url = (
                    self._public_url(flow_id, Path(raw).name)
                    if raw and not raw.startswith("/") and not raw.startswith("http")
                    else raw or None
                )
                open_url = str(item.get("open_url") or "").strip() or None
                if open_url and open_url.startswith("#"):
                    open_url = open_url[1:]
                auto_nav = bool(item.get("auto_navigate", False))
                steps.append(
                    FlowStepDefinition(
                        text=str(item.get("text") or "").strip(),
                        image=image_url,
                        open_url=open_url,
                        auto_navigate=auto_nav,
                    )
                )
        return steps

    def _load_metadata(self, folder: Path, flow_id: str) -> dict[str, Any]:
        path = folder / "metadata.json"
        if path.is_file():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                pass
        title = flow_id.replace("_", " ").title()
        return {
            "title": title,
            "keywords": [flow_id.replace("_", " "), title.lower()],
            "description": f"Support walkthrough for {title}",
        }

    def _bind_steps_to_disk_images(
        self,
        settings: Settings,
        folder: Path,
        flow_id: str,
        steps: list[FlowStepDefinition],
    ) -> list[FlowStepDefinition]:
        """Always prefer real files on disk (step1.png, step2.png, …) for image URLs."""
        disk_images = self._sort_step_images(folder)
        bound: list[FlowStepDefinition] = []
        for i, step in enumerate(steps):
            disk_name = disk_images[i].name if i < len(disk_images) else None
            resolved = resolve_step_image_url(
                settings,
                flow_id=flow_id,
                image_ref=step.image,
                disk_filename=disk_name,
            )
            if resolved:
                logger.info("[IMAGE] flow=%s step=%d url=%s", flow_id, i + 1, resolved)
            bound.append(
                FlowStepDefinition(
                    text=step.text,
                    image=resolved,
                    open_url=step.open_url,
                    auto_navigate=step.auto_navigate,
                )
            )
        return bound

    def _build_flow_from_folder(self, settings: Settings, folder: Path) -> SupportFlowDefinition | None:
        if not folder.is_dir() or folder.name.startswith("."):
            return None
        flow_id = folder.name
        meta = self._load_metadata(folder, flow_id)
        steps = self._load_steps_json(folder, flow_id)
        images = self._sort_step_images(folder)

        if not steps and images:
            for img_path in images:
                steps.append(
                    FlowStepDefinition(
                        text="",
                        image=self._public_url(flow_id, img_path.name),
                    )
                )

        if not steps:
            return None

        steps = self._bind_steps_to_disk_images(settings, folder, flow_id, steps)

        for i, step in enumerate(steps):
            if not step.text:
                steps[i] = FlowStepDefinition(
                    text=f"Follow the on-screen guidance in step {i + 1}.",
                    image=step.image,
                    open_url=step.open_url,
                    auto_navigate=step.auto_navigate,
                )

        return SupportFlowDefinition(
            intent=flow_id,
            folder_id=flow_id,
            title=str(meta.get("title") or flow_id.replace("_", " ").title()),
            description=str(meta.get("description") or ""),
            keywords=self._folder_keywords(flow_id, meta),
            intro=meta.get("intro") or f"Here's how to handle **{meta.get('title', flow_id)}**:",
            steps=steps,
            suggested_replies=list(meta.get("suggested_replies") or [])[:8],
        )

    def _legacy_json_flows(self, settings: Settings) -> list[SupportFlowDefinition]:
        """Fallback: backend/flows/*.json when no support-assets folders exist."""
        flows_dir = (
            Path(settings.flows_dir).expanduser().resolve()
            if settings.flows_dir
            else DEFAULT_LEGACY_FLOWS_DIR.resolve()
        )
        if not flows_dir.is_dir():
            return []
        out: list[SupportFlowDefinition] = []
        for path in sorted(flows_dir.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                flow = SupportFlowDefinition.model_validate(data)
                if not flow.folder_id:
                    flow = flow.model_copy(update={"folder_id": flow.intent})
                out.append(flow)
            except Exception:
                continue
        return out

    def _migrate_legacy_demo_assets(self, assets_dir: Path) -> None:
        """One-time layout: demo-assets/* -> support-assets/<intent>/stepN.png"""
        legacy = assets_dir.parent / "demo-assets"
        mapping = {
            "password": "password_reset",
            "payments": "payment_failed",
            "uploads": "upload_documents",
            "profile": "profile_update",
            "account": "account_settings",
        }
        if not legacy.is_dir():
            return
        for src_name, dest_id in mapping.items():
            src = legacy / src_name
            if not src.is_dir():
                continue
            dest = assets_dir / dest_id
            dest.mkdir(parents=True, exist_ok=True)
            for img in src.iterdir():
                if img.is_file() and img.suffix.lower() in IMAGE_EXTS:
                    target = dest / img.name
                    if not target.exists():
                        try:
                            target.write_bytes(img.read_bytes())
                        except OSError:
                            pass

    def _folder_mtime(self, assets_dir: Path) -> float:
        if not assets_dir.is_dir():
            return 0.0
        latest = assets_dir.stat().st_mtime
        for path in assets_dir.rglob("*"):
            try:
                latest = max(latest, path.stat().st_mtime)
            except OSError:
                pass
        return latest

    def _embed_flows(self, settings: Settings, entries: list[_CatalogEntry]) -> None:
        if not settings.openai_api_key.strip():
            return
        try:
            from openai import OpenAI

            client = OpenAI(api_key=settings.openai_api_key.strip())
            texts = [e.search_text for e in entries]
            resp = client.embeddings.create(model=settings.embedding_model, input=texts)
            for entry, item in zip(entries, resp.data, strict=True):
                entry.embedding = list(item.embedding)
            logger.info("[INDEX] OpenAI embeddings built for %d flows", len(entries))
        except Exception as exc:
            logger.warning("[INDEX] Embedding build skipped: %s", exc)

    def refresh(self, settings: Settings, *, force: bool = False) -> int:
        with self._lock:
            assets_dir = self.assets_directory(settings)
            assets_dir.mkdir(parents=True, exist_ok=True)
            self._migrate_legacy_demo_assets(assets_dir)

            mtime = self._folder_mtime(assets_dir)
            if not force and self._entries and mtime <= self._assets_mtime:
                return len(self._entries)

            flows: list[SupportFlowDefinition] = []
            for child in sorted(assets_dir.iterdir()):
                built = self._build_flow_from_folder(settings, child)
                if built:
                    flows.append(built)

            if not flows:
                flows = self._legacy_json_flows(settings)
                logger.warning(
                    "[INDEX] No support-assets folders found; using %d legacy JSON flows",
                    len(flows),
                )

            entries: list[_CatalogEntry] = []
            for flow in flows:
                search_text = " ".join(
                    filter(
                        None,
                        [
                            flow.intent,
                            flow.title or "",
                            flow.description or "",
                            flow.intro or "",
                            " ".join(flow.keywords),
                            " ".join(s.text for s in flow.steps),
                        ],
                    )
                )
                entries.append(_CatalogEntry(flow=flow, search_text=search_text))

            self._tfidf.fit([e.search_text for e in entries])
            self._embed_flows(settings, entries)
            self._entries = entries
            self._assets_mtime = mtime
            self._last_scan = time.time()
            self._catalog_path = assets_dir

            cache_path = Path(settings.support_index_cache_path)
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                cache_path.write_text(
                    json.dumps(
                        {
                            "scanned_at": self._last_scan,
                            "flows": [e.flow.model_dump() for e in entries],
                        },
                        indent=2,
                    ),
                    encoding="utf-8",
                )
            except OSError:
                pass

            logger.info(
                "[INDEX] Support catalog ready: %d flows from %s",
                len(entries),
                assets_dir,
            )
            return len(entries)

    def list_flows(self, settings: Settings) -> list[SupportFlowDefinition]:
        with self._lock:
            if not self._entries:
                self.refresh(settings)
            return [e.flow for e in self._entries]

    def get_flow_by_intent(self, settings: Settings, intent: str) -> SupportFlowDefinition | None:
        for flow in self.list_flows(settings):
            if flow.intent == intent:
                return flow
        return None

    def match(self, settings: Settings, message: str) -> FlowMatch | None:
        with self._lock:
            if not self._entries:
                self.refresh(settings)
            if not self._entries:
                return None

            tfidf_scores = self._tfidf.score_query(message)
            query_embedding: list[float] | None = None
            if settings.openai_api_key.strip():
                try:
                    from openai import OpenAI

                    client = OpenAI(api_key=settings.openai_api_key.strip())
                    query_embedding = list(
                        client.embeddings.create(
                            model=settings.embedding_model,
                            input=[message],
                        ).data[0].embedding
                    )
                except Exception:
                    query_embedding = None

            best: FlowMatch | None = None
            for idx, entry in enumerate(self._entries):
                kw = keyword_score(message, entry.flow.keywords)
                fuzzy = fuzzy_score(message, entry.search_text)
                tfidf = tfidf_scores[idx] if idx < len(tfidf_scores) else 0.0
                emb = (
                    embedding_cosine(query_embedding, entry.embedding)
                    if query_embedding and entry.embedding
                    else 0.0
                )
                combined = combine_scores(
                    keyword=kw,
                    fuzzy=fuzzy,
                    tfidf=tfidf,
                    embedding=emb,
                    w_keyword=settings.match_weight_keyword,
                    w_fuzzy=settings.match_weight_fuzzy,
                    w_tfidf=settings.match_weight_tfidf,
                    w_embedding=settings.match_weight_embedding,
                )
                scores = {
                    "keyword": round(kw, 4),
                    "fuzzy": round(fuzzy, 4),
                    "tfidf": round(tfidf, 4),
                    "embedding": round(emb, 4),
                    "combined": round(combined, 4),
                }
                if best is None or combined > best.confidence:
                    best = FlowMatch(flow=entry.flow, confidence=combined, scores=scores)

            if best is None or best.confidence < settings.intent_flow_threshold:
                if best:
                    logger.info(
                        "[MATCH] Below threshold %.2f: %s (%.3f)",
                        settings.intent_flow_threshold,
                        best.flow.intent,
                        best.confidence,
                    )
                return None

            logger.info(
                "[MATCH] %s confidence=%.3f scores=%s",
                best.flow.intent,
                best.confidence,
                best.scores,
            )
            return best

    def catalog_summary(self, settings: Settings) -> dict[str, Any]:
        with self._lock:
            if not self._entries:
                self.refresh(settings)
            return {
                "assets_dir": str(self.assets_directory(settings)),
                "flow_count": len(self._entries),
                "last_scan": self._last_scan,
                "flows": [
                    {
                        "intent": e.flow.intent,
                        "title": e.flow.title,
                        "steps": len(e.flow.steps),
                        "keywords": e.flow.keywords[:6],
                        "has_embedding": e.embedding is not None,
                    }
                    for e in self._entries
                ],
            }


_indexer = SupportIndexer()


def get_support_indexer() -> SupportIndexer:
    return _indexer


def invalidate_flow_cache() -> None:
    with _indexer._lock:
        _indexer._entries = []
        _indexer._assets_mtime = 0.0


def list_flows(settings: Settings) -> list[SupportFlowDefinition]:
    return _indexer.list_flows(settings)


def match_support_flow(settings: Settings, message: str) -> FlowMatch | None:
    _indexer.refresh(settings)
    return _indexer.match(settings, message)
