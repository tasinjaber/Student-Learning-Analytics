from __future__ import annotations

import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import Depends, Header, HTTPException, status
from pymongo.errors import PyMongoError

from app.db import database

_USERS_COL = database["users"]
_REQS_COL  = database["registration_requests"]

# Built-in fallback accounts (always available)
_BUILTIN = {
    "admin": {"password": "admin123", "role": "admin"},
}

TOKEN_STORE: dict[str, "User"] = {}


@dataclass
class User:
    username: str
    role: str


# ── helpers ──────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _find_user(username: str) -> dict | None:
    try:
        doc = await _USERS_COL.find_one({"_id": username})
        if doc:
            return doc
    except PyMongoError:
        pass
    row = _BUILTIN.get(username)
    if row:
        return {"_id": username, "username": username, **row, "source": "builtin"}
    return None


# ── login / token ─────────────────────────────────────────────────────────────

def login_user(username: str, password: str) -> tuple[str, User]:
    raise NotImplementedError("use async_login_user")


async def async_login_user(username: str, password: str) -> tuple[str, User]:
    row = await _find_user(username)
    if not row or row.get("password") != password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = secrets.token_urlsafe(24)
    user = User(username=username, role=row["role"])
    TOKEN_STORE[token] = user
    return token, user


def get_current_user(authorization: str | None = Header(default=None)) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    user = TOKEN_STORE.get(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return user


def admin_only(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return user


# ── user management ───────────────────────────────────────────────────────────

async def list_users() -> list[dict]:
    builtin = [
        {"username": k, "role": v["role"], "source": "builtin"}
        for k, v in _BUILTIN.items()
    ]
    try:
        db_users = await _USERS_COL.find({}, {"_id": 0, "password": 0}).to_list(length=500)
    except PyMongoError:
        db_users = []
    return builtin + [{"source": "db", **u} for u in db_users]


async def create_user(username: str, password: str, role: str) -> dict:
    if username in _BUILTIN:
        raise HTTPException(400, "Cannot override a built-in account.")
    existing = await _USERS_COL.find_one({"_id": username})
    if existing:
        raise HTTPException(400, f"User '{username}' already exists.")
    doc = {
        "_id": username,
        "username": username,
        "password": password,
        "role": role,
        "created_at": _now(),
        "source": "db",
    }
    await _USERS_COL.insert_one(doc)
    return {"username": username, "role": role, "source": "db"}


async def update_user(username: str, password: str | None, role: str | None) -> dict:
    if username in _BUILTIN:
        raise HTTPException(400, "Cannot edit a built-in account.")
    update: dict = {}
    if password:
        update["password"] = password
    if role:
        update["role"] = role
    if not update:
        raise HTTPException(400, "Nothing to update.")
    result = await _USERS_COL.update_one({"_id": username}, {"$set": update})
    if result.matched_count == 0:
        raise HTTPException(404, "User not found.")
    # Invalidate existing tokens for this user
    for tok, u in list(TOKEN_STORE.items()):
        if u.username == username:
            del TOKEN_STORE[tok]
    return {"username": username, "updated": list(update.keys())}


async def delete_user(username: str) -> dict:
    if username in _BUILTIN:
        raise HTTPException(400, "Cannot delete a built-in account.")
    result = await _USERS_COL.delete_one({"_id": username})
    if result.deleted_count == 0:
        raise HTTPException(404, "User not found.")
    for tok, u in list(TOKEN_STORE.items()):
        if u.username == username:
            del TOKEN_STORE[tok]
    return {"deleted": username}


# ── registration requests ─────────────────────────────────────────────────────

async def create_registration_request(username: str, password: str, email: str, role: str) -> dict:
    existing_user = await _find_user(username)
    if existing_user:
        raise HTTPException(400, f"Username '{username}' is already taken.")
    pending = await _REQS_COL.find_one({"username": username, "status": "pending"})
    if pending:
        raise HTTPException(400, "A pending request for this username already exists.")
    req_id = uuid.uuid4().hex[:16]
    doc = {
        "_id": req_id,
        "request_id": req_id,
        "username": username,
        "password": password,
        "email": email,
        "role": role,
        "status": "pending",
        "created_at": _now(),
    }
    await _REQS_COL.insert_one(doc)
    return {"request_id": req_id, "status": "pending"}


async def list_registration_requests(status_filter: str | None = None) -> list[dict]:
    query = {}
    if status_filter:
        query["status"] = status_filter
    try:
        docs = await _REQS_COL.find(query, {"_id": 0, "password": 0}).to_list(length=200)
        return docs
    except PyMongoError:
        return []


async def approve_request(request_id: str) -> dict:
    req = await _REQS_COL.find_one({"_id": request_id})
    if not req:
        raise HTTPException(404, "Request not found.")
    if req["status"] != "pending":
        raise HTTPException(400, f"Request is already {req['status']}.")
    await create_user(req["username"], req["password"], req["role"])
    await _REQS_COL.update_one({"_id": request_id}, {"$set": {"status": "approved"}})
    return {"approved": req["username"]}


async def decline_request(request_id: str) -> dict:
    req = await _REQS_COL.find_one({"_id": request_id})
    if not req:
        raise HTTPException(404, "Request not found.")
    if req["status"] != "pending":
        raise HTTPException(400, f"Request is already {req['status']}.")
    await _REQS_COL.update_one({"_id": request_id}, {"$set": {"status": "declined"}})
    return {"declined": request_id}
