"""
Calendar / Email-Archive MCP Server for Jarvis.

Backed by: <project_root>/email_archive/<client_name>/*.txt
Each .txt file follows the format:
    From: Name <email>
    To:   Name <email>
    Date: DD Month YYYY HH:MM GMT
    Subject: Subject line

    Body...

Run standalone:  uv run python src/jarvis/tools/calendar_server.py
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Resolve the email archive root (sibling of workspace/, outside workspace)
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve()
# src/jarvis/tools/calendar_server.py → go up 4 levels to project root
_PROJECT_ROOT = _HERE.parents[3]
EMAIL_ARCHIVE_ROOT = _PROJECT_ROOT / "email_archive"

ADVISOR_FROM = "Abimanyu Chamika <abimanyu.chamika@advisor.co.uk>"

# ---------------------------------------------------------------------------
# FastMCP server
# ---------------------------------------------------------------------------
mcp = FastMCP("calendar")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _client_dir(client_name: str) -> Path:
    """Resolve the archive directory for a client (case-insensitive slug)."""
    slug = client_name.strip().lower().replace(" ", "_")
    return EMAIL_ARCHIVE_ROOT / slug


def _parse_email(path: Path) -> dict:
    """Parse headers + body from a .txt email file."""
    raw = path.read_text(encoding="utf-8")
    headers: dict[str, str] = {}
    lines = raw.splitlines()
    body_start = 0

    for i, line in enumerate(lines):
        if line.strip() == "":
            body_start = i + 1
            break
        match = re.match(r"^(From|To|Date|Subject):\s*(.*)$", line, re.IGNORECASE)
        if match:
            headers[match.group(1).capitalize()] = match.group(2).strip()

    body = "\n".join(lines[body_start:]).strip()
    return {
        "filename": path.name,
        "from": headers.get("From", ""),
        "to": headers.get("To", ""),
        "date": headers.get("Date", ""),
        "subject": headers.get("Subject", ""),
        "body": body,
    }


def _parse_date(date_str: str) -> datetime | None:
    """Try to parse the Date header into a datetime object."""
    formats = [
        "%d %B %Y %H:%M GMT",
        "%d %b %Y %H:%M GMT",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None


def _date_slug(subject: str) -> str:
    """Create a filesystem-safe slug from the subject."""
    slug = re.sub(r"[^a-z0-9]+", "_", subject.lower()).strip("_")
    return slug[:50]


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def list_clients() -> list[dict]:
    """List all clients in the email archive with their email counts.

    Returns:
        A list of dicts with keys: client_name, folder, email_count.
    """
    if not EMAIL_ARCHIVE_ROOT.exists():
        return []

    result = []
    for d in sorted(EMAIL_ARCHIVE_ROOT.iterdir()):
        if d.is_dir():
            emails = list(d.glob("*.txt"))
            result.append({
                "client_name": d.name.replace("_", " ").title(),
                "folder": d.name,
                "email_count": len(emails),
            })
    return result


@mcp.tool()
def list_emails(client_name: str) -> list[dict]:
    """List all emails for a specific client with metadata (no body).

    Args:
        client_name: Client's full name or folder slug, e.g. "Alan Partridge" or "alan_partridge".

    Returns:
        A list of email metadata dicts (filename, from, to, date, subject).
    """
    client_dir = _client_dir(client_name)
    if not client_dir.exists():
        return [{"error": f"No email archive found for client '{client_name}'."}]

    emails = sorted(client_dir.glob("*.txt"), reverse=True)
    result = []
    for path in emails:
        parsed = _parse_email(path)
        parsed.pop("body")  # omit body in listing
        result.append(parsed)
    return result


@mcp.tool()
def read_email(client_name: str, filename: str) -> dict:
    """Read the full content of a specific email.

    Args:
        client_name: Client's full name or folder slug.
        filename: The exact filename, e.g. "2026-01-15_contract_renewal_update.txt".

    Returns:
        Full email dict including body, or an error dict.
    """
    path = _client_dir(client_name) / filename
    if not path.exists():
        return {"error": f"Email '{filename}' not found for client '{client_name}'."}
    return _parse_email(path)


@mcp.tool()
def search_emails(
    query: str,
    client_name: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict]:
    """Full-text search across email archives.

    Args:
        query: Case-insensitive search string matched against subject, body, from, and to.
        client_name: Optional — restrict search to a single client.
        date_from: Optional filter — only emails on or after this date (YYYY-MM-DD).
        date_to:   Optional filter — only emails on or before this date (YYYY-MM-DD).

    Returns:
        Matching email dicts (including client_folder), most recent first.
    """
    q = query.lower()

    dt_from = datetime.strptime(date_from, "%Y-%m-%d") if date_from else None
    dt_to = datetime.strptime(date_to, "%Y-%m-%d") if date_to else None

    # Determine which client folders to search
    if client_name:
        dirs = [_client_dir(client_name)]
    else:
        dirs = sorted(EMAIL_ARCHIVE_ROOT.iterdir()) if EMAIL_ARCHIVE_ROOT.exists() else []

    results = []
    for d in dirs:
        if not d.is_dir():
            continue
        for path in sorted(d.glob("*.txt"), reverse=True):
            parsed = _parse_email(path)

            # Date filter
            email_dt = _parse_date(parsed["date"])
            if dt_from and email_dt and email_dt < dt_from:
                continue
            if dt_to and email_dt and email_dt > dt_to:
                continue

            # Text match
            haystack = f"{parsed['subject']} {parsed['from']} {parsed['to']} {parsed['body']}".lower()
            if q in haystack:
                parsed["client_folder"] = d.name
                results.append(parsed)

    return results


@mcp.tool()
def send_email(
    client_name: str,
    to: str,
    subject: str,
    body: str,
) -> dict:
    """Compose and save a new outgoing email to a client's archive.

    Args:
        client_name: The client this email relates to (determines storage folder).
        to: Recipient address, e.g. "Alan Partridge <alan.partridge@norfolkradio.co.uk>".
        subject: Email subject line.
        body: Plain-text body of the email.

    Returns:
        Dict with 'success', 'filename', and 'path' keys, or an error dict.
    """
    client_dir = _client_dir(client_name)
    client_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    date_str = now.strftime("%d %B %Y %H:%M GMT")
    date_prefix = now.strftime("%Y-%m-%d")
    slug = _date_slug(subject)
    filename = f"{date_prefix}_{slug}.txt"

    # Avoid collisions
    path = client_dir / filename
    if path.exists():
        uid = str(uuid.uuid4())[:6]
        filename = f"{date_prefix}_{slug}_{uid}.txt"
        path = client_dir / filename

    content = (
        f"From: {ADVISOR_FROM}\n"
        f"To: {to}\n"
        f"Date: {date_str}\n"
        f"Subject: {subject}\n"
        f"\n"
        f"{body}\n"
    )
    path.write_text(content, encoding="utf-8")

    return {
        "success": True,
        "filename": filename,
        "path": str(path),
        "message": f"Email saved to {client_name.title()}'s archive as '{filename}'.",
    }


@mcp.tool()
def get_recent_emails(
    days: int = 7,
    client_name: str | None = None,
) -> list[dict]:
    """Retrieve emails from the last N days across all (or one) client archive.

    Args:
        days: Number of days to look back (default: 7).
        client_name: Optional — restrict to a single client.

    Returns:
        List of matching email dicts with 'client_folder' key, most recent first.
    """
    cutoff = datetime.now() - timedelta(days=days)

    if client_name:
        dirs = [_client_dir(client_name)]
    else:
        dirs = sorted(EMAIL_ARCHIVE_ROOT.iterdir()) if EMAIL_ARCHIVE_ROOT.exists() else []

    results = []
    for d in dirs:
        if not d.is_dir():
            continue
        for path in sorted(d.glob("*.txt"), reverse=True):
            parsed = _parse_email(path)
            email_dt = _parse_date(parsed["date"])
            if email_dt and email_dt >= cutoff:
                parsed["client_folder"] = d.name
                results.append((email_dt, parsed))

    # Sort globally by date desc
    results.sort(key=lambda x: x[0], reverse=True)
    return [r[1] for r in results]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    mcp.run(transport="stdio")
