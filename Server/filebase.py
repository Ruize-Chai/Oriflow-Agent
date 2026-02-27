from fastapi import APIRouter
from Server.utils import read_filebase_lists

router = APIRouter(prefix="/filebase", tags=["filebase"])


@router.get("/list")
def filebase_list():
    return read_filebase_lists()
