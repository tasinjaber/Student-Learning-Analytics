import asyncio

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth import (
    User,
    admin_only,
    approve_request,
    async_login_user,
    create_registration_request,
    create_user,
    decline_request,
    delete_user,
    get_current_user,
    list_registration_requests,
    list_users,
    update_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginPayload(BaseModel):
    username: str
    password: str


class RegisterPayload(BaseModel):
    username: str
    password: str
    email: str = ""
    role: str = "admin"


class CreateUserPayload(BaseModel):
    username: str
    password: str
    role: str = "instructor"


class UpdateUserPayload(BaseModel):
    password: str | None = None
    role: str | None = None


# ── public ────────────────────────────────────────────────────────────────────

@router.post("/login")
async def login(payload: LoginPayload):
    token, user = await async_login_user(payload.username, payload.password)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"username": user.username, "role": user.role},
    }


@router.post("/register")
async def register(payload: RegisterPayload):
    return await create_registration_request(
        payload.username, payload.password, payload.email, payload.role
    )


@router.get("/me")
async def me(user: User = Depends(get_current_user)):
    return {"username": user.username, "role": user.role}


# ── admin: user management ────────────────────────────────────────────────────

@router.get("/admin-data")
async def get_admin_data(_admin: User = Depends(admin_only)):
    users, requests = await asyncio.gather(list_users(), list_registration_requests())
    return {"users": users, "requests": requests}


@router.get("/users")
async def get_users(_admin: User = Depends(admin_only)):
    return await list_users()


@router.post("/users")
async def add_user(payload: CreateUserPayload, _admin: User = Depends(admin_only)):
    return await create_user(payload.username, payload.password, payload.role)


@router.put("/users/{username}")
async def edit_user(username: str, payload: UpdateUserPayload, _admin: User = Depends(admin_only)):
    return await update_user(username, payload.password, payload.role)


@router.delete("/users/{username}")
async def remove_user(username: str, _admin: User = Depends(admin_only)):
    return await delete_user(username)


# ── admin: registration requests ──────────────────────────────────────────────

@router.get("/registration-requests")
async def get_requests(status: str | None = None, _admin: User = Depends(admin_only)):
    return await list_registration_requests(status_filter=status)


@router.post("/registration-requests/{request_id}/approve")
async def approve(request_id: str, _admin: User = Depends(admin_only)):
    return await approve_request(request_id)


@router.post("/registration-requests/{request_id}/decline")
async def decline(request_id: str, _admin: User = Depends(admin_only)):
    return await decline_request(request_id)
