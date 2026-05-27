from __future__ import annotations

from datetime import datetime
from pathlib import Path

from src.infrastructure.persistence.mysql_connection import init_schema, mysql_connection


PROMPT_SOURCE_SYSTEM = "system"
PROMPT_SOURCE_MANUAL = "manual"
PROMPT_SOURCE_GENERATED = "generated"


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def normalize_prompt_filename(filename: str | None) -> str:
    normalized = str(filename or "").strip().replace("\\", "/")
    if not normalized:
        return ""
    if "/" not in normalized:
        return f"prompts/{normalized}"
    return normalized


def list_prompt_documents() -> list[str]:
    with mysql_connection() as conn:
        init_schema(conn)
        rows = conn.execute(
            """
            SELECT filename
            FROM prompt_documents
            ORDER BY filename ASC
            """
        ).fetchall()
    return [str(row["filename"]) for row in rows]


def get_prompt_document(filename: str) -> dict | None:
    normalized = normalize_prompt_filename(filename)
    with mysql_connection() as conn:
        init_schema(conn)
        row = conn.execute(
            """
            SELECT filename, content, source, created_at, updated_at
            FROM prompt_documents
            WHERE filename = ?
            """,
            (normalized,),
        ).fetchone()
    if row is None:
        return None
    return dict(row)


def get_prompt_content(filename: str | None) -> str:
    normalized = normalize_prompt_filename(filename)
    if not normalized:
        return ""
    try:
        document = get_prompt_document(normalized)
    except Exception:
        document = None
    if document is not None:
        return str(document.get("content") or "")

    path = Path(normalized)
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def upsert_prompt_document(
    filename: str,
    content: str,
    *,
    source: str = PROMPT_SOURCE_MANUAL,
) -> dict:
    normalized = normalize_prompt_filename(filename)
    if not normalized:
        raise ValueError("filename 不能为空")

    now = _now_iso()
    with mysql_connection() as conn:
        init_schema(conn)
        existing = conn.execute(
            "SELECT filename, created_at FROM prompt_documents WHERE filename = ?",
            (normalized,),
        ).fetchone()
        created_at = str(existing["created_at"]) if existing else now
        conn.execute(
            """
            INSERT INTO prompt_documents (filename, content, source, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON DUPLICATE KEY UPDATE
                content = VALUES(content),
                source = VALUES(source),
                updated_at = VALUES(updated_at)
            """,
            (normalized, content, source, created_at, now),
        )
        conn.commit()
    return {
        "filename": normalized,
        "content": content,
        "source": source,
        "created_at": created_at,
        "updated_at": now,
    }
