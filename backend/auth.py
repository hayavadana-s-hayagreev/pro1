from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/me")
async def read_users_me():
    return {"message": "This is a protected route"}
