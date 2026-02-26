"""
Heartbeat-specific tools for Jarvis.

These tools are only provided to the agent during heartbeat invocations so
that the LLM can take concrete actions (create notifications, draft emails)
rather than simply returning free-text that the heartbeat handler has to
interpret.
"""

import uuid
from datetime import datetime
from langchain_core.tools import tool


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
    from jarvis.jarvis_heartbeat import send_notification
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
