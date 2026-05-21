"""Review history storage using TinyDB."""
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from tinydb import Query, TinyDB

from config import REVIEWS_DB_PATH


class ReviewStorage:
    def __init__(self, db_path=None):
        self.db = TinyDB(str(db_path or REVIEWS_DB_PATH))
        self.table = self.db.table("reviews")

    def save_review(self, review_data: dict) -> str:
        review_id = str(uuid.uuid4())[:8]
        record = {
            "id": review_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            **review_data,
        }
        self.table.insert(record)
        return review_id

    def get_all(self, limit: int = 50) -> list[dict]:
        records = self.table.all()
        records.sort(key=lambda r: r.get("created_at", ""), reverse=True)
        return records[:limit]

    def get_by_id(self, review_id: str) -> Optional[dict]:
        q = Query()
        results = self.table.search(q.id == review_id)
        return results[0] if results else None

    def delete(self, review_id: str) -> bool:
        q = Query()
        removed = self.table.remove(q.id == review_id)
        return len(removed) > 0

    def clear_all(self) -> int:
        count = len(self.table)
        self.table.truncate()
        return count

    def search(self, query_text: str) -> list[dict]:
        q = Query()
        text = query_text.lower()
        return self.table.search(
            (q.summary.test(lambda s: text in (s or "").lower()))
            | (q.filename.test(lambda s: text in (s or "").lower()))
            | (q.personality.test(lambda s: text in (s or "").lower()))
        )
