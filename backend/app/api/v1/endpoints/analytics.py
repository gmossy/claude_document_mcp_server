from fastapi import APIRouter

router = APIRouter()


@router.get("/overview")
async def analytics_overview():
    return {"totals": {}}

