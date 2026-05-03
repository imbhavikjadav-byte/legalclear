import re


def sanitise_filename(name: str) -> str:
    """Remove special characters and replace spaces with hyphens for safe filenames."""
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"\s+", "-", name.strip())
    return name[:80] if len(name) > 80 else name


def is_valid_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))
