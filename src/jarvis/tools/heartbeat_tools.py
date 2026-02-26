"""
Heartbeat-specific tools for Jarvis.

These tools are only provided to the agent during heartbeat invocations so
that the LLM can take concrete actions (create notifications, draft emails)
rather than simply returning free-text that the heartbeat handler has to
interpret.
"""

import uuid
import os
import requests
from datetime import datetime
from langchain_core.tools import tool

# API endpoint for notifications (used for HTTP fallback only)
API_BASE_URL = os.getenv("API_INTERNAL_URL", "http://localhost:8000")


def send_notification(title: str, message: str, notification_type: str = "action"):
    """
    Send a notification to the dashboard.
    When running in-process with API, uses direct function call.
    Falls back to HTTP request if direct import fails.
    """
    try:
        # Try direct function call first (when running in-process with API)
        from jarvis.api import add_notification
        add_notification(notification_type, title, message)
        print(f"[Scheduler]: Notification added to dashboard")
    except ImportError:
        # Fall back to HTTP request (when running as separate process)
        try:
            response = requests.post(
                f"{API_BASE_URL}/api/notifications",
                json={
                    "type": notification_type,
                    "title": title,
                    "message": message
                },
                timeout=5
            )
            if response.ok:
                print(f"[Scheduler]: Notification sent to dashboard")
            else:
                print(f"[Scheduler]: Failed to send notification: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"[Scheduler]: Could not reach API: {e}")


@tool
def send_important_notification(title: str, message: str, notification_type: str = "action") -> str:
    """Send an important notification to the advisor's dashboard.

    Use this ONLY during heartbeat checks when something urgent or noteworthy
    needs the advisor's attention.  The notification will appear immediately
    on the dashboard.

    Args:
        title: Short headline for the notification (e.g. '🚨 Urgent: Client Risk').
        message: Detailed body text explaining what was found.
        notification_type: One of 'info', 'warning', 'action', 'success'. Defaults to 'action'.
    """
    send_notification(title=title, message=message, notification_type=notification_type)
    return f"Notification sent to dashboard: {title}"


@tool
def send_draft_email(client_name: str, to: str, subject: str, body: str) -> str:
    """Create a draft email for the advisor to review and approve before sending.

    Use this when you identify an action that requires sending an email to or
    about a client.  The draft will appear in the Email Drafts section of the
    dashboard for review.

    Args:
        client_name: Name of the client this email relates to (e.g. 'David Chen').
        to: Full recipient string (e.g. 'David Chen <david.chen@globalbank.com>').
        subject: Email subject line.
        body: Full email body text.
    """
    from jarvis.api import _email_suggestions

    suggestion = {
        "id": str(uuid.uuid4()),
        "client_name": client_name,
        "to": to,
        "subject": subject,
        "body": body,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
    }
    _email_suggestions[suggestion["id"]] = suggestion

    return f"Draft email created for advisor approval (id={suggestion['id']}). It will appear in the Email Drafts dashboard."
