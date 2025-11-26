from fastapi import APIRouter

router = APIRouter()


@router.post("/login")
async def login():
    return {"token": "placeholder"}


@router.get("/me")
async def me():
    return {"user": "placeholder"}

