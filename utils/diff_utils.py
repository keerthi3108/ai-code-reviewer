"""Diff generation and comparison utilities."""
from diff_match_patch import diff_match_patch


def generate_unified_diff(original: str, improved: str, context: int = 3) -> str:
    """Generate a simple unified-style diff."""
    dmp = diff_match_patch()
    diffs = dmp.diff_main(original, improved)
    dmp.diff_cleanupSemantic(diffs)

    lines = []
    for op, text in diffs:
        for line in text.splitlines(keepends=True):
            stripped = line.rstrip("\n\r")
            if not stripped and not line.strip():
                continue
            if op == 0:
                lines.append(f"  {stripped}")
            elif op == -1:
                lines.append(f"- {stripped}")
            else:
                lines.append(f"+ {stripped}")
    return "\n".join(lines) if lines else "No changes detected."


def split_lines_for_compare(original: str, improved: str) -> tuple[list[str], list[str]]:
    return original.splitlines(), improved.splitlines()
