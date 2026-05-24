import re
from typing import List, Dict


def parse_diff(diff_text: str) -> List[Dict]:
    """Very small parser: extracts changed file paths and a rough change_type.

    Returns list of {file_path, change_type, added_lines, removed_lines}
    """
    files = []
    # find diff --git lines
    pattern = re.compile(r"^diff --git a/(.+?) b/(.+)$", re.MULTILINE)
    matches = list(pattern.finditer(diff_text))

    # split by matches to isolate hunks per file
    if not matches:
        return files

    # Collect file segments
    indices = [m.start() for m in matches] + [len(diff_text)]
    for i, m in enumerate(matches):
        start = indices[i]
        end = indices[i + 1]
        segment = diff_text[start:end]
        file_path = m.group(2)

        added = len(re.findall(r"^\+[^+].*", segment, re.MULTILINE))
        removed = len(re.findall(r"^-[^-].*", segment, re.MULTILINE))

        if "new file mode" in segment:
            change_type = "Added"
        elif "deleted file mode" in segment:
            change_type = "Removed"
        else:
            change_type = "Modified"

        files.append({
            "file_path": file_path,
            "change_type": change_type,
            "added_lines": added,
            "removed_lines": removed,
        })

    return files
