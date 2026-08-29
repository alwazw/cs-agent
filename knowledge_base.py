import os
from pathlib import Path
from typing import Dict, Any

INITIATIVE_MAP: Dict[str, Dict[str, Any]] = {
    "+18005550100": {
        "docs_subdir": "support",
        "personality": "Warm and Empathetic"
    },
    "+18005550200": {
        "docs_subdir": "sales",
        "personality": "Crisp and Professional"
    },
    "+18005550300": {
        "docs_subdir": "vip",
        "personality": "Witty and Casual"
    }
}

def load_knowledge_base(docs_dir: str = "docs", phone_number: str | None = None) -> str:
    """
    Scans the given docs directory (or initiative subdirectory if phone_number is mapped)
    for all .md files, reads their contents, and returns an aggregated string.
    """
    base_path = Path(docs_dir)

    # Check if destination phone number maps to a specific initiative subdirectory
    target_path = base_path
    if phone_number and phone_number in INITIATIVE_MAP:
        sub_dir = INITIATIVE_MAP[phone_number].get("docs_subdir")
        if sub_dir:
            initiative_path = base_path / sub_dir
            if initiative_path.exists() and initiative_path.is_dir():
                target_path = initiative_path

    if not target_path.exists() or not target_path.is_dir():
        return ""

    aggregated_content = []
    # Collect .md files in the target directory
    for file_path in sorted(target_path.glob("*.md")):
        try:
            content = file_path.read_text(encoding="utf-8")
            aggregated_content.append(f"--- Document: {file_path.name} ---\n{content.strip()}")
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    # Fallback to root docs if subdirectory had no .md files
    if not aggregated_content and target_path != base_path and base_path.exists():
        for file_path in sorted(base_path.glob("*.md")):
            try:
                content = file_path.read_text(encoding="utf-8")
                aggregated_content.append(f"--- Document: {file_path.name} ---\n{content.strip()}")
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

    return "\n\n".join(aggregated_content)
