"""Handle file uploads, ZIP extraction, and code aggregation."""
import io
import zipfile
from pathlib import Path
from typing import Optional

from config import MAX_CODE_CHARS, MAX_FILES_PER_REVIEW, SUPPORTED_EXTENSIONS


def detect_language(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    lang_map = {
        ".py": "python", ".js": "javascript", ".ts": "typescript",
        ".jsx": "javascript", ".tsx": "typescript", ".java": "java",
        ".go": "go", ".rs": "rust", ".cpp": "cpp", ".c": "c",
        ".cs": "csharp", ".rb": "ruby", ".php": "php", ".swift": "swift",
        ".kt": "kotlin", ".scala": "scala", ".sql": "sql",
        ".sh": "bash", ".bash": "bash", ".yaml": "yaml", ".yml": "yaml",
        ".json": "json", ".html": "html", ".css": "css", ".vue": "vue",
    }
    return lang_map.get(ext, "text")


def is_supported_file(path: str) -> bool:
    return Path(path).suffix.lower() in SUPPORTED_EXTENSIONS


def extract_zip(uploaded_bytes: bytes) -> list[dict]:
    """Extract code files from a ZIP archive."""
    files = []
    skip_dirs = {"node_modules", ".git", "__pycache__", "venv", ".venv", "dist", "build", ".tox"}

    with zipfile.ZipFile(io.BytesIO(uploaded_bytes)) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            name = info.filename.replace("\\", "/")
            parts = name.split("/")
            if any(p in skip_dirs for p in parts):
                continue
            if not is_supported_file(name):
                continue
            try:
                content = zf.read(info).decode("utf-8", errors="replace")
            except Exception:
                continue
            if content.strip():
                files.append({
                    "path": name,
                    "content": content,
                    "language": detect_language(name),
                })
            if len(files) >= MAX_FILES_PER_REVIEW:
                break
    return files


def process_uploaded_file(uploaded_file) -> Optional[dict]:
    """Process a single uploaded file."""
    name = uploaded_file.name
    if name.lower().endswith(".zip"):
        return {"type": "zip", "files": extract_zip(uploaded_file.getvalue())}
    if is_supported_file(name):
        content = uploaded_file.getvalue().decode("utf-8", errors="replace")
        return {
            "type": "single",
            "files": [{
                "path": name,
                "content": content,
                "language": detect_language(name),
            }],
        }
    return None


def aggregate_code(files: list[dict], max_chars: int = MAX_CODE_CHARS) -> tuple[str, list[dict]]:
    """Combine multiple files into review payload with truncation."""
    parts = []
    total = 0
    included = []

    for f in files:
        header = f"\n# --- File: {f['path']} ---\n"
        block = header + f["content"]
        if total + len(block) > max_chars:
            remaining = max_chars - total
            if remaining > 500:
                block = block[:remaining] + "\n# ... [truncated]"
                parts.append(block)
                included.append({**f, "truncated": True})
            break
        parts.append(block)
        total += len(block)
        included.append(f)

    return "\n".join(parts), included


def primary_language(files: list[dict]) -> str:
    if not files:
        return "python"
    langs = [f.get("language", "text") for f in files]
    return max(set(langs), key=langs.count)
