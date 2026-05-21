"""Security scanning using Bandit for Python code."""
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


def run_bandit_scan(code: str, filename: str = "review.py") -> dict:
    """Run Bandit on Python source code."""
    if not code.strip():
        return {"issues": [], "metrics": {}, "skipped": True, "reason": "Empty code"}

    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / filename
        filepath.write_text(code, encoding="utf-8")

        try:
            result = subprocess.run(
                [
                    "bandit", "-r", str(filepath),
                    "-f", "json", "-q",
                    "--severity-level", "all",
                    "--confidence-level", "all",
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )
            output = result.stdout.strip()
            if not output:
                return {"issues": [], "metrics": {}, "skipped": False}

            data = json.loads(output)
            issues = []
            for item in data.get("results", []):
                sev = item.get("issue_severity", "UNDEFINED").lower()
                conf = item.get("issue_confidence", "UNDEFINED").lower()
                severity_map = {
                    "high": "high",
                    "medium": "medium",
                    "low": "low",
                }
                issues.append({
                    "type": "security",
                    "severity": severity_map.get(sev, "medium"),
                    "title": item.get("test_id", "Security Issue"),
                    "message": item.get("issue_text", ""),
                    "line": item.get("line_number", 0),
                    "file": item.get("filename", filename),
                    "cwe": item.get("issue_cwe", {}).get("id") if isinstance(item.get("issue_cwe"), dict) else None,
                    "confidence": conf,
                    "source": "bandit",
                })
            return {
                "issues": issues,
                "metrics": data.get("metrics", {}),
                "skipped": False,
            }
        except FileNotFoundError:
            return {
                "issues": [],
                "metrics": {},
                "skipped": True,
                "reason": "Bandit not installed. Run: pip install bandit",
            }
        except subprocess.TimeoutExpired:
            return {"issues": [], "metrics": {}, "skipped": True, "reason": "Scan timed out"}
        except json.JSONDecodeError:
            return {"issues": [], "metrics": {}, "skipped": False}
        except Exception as e:
            return {"issues": [], "metrics": {}, "skipped": True, "reason": str(e)}


def should_run_bandit(files: list[dict]) -> bool:
    """Determine if Bandit scan is applicable."""
    return any(
        f.get("language") == "python" or f.get("path", "").endswith(".py")
        for f in files
    )


def get_python_code(files: list[dict]) -> Optional[str]:
    py_files = [f for f in files if f.get("language") == "python" or f.get("path", "").endswith(".py")]
    if not py_files:
        return None
    return "\n\n".join(f["content"] for f in py_files)
