# app/auth.py

from fastapi import Header, HTTPException

# Demo token store. A support agent may read every ticket; a customer may
# only read tickets that belong to them.
TOKENS = {
    "valid-token": {"user_id": 0, "name": "Support Agent", "role": "agent"},
    "userA": {"user_id": 1, "name": "Alice Anderson", "role": "customer"},
    "userB": {"user_id": 2, "name": "Bob Brown", "role": "customer"},
}

UNAUTHORIZED_HEADERS = {"WWW-Authenticate": "Bearer"}


def require_user(authorization: str | None = Header(default=None)) -> dict:
    """Resolve the caller from the Authorization header, or raise 401."""

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header",
            headers=UNAUTHORIZED_HEADERS,
        )

    scheme, _, token = authorization.partition(" ")

    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header",
            headers=UNAUTHORIZED_HEADERS,
        )

    user = TOKENS.get(token)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers=UNAUTHORIZED_HEADERS,
        )

    return user


def can_read_ticket(user: dict, ticket: dict) -> bool:
    """An agent reads anything; a customer only reads their own tickets."""

    if user["role"] == "agent":
        return True

    return int(ticket["customer_id"]) == user["user_id"]
