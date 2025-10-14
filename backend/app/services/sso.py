def verify_ticket(ticket: str) -> dict | None:
    """Stub SSO verification."""
    if ticket:
        return {"uid": "demo", "email": "demo@example.com"}
    return None
