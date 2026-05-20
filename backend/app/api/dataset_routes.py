from __future__ import annotations

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from app.services import dataset_manager as dm

router = APIRouter(prefix="/datasets", tags=["datasets"])


class UrlPayload(BaseModel):
    url: str
    name: str


class KagglePayload(BaseModel):
    dataset_path: str
    name: str
    kaggle_username: str
    kaggle_key: str


@router.get("/")
async def list_datasets():
    return await dm.list_datasets()


@router.post("/upload")
async def upload_dataset(name: str, file: UploadFile = File(...)):
    raw = await file.read()
    if not raw:
        raise HTTPException(400, "Empty file")
    meta = await dm.save_from_bytes(raw, file.filename or "upload.csv", name)
    return meta


@router.post("/from-url")
async def dataset_from_url(payload: UrlPayload):
    try:
        meta = await dm.save_from_url(payload.url, payload.name)
        return meta
    except Exception as exc:
        raise HTTPException(400, f"Failed to fetch URL: {exc}")


@router.post("/from-kaggle")
async def dataset_from_kaggle(payload: KagglePayload):
    try:
        meta = await dm.save_from_kaggle(
            payload.dataset_path,
            payload.name,
            payload.kaggle_username,
            payload.kaggle_key,
        )
        return meta
    except Exception as exc:
        raise HTTPException(400, f"Kaggle download failed: {exc}")


@router.get("/{dataset_id}/validate")
async def validate_dataset(dataset_id: str):
    result = await dm.validate_dataset(dataset_id if dataset_id != "default" else None)
    return result


@router.delete("/{dataset_id}")
async def delete_dataset(dataset_id: str):
    ok = await dm.delete_dataset(dataset_id)
    if not ok:
        raise HTTPException(404, "Dataset not found")
    return {"deleted": dataset_id}
