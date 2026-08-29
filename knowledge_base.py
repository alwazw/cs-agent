import os
from pathlib import Path

def load_knowledge_base(docs_dir: str = "docs") -> str:
    """
    Scans the given docs directory for all .md files, reads their contents,
    and returns an aggregated string.
    """
    docs_path = Path(docs_dir)
    if not docs_path.exists() or not docs_path.is_dir():
        return ""

    aggregated_content = []
    # Sort files for deterministic aggregation order
    for file_path in sorted(docs_path.glob("*.md")):
        try:
            content = file_path.read_text(encoding="utf-8")
            aggregated_content.append(f"--- Document: {file_path.name} ---\n{content.strip()}")
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    return "\n\n".join(aggregated_content)
